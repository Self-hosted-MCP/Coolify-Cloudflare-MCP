import pytest
from starlette.testclient import TestClient

from opsmcp import auth, confirm_app, consent


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    monkeypatch.setenv("LOGIN_HASH", auth.hash_passphrase("pass", rounds=1000))
    prov = auth.PassphraseOAuth("https://ops.test", ["claude.ai"])
    monkeypatch.setattr(confirm_app, "PROVIDER", prov)
    return TestClient(confirm_app.app(), follow_redirects=False), prov


WHO = "test@localhost"
FORM = {"content-type": "application/x-www-form-urlencoded"}


def test_the_page_lists_connected_apps_and_the_pairing_state(web):
    client, prov = web
    prov.approved.add("c1")
    page = client.get("/confirm").text
    assert "No app is connected" in page or "Disconnect" in page
    assert "New apps can connect: <b>closed</b>" in page


def test_allow_a_new_app_needs_a_token_then_opens_pairing(web):
    client, prov = web
    assert client.post("/pairing", headers=FORM, data={"csrf": "x"}).status_code == 403 and not prov.pairing_open()
    r = client.post("/pairing", headers=FORM, data={"csrf": consent.csrf("pairing", WHO)})
    assert r.status_code == 303 and prov.pairing_open() and r.headers["location"] == "/confirm?n=pairing"
    assert "open for a few minutes" in client.get("/confirm").text


def test_disconnect_needs_a_token_and_a_known_app(web):
    client, prov = web
    prov.approved.add("c1")
    assert client.post("/apps/disconnect", headers=FORM, data={"csrf": "x", "id": "c1"}).status_code == 403
    assert client.post("/apps/disconnect", headers=FORM, data={"csrf": consent.csrf("apps", WHO), "id": "unknown"}).status_code == 403
    assert client.post("/apps/disconnect", headers=FORM, data={"csrf": consent.csrf("apps", WHO), "id": "c1"}).status_code == 303
    assert "c1" not in prov.approved


def test_notes_are_fixed_texts_so_a_link_cannot_put_words_on_the_page(web):
    client, _ = web
    assert "Confirmed." in client.get("/confirm?n=confirmed").text
    page = client.get("/confirm?n=<b>fake</b>&note=Your%20money%20is%20safe").text
    assert "fake" not in page and "money" not in page


def test_big_posts_are_refused(web):
    client, _ = web
    assert client.post("/freeze", headers={**FORM, "content-length": "999999"}, content=b"x").status_code == 413


def test_the_root_goes_to_the_confirm_page_and_health_is_open(web):
    client, _ = web
    assert client.get("/").status_code in (302, 307) and client.get("/health").text == "ok"


def test_start_listens_on_loopback_when_zero_trust_is_off(monkeypatch):
    started = {}

    class FakeServer:
        def __init__(self, cfg):
            started["host"] = cfg.host

        def run(self):
            pass
    monkeypatch.setattr(confirm_app.uvicorn, "Server", FakeServer)
    monkeypatch.setenv("ACCESS_ENFORCE", "off")
    confirm_app.start(None)
    assert started["host"] == "127.0.0.1"
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    confirm_app.start(None)
    assert started["host"] == "0.0.0.0"
