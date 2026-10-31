import asyncio

import httpx
import pytest
from starlette.testclient import TestClient

from conftest import text
from opsmcp import cloudflare, confirm_app, consent, coolify, terminal
from test_cloudflare_changes import ACCT, TUN, ZONE, FakeCF, cf, tap  # noqa: F401 (the fixture is used by name)
from test_terminal import World, ssh  # noqa: F401


def test_a_missing_zone_name_stops_every_cloudflare_change(cf, monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_NAME", "")
    with pytest.raises(cloudflare.CloudflareError, match="zone name"):
        cloudflare.check_hostname("x.example.com")


async def test_two_records_with_the_same_name_are_left_for_the_dashboard(cf):
    cf.dns["dup" + "x" * 30] = {"id": "dup" + "x" * 30, "type": "A", "name": "app.example.com", "content": "8.8.8.8", "proxied": False, "ttl": 1}
    with pytest.raises(cloudflare.CloudflareError, match="more than one"):
        await cloudflare.dns_find("app.example.com", "A")


async def test_delete_refuses_a_record_that_vanished_or_changed(cf):
    old = cloudflare._pick_dns(cf.dns["r1" + "x" * 30])
    payload = {"name": "app.example.com", "type": "A", "old_digest": cloudflare.digest(old)}
    cf.dns["r1" + "x" * 30]["content"] = "6.6.6.6"
    with pytest.raises(cloudflare.CloudflareError, match="changed after"):
        await cloudflare.dns_delete(payload)
    cf.dns.clear()
    with pytest.raises(cloudflare.CloudflareError, match="does not exist"):
        await cloudflare.dns_delete(payload)
    assert cf.writes == []


async def test_a_tunnel_answer_in_the_wrong_shape_is_refused(cf):
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(200, json={"success": True, "result": {"config": {"ingress": "not a list"}}}))
    with pytest.raises(cloudflare.CloudflareError, match="expected format"):
        await cloudflare.tunnel_config()


async def test_route_delete_refuses_a_changed_tunnel_or_a_vanished_route(cf):
    payload = {"hostname": "app.example.com", "old_digest": cloudflare.digest(cf.ingress)}
    cf.ingress.insert(0, {"hostname": "x.example.com", "service": "http://localhost:1"})
    with pytest.raises(cloudflare.CloudflareError, match="changed after"):
        await cloudflare.route_delete(payload)
    cf.ingress = [r for r in cf.ingress if r.get("hostname") != "app.example.com"]
    with pytest.raises(cloudflare.CloudflareError, match="does not exist"):
        await cloudflare.route_delete({"hostname": "app.example.com", "old_digest": cloudflare.digest(cf.ingress)})
    assert cf.writes == []


def test_log_lines_ignore_things_that_are_not_logs():
    assert coolify._log_lines(None) == [] and coolify._log_lines({"a": 1}) == [] and coolify._log_lines([{"output": "a\nb"}, "plain", 5]) == ["a", "b", "plain", "5"]


async def test_the_terminal_reports_a_failed_open_and_a_failed_key_press(ssh, monkeypatch):
    real = World.answer

    def answer(self, cmd):
        if cmd.startswith("tmux new-session"):
            return real(self, "df")                      # exit 0 would be wrong, so force a failure
        return real(self, cmd)
    monkeypatch.setattr(World, "answer", lambda self, cmd: type("R", (), {"exit_status": 1, "stdout": "", "stderr": "x"})() if cmd.startswith("tmux new-session") else real(self, cmd))
    with pytest.raises(terminal.TerminalError, match="Could not open"):
        await terminal.open_session("main")
    monkeypatch.setattr(World, "answer", real)
    await terminal.open_session("main")
    monkeypatch.setattr(World, "answer", lambda self, cmd: type("R", (), {"exit_status": 1, "stdout": "", "stderr": ""})() if "Enter" in cmd else real(self, cmd))
    with pytest.raises(terminal.TerminalError, match="does not exist"):
        await terminal.write("main", "ls", "enter")


# ------------------------------------------------------------ typed confirm on the page
def test_the_page_asks_for_the_word_and_a_wrong_word_changes_nothing(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    web = TestClient(confirm_app.app(), follow_redirects=False)
    form = {"content-type": "application/x-www-form-urlencoded"}

    async def run(p, s):
        return "ok"
    t = consent.ENGINE.create("t", "DELETE a thing", {}, run, confirm_word="app.example.com")
    page = web.get(f"/confirm/{t.id}").text
    assert "type <b>app.example.com</b> exactly" in page and "name='typed'" in page and "form='ok'" in page
    token = consent.csrf(t.id, "test@localhost")
    r = web.post(f"/confirm/{t.id}/approve", headers=form, data={"csrf": token, "typed": "App.example.com"})
    assert r.headers["location"] == "/confirm?n=typed" and consent.ENGINE.get(t.id).status == "pending"
    assert "did not match" in web.get("/confirm?n=typed").text
    r = web.post(f"/confirm/{t.id}/approve", headers=form, data={"csrf": token})
    assert consent.ENGINE.get(t.id).status == "pending"
    r = web.post(f"/confirm/{t.id}/approve", headers=form, data={"csrf": token, "typed": "app.example.com"})
    assert r.headers["location"] == "/confirm?n=confirmed" and consent.ENGINE.get(t.id).status == "approved"
    d = consent.ENGINE.create("t", "x", {}, run, confirm_word="word")
    assert web.post(f"/confirm/{d.id}/deny", headers=form, data={"csrf": consent.csrf(d.id, "test@localhost")}).headers["location"] == "/confirm?n=denied"   # denying never needs the word
