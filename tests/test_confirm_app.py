import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

from opsmcp import access, confirm_app, consent

TEAM, AUD, EMAIL = "team.cloudflareaccess.com", "aud-tag-123", "owner@example.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeKeys:
    def get_signing_key_from_jwt(self, token):
        class K:
            key = KEY.public_key()
        return K()


def token(email=EMAIL, aud=AUD, iss=f"https://{TEAM}", exp=3600, key=KEY):
    now = int(time.time())
    return jwt.encode({"email": email, "aud": aud, "iss": iss, "iat": now, "exp": now + exp}, key, algorithm="RS256")


@pytest.fixture
def zt(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", TEAM)
    monkeypatch.setenv("CF_ACCESS_AUD", AUD)
    monkeypatch.setenv("CONFIRM_ALLOWED_EMAILS", EMAIL)
    monkeypatch.setattr(access, "_keys", lambda: FakeKeys())
    return TestClient(confirm_app.app(), follow_redirects=False)


def hdr(**kw):
    return {"cf-access-jwt-assertion": token(**kw)}


def ticket(summary="Deploy app"):
    async def run(p, secret):
        return "ok"
    return consent.ENGINE.create("t", summary, {"a": 1}, run, why="because")


def test_health_is_open_and_everything_else_needs_zero_trust(zt):
    assert zt.get("/health").text == "ok"
    assert zt.get("/confirm").status_code == 401
    assert zt.get("/confirm", headers={"cf-access-jwt-assertion": "garbage"}).status_code == 401


@pytest.mark.parametrize("kw", [dict(email="someone@else.com"), dict(aud="wrong"), dict(iss="https://evil.test"), dict(exp=-3600)])
def test_wrong_email_audience_issuer_or_expired_token_is_refused(zt, kw):
    assert zt.get("/confirm", headers=hdr(**kw)).status_code == 401


def test_token_signed_with_another_key_is_refused(zt):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert zt.get("/confirm", headers=hdr(key=other)).status_code == 401


def test_enforcing_but_not_configured_refuses_everything(zt, monkeypatch):
    monkeypatch.setenv("CONFIRM_ALLOWED_EMAILS", "")
    assert zt.get("/confirm", headers=hdr()).status_code == 401


def test_page_shows_tickets_and_escapes_everything(zt):
    ticket("<script>alert(1)</script> & <img src=x onerror=alert(2)>")
    r = zt.get(f"/confirm/{consent.ENGINE.open_tickets()[0].id}", headers=hdr())
    assert r.status_code == 200 and "<script>alert" not in r.text and "&lt;script&gt;" in r.text and "onerror=alert" not in r.text.replace("&lt;img src=x onerror=alert(2)&gt;", "")
    assert "script-src" not in r.headers["content-security-policy"] and "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY" and r.headers["cache-control"] == "no-store"


def test_confirm_needs_the_right_form_token(zt):
    t = ticket()
    h = {**hdr(), "content-type": "application/x-www-form-urlencoded"}
    assert zt.post(f"/confirm/{t.id}/approve", headers=h, data={"csrf": "wrong"}).status_code == 403
    other = ticket()
    assert zt.post(f"/confirm/{t.id}/approve", headers=h, data={"csrf": consent.csrf(other.id, EMAIL)}).status_code == 403
    assert consent.ENGINE.get(t.id).status == "pending"
    ok = zt.post(f"/confirm/{t.id}/approve", headers=h, data={"csrf": consent.csrf(t.id, EMAIL)})
    assert ok.status_code == 303 and consent.ENGINE.get(t.id).status == "approved" and consent.ENGINE.get(t.id).decided_by == EMAIL


def test_deny_works_and_cannot_be_flipped(zt):
    t = ticket()
    h = {**hdr(), "content-type": "application/x-www-form-urlencoded"}
    zt.post(f"/confirm/{t.id}/deny", headers=h, data={"csrf": consent.csrf(t.id, EMAIL)})
    assert consent.ENGINE.get(t.id).status == "denied"
    zt.post(f"/confirm/{t.id}/approve", headers=h, data={"csrf": consent.csrf(t.id, EMAIL)})
    assert consent.ENGINE.get(t.id).status == "denied"


def test_cross_site_posts_and_wrong_content_types_are_refused(zt):
    t = ticket()
    form = {**hdr(), "content-type": "application/x-www-form-urlencoded"}
    csrf = {"csrf": consent.csrf(t.id, EMAIL)}
    assert zt.post(f"/confirm/{t.id}/approve", headers={**form, "origin": "https://evil.test"}, data=csrf).status_code == 403
    assert zt.post(f"/confirm/{t.id}/approve", headers={**hdr(), "content-type": "application/json"}, content=b"{}").status_code == 415
    assert consent.ENGINE.get(t.id).status == "pending"


def test_the_pages_own_forms_send_their_origin_and_pass(zt):
    # Found in a real browser test: with Referrer-Policy no-referrer, Chrome sent "Origin: null" and every tap was refused.
    page = zt.get("/confirm", headers=hdr())
    assert page.headers["referrer-policy"] == "same-origin"
    h = {**hdr(), "content-type": "application/x-www-form-urlencoded", "origin": "http://testserver"}
    assert zt.post("/freeze", headers=h, data={"csrf": consent.csrf("freeze", EMAIL)}).status_code == 303
    assert zt.post("/freeze", headers={**h, "origin": "null"}, data={"csrf": consent.csrf("freeze", EMAIL)}).status_code == 403


def test_freeze_switch_needs_a_token_and_blocks_new_tickets(zt):
    h = {**hdr(), "content-type": "application/x-www-form-urlencoded"}
    assert zt.post("/freeze", headers=h, data={"csrf": "x"}).status_code == 403 and not consent.frozen()
    assert zt.post("/freeze", headers=h, data={"csrf": consent.csrf("freeze", EMAIL)}).status_code == 303
    assert consent.frozen()
    with pytest.raises(consent.ConsentError):
        ticket()


def test_the_list_page_has_no_confirm_buttons_and_never_refreshes(zt):
    t = ticket("Deploy studio")
    page = zt.get("/confirm", headers=hdr()).text
    assert "Deploy studio" in page and "/approve" not in page and "refresh" not in page.lower() and f"/confirm/{t.id}" in page


def test_the_ticket_page_shows_the_exact_ticket_and_does_not_refresh(zt):
    t = ticket("Deploy studio")
    page = zt.get(f"/confirm/{t.id}", headers=hdr()).text
    assert "Deploy studio" in page and f"/confirm/{t.id}/approve" in page and "refresh" not in page.lower() and "because" in page
    consent.ENGINE.decide(t.id, False, EMAIL)
    assert "no longer open" in zt.get(f"/confirm/{t.id}", headers=hdr()).text
    assert "no longer open" in zt.get("/confirm/doesnotexist1", headers=hdr()).text


def test_freeze_cancels_open_tickets(zt):
    t = ticket()
    h = {**hdr(), "content-type": "application/x-www-form-urlencoded"}
    zt.post("/freeze", headers=h, data={"csrf": consent.csrf("freeze", EMAIL)})
    assert consent.ENGINE.get(t.id).status == "denied"
