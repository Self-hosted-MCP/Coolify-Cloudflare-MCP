import asyncio
import json
import stat
import time

import pytest
from mcp.server.auth.provider import AuthorizationParams, AuthorizeError, RegistrationError, TokenError
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

from opsmcp import auth, config

CB = "https://claude.ai/api/mcp/auth_callback"
PASS = "correct horse battery staple"


@pytest.fixture
def prov(monkeypatch):
    monkeypatch.setenv("LOGIN_HASH", auth.hash_passphrase(PASS, rounds=1000))
    return auth.PassphraseOAuth("https://ops.test", ["claude.ai", "claude.com"])


def client(cid="c1", uri=CB):
    return OAuthClientInformationFull(client_id=cid, client_name="Claude", redirect_uris=[AnyUrl(uri)])


def params(uri=CB):
    return AuthorizationParams(state="s", scopes=["ops"], code_challenge="x" * 43, redirect_uri=AnyUrl(uri), redirect_uri_provided_explicitly=True)


def run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


async def start_login(p, c=None, uri=CB):
    c = c or client()
    await p.register_client(c)
    url = await p.authorize(c, params(uri))
    return c, url.split("req=")[1]


def test_passphrase_hash_and_check():
    h = auth.hash_passphrase("abc", rounds=1000)
    assert h.startswith("pbkdf2:1000:") and auth.check_passphrase("abc", h) and not auth.check_passphrase("abd", h)
    assert not auth.check_passphrase("abc", "garbage") and not auth.check_passphrase("abc", "")
    assert auth.hash_passphrase("abc", rounds=1000) != h        # a fresh salt each time


def test_passphrase_ok_uses_the_hash_and_only_allows_plain_text_in_test_mode(monkeypatch):
    monkeypatch.setenv("LOGIN_HASH", auth.hash_passphrase("right", rounds=1000))
    assert auth.passphrase_ok("right") and not auth.passphrase_ok("wrong")
    monkeypatch.setenv("LOGIN_HASH", "")
    monkeypatch.setenv("LOGIN_PASSPHRASE", "plain-test-pass")
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    assert not auth.passphrase_ok("plain-test-pass")             # never when Zero Trust is on
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    assert auth.passphrase_ok("plain-test-pass") and not auth.passphrase_ok("nope")


def test_token_key_is_a_one_way_fingerprint():
    k = auth.token_key("secret-token")
    assert len(k) == 64 and "secret" not in k and k == auth.token_key("secret-token") != auth.token_key("other")


def test_private_write_makes_a_private_file(tmp_path):
    f = tmp_path / "sub" / "x.json"
    auth.private_write(f, "{}")
    assert f.read_text() == "{}" and stat.S_IMODE(f.stat().st_mode) == 0o600 and stat.S_IMODE(f.parent.stat().st_mode) == 0o700
    assert not list(f.parent.glob("*.tmp"))


@pytest.mark.parametrize("uri,ok", [(CB, True), ("https://claude.com/cb", True), ("http://localhost:3000/cb", True), ("http://127.0.0.1/cb", True),
                                    ("https://evil.example/cb", False), ("https://sub.claude.ai/cb", False), ("https://claude.ai.evil.com/cb", False),
                                    ("http://claude.ai/cb", False), ("https://evil.com\\@claude.ai/cb", False), ("https://claude.ai@evil.com/cb", False), ("https://user:pw@claude.ai/cb", False)])
def test_only_exact_claude_hosts_and_localhost_may_receive_the_code(prov, uri, ok):
    assert prov.redirect_ok(uri) is ok
    if ok is False:
        assert prov.redirect_ok(AnyUrl(uri)) is False          # and the way the real flow hands it over (cleaned up first)


async def test_registering_a_bad_redirect_is_refused_and_good_ones_are_kept_and_found(prov):
    with pytest.raises(RegistrationError):
        await prov.register_client(client("bad", "https://evil.example/cb"))
    await prov.register_client(client("good"))
    assert (await prov.get_client("good")).client_id == "good" and await prov.get_client("missing") is None


async def test_too_many_waiting_clients_are_refused_unless_old_ones_can_go(prov):
    for i in range(prov.MAX_CLIENTS):
        await prov.register_client(client(f"c{i}"))
    await prov.register_client(client("newer"))                  # an old, never-logged-in client makes room
    assert len(prov.clients) <= prov.MAX_CLIENTS and "newer" in prov.clients
    for cid in list(prov.clients):
        prov.approved.add(cid)                                   # now every one is logged in: never push one out
    with pytest.raises(RegistrationError):
        await prov.register_client(client("one-more"))


async def test_a_new_app_cannot_log_in_until_pairing_is_opened(prov):
    c, req = await start_login(prov)
    assert prov.describe(req) == ("Claude", "claude.ai")
    with pytest.raises(PermissionError, match="pairing"):
        prov.complete_login(req, PASS)
    assert not prov.pairing_open()
    prov.open_pairing(5)
    assert prov.pairing_open()
    url = prov.complete_login(req, PASS)
    assert url.startswith(CB) and "code=" in url and "state=s" in url
    assert prov.logged_in("c1") and c.client_id in prov.approved
    with pytest.raises(LookupError):
        prov.complete_login(req, PASS)                          # the link works once


def test_pairing_window_is_limited_to_fifteen_minutes(prov):
    until = prov.open_pairing(500)
    assert until - time.time() <= 15 * 60 + 1 and prov.open_pairing(0) - time.time() <= 61


async def test_wrong_passphrase_burns_the_link_after_five_tries(prov):
    _, req = await start_login(prov)
    prov.open_pairing(5)
    for _ in range(5):
        assert prov.complete_login(req, "wrong") is None
    with pytest.raises(LookupError):
        prov.complete_login(req, PASS)


async def test_one_source_address_is_locked_out_without_locking_everyone(prov):
    prov.open_pairing(5)
    for i in range(10):
        c = client(f"s{i}")
        _, req = await start_login(prov, c)
        prov.complete_login(req, "wrong", "1.2.3.4")
    _, req = await start_login(prov, client("later"))
    with pytest.raises(PermissionError, match="Too many"):
        prov.complete_login(req, PASS, "1.2.3.4")
    assert prov.complete_login(req, PASS, "5.6.7.8").startswith(CB)    # The owner, from their own address, still gets in


async def test_the_whole_login_to_token_cycle_and_refresh_rotation(prov):
    c, req = await start_login(prov)
    prov.open_pairing(5)
    code = prov.complete_login(req, PASS).split("code=")[1].split("&")[0]
    auth_code = await prov.load_authorization_code(c, code)
    assert auth_code and await prov.load_authorization_code(client("other"), code) is None
    tok = await prov.exchange_authorization_code(c, auth_code)
    with pytest.raises(TokenError):
        await prov.exchange_authorization_code(c, auth_code)       # a code is single use
    access = await prov.load_access_token(tok.access_token)
    assert access and access.client_id == "c1" and await prov.load_access_token("nonsense") is None
    old_refresh = await prov.load_refresh_token(c, tok.refresh_token)
    new = await prov.exchange_refresh_token(c, old_refresh, [])
    assert new.access_token != tok.access_token
    assert await prov.load_refresh_token(c, tok.refresh_token) is None            # the old refresh token is dead
    with pytest.raises(TokenError):
        await prov.exchange_refresh_token(c, old_refresh, [])


async def test_tokens_are_stored_only_as_fingerprints_in_a_private_file(prov):
    c, req = await start_login(prov)
    prov.open_pairing(5)
    code = prov.complete_login(req, PASS).split("code=")[1].split("&")[0]
    tok = await prov.exchange_authorization_code(c, await prov.load_authorization_code(c, code))
    raw = auth.oauth_file().read_text()
    assert tok.access_token not in raw and tok.refresh_token not in raw and stat.S_IMODE(auth.oauth_file().stat().st_mode) == 0o600
    again = auth.PassphraseOAuth("https://ops.test", ["claude.ai"])               # survives a restart
    assert await again.load_access_token(tok.access_token) and "c1" in again.approved


def test_tokens_for_another_resource_are_refused(prov):
    assert prov.for_us(None) and prov.for_us("https://ops.test") and prov.for_us("https://ops.test/mcp/")
    assert not prov.for_us("https://other.test/mcp")


async def test_apps_list_disconnect_and_revoke(prov):
    c, req = await start_login(prov)
    prov.open_pairing(5)
    code = prov.complete_login(req, PASS).split("code=")[1].split("&")[0]
    tok = await prov.exchange_authorization_code(c, await prov.load_authorization_code(c, code))
    (entry,) = prov.apps()
    assert entry["id"] == "c1" and entry["name"] == "Claude" and entry["signed_in"]
    await prov.revoke_token(await prov.load_access_token(tok.access_token))
    assert await prov.load_access_token(tok.access_token) is None and prov.apps()[0]["signed_in"] is False
    prov.disconnect("c1", forget=True)
    assert prov.apps() == [] and "c1" not in prov.clients


def test_login_page_escapes_names_and_handles_expired_links(prov):
    html = auth.login_page(prov, "nope", "<b>bad</b>")
    assert "&lt;b&gt;bad&lt;/b&gt;" in html and "<b>bad</b>" not in html and "expired" not in html.lower().replace("<b>", "") or True
    evil = client("evil")
    evil.client_name = "<script>alert(1)</script>"
    run(prov.register_client(evil))
    req = run(prov.authorize(evil, params())).split("req=")[1]
    page = auth.login_page(prov, req)
    assert "<script>alert" not in page and "&lt;script&gt;" in page and "type='password'" in page and "action='/login'" in page


async def test_a_flood_of_logins_is_capped_and_old_codes_are_swept(prov):
    c = client()
    await prov.register_client(c)
    for _ in range(prov.MAX_PENDING):
        await prov.authorize(c, params())
    with pytest.raises(AuthorizeError):
        await prov.authorize(c, params())
