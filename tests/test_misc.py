import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from opsmcp import access, audit, config, consent, safety


def test_config_getters_use_defaults_and_overrides(monkeypatch):
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("ADMIN_PORT", "9998")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "7")
    assert (config.port(), config.admin_port(), config.host(), config.http_timeout()) == (9999, 9998, "127.0.0.1", 7)
    monkeypatch.setenv("PORT", "not a number")
    assert config.port() == 8765 and config.env_int("NOPE_X", 5) == 5
    monkeypatch.setenv("ALLOWED_REDIRECT_HOSTS", " Claude.AI , ,claude.com ")
    assert config.redirect_hosts() == ["claude.ai", "claude.com"]
    monkeypatch.setenv("FLAG_X", "Yes")
    assert config.flag("FLAG_X") and not config.flag("FLAG_NOT_SET")
    assert config.confirm_url() == "http://localhost:8766" and config.public_url() == "http://localhost:8765"
    assert config.coolify_url() == "https://coolify.test" and config.cf_account() == "" and config.cf_zone() == "" and config.cf_read_token() == ""
    assert (config.confirm_wait(), config.confirm_ttl(), config.output_max_chars(), config.max_log_lines(), config.rate_limit_per_minute()) == (2, 300, 8000, 200, 30)


def test_as_json_masks_and_formats():
    out = safety.as_json({"name": "x", "token": "abcdef"})
    assert json.loads(out) == {"name": "x", "token": "***"}


def test_recent_log_skips_damaged_lines_and_handles_a_missing_file():
    assert audit.recent() == []
    audit.log("ok", n=1)
    with audit.log_file().open("a") as f:
        f.write("not json\n")
    audit.log("second", n=2)
    lines = audit.recent(10)
    assert len(lines) == 2 and lines[0].split()[2] == "second"


def test_summary_that_is_too_long_is_refused_not_cut():
    async def run(p, s):
        return "x"
    with pytest.raises(consent.ConsentError, match="too long"):
        consent.ENGINE.create("t", "x" * (consent.MAX_SUMMARY + 1), {}, run)
    consent.ENGINE.create("t", "x" * consent.MAX_SUMMARY, {}, run)


def test_old_tickets_are_forgotten_and_a_late_tap_still_gets_a_grace_period(monkeypatch):
    async def run(p, s):
        return "x"
    t = consent.ENGINE.create("t", "s", {}, run)
    t.expires = time.time() + 1                          # nearly expired
    consent.ENGINE.decide(t.id, True, "a@b.c")
    assert t.expires >= time.time() + consent.LATE_GRACE - 2
    t.expires = time.time() - 4000
    assert consent.ENGINE.get(t.id) is None


async def test_late_collection_still_runs_after_a_tap_near_the_end():
    ran = []

    async def run(p, s):
        ran.append(1)
        return "ok"
    t = consent.ENGINE.create("t", "s", {}, run)
    t.expires = time.time() + 0.05
    consent.ENGINE.decide(t.id, True, "a@b.c")
    import asyncio
    await asyncio.sleep(0.1)                             # the original deadline has passed
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "done" and ran == [1]


async def test_unknown_ticket_and_the_secret_is_forgotten_after_the_run():
    assert (await consent.ENGINE.run_if_approved("nope"))[0] == "unknown"

    async def run(p, s):
        return "ok"
    t = consent.ENGINE.create("t", "s", {}, run, secret="topsecret")
    consent.ENGINE.decide(t.id, True, "a@b.c")
    await consent.ENGINE.run_if_approved(t.id)
    assert t.secret is None
    d = consent.ENGINE.create("t", "s", {}, run, secret="topsecret2")
    consent.ENGINE.decide(d.id, False, "a@b.c")
    assert d.secret is None


def test_freeze_holds_even_when_the_file_cannot_be_written(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", "/proc/definitely/not/writable")
    consent.set_frozen(True)
    assert consent.frozen()
    consent.set_frozen(False)
    assert not consent.frozen()


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def test_access_keys_client_is_built_for_the_team(monkeypatch):
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", "https://team.cloudflareaccess.com/")
    monkeypatch.setattr(access, "_client", None)
    built = {}
    monkeypatch.setattr(jwt, "PyJWKClient", lambda url, **kw: built.update(url=url) or object())
    access._keys()
    assert built["url"] == "https://team.cloudflareaccess.com/cdn-cgi/access/certs"
    monkeypatch.setattr(access, "_client", None)


async def test_access_refuses_a_missing_header_when_enforcing(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", "t.cloudflareaccess.com")
    monkeypatch.setenv("CF_ACCESS_AUD", "aud")
    monkeypatch.setenv("CONFIRM_ALLOWED_EMAILS", "a@b.c")
    assert await access.who({}) is None
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    assert (await access.who({}))["email"] == "test@localhost"
