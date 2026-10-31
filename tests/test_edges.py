"""The last single lines: odd paths that must still end safely."""
import asyncio
import os
import time

import httpx
import pytest
from mcp.server.auth.provider import AuthorizeError
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import AnyUrl
from starlette.testclient import TestClient

from conftest import APP, install, text
from opsmcp import auth, confirm_app, consent, coolify, server
from test_auth import client, params

CALL = server.mcp.call_tool


def test_a_failed_private_write_leaves_no_half_written_file(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        auth.private_write(tmp_path / "x.json", "{}")
    assert list(tmp_path.iterdir()) == []


async def test_clients_that_are_all_waiting_make_room_and_a_bad_redirect_cannot_start_a_login(monkeypatch):
    monkeypatch.setenv("LOGIN_HASH", "h")
    p = auth.PassphraseOAuth("https://ops.test", ["claude.ai"])
    for i in range(p.MAX_CLIENTS):
        await p.register_client(client(f"c{i}"))
    await p.register_client(client("fresh"))
    assert "fresh" in p.clients and len(p.clients) == p.MAX_CLIENTS
    with pytest.raises(AuthorizeError):
        await p.authorize(client("fresh"), params("https://evil.example/cb"))


def test_unfreezing_from_the_page_works(monkeypatch):
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    web = TestClient(confirm_app.app(), follow_redirects=False)
    form = {"content-type": "application/x-www-form-urlencoded"}
    tok = consent.csrf("freeze", "test@localhost")
    web.post("/freeze", headers=form, data={"csrf": tok})
    assert consent.frozen()
    assert web.post("/freeze", headers=form, data={"csrf": tok}).headers["location"] == "/confirm?n=unfrozen" and not consent.frozen()


def test_an_unfreeze_runs_out_by_itself_and_survives_a_restart(monkeypatch):
    monkeypatch.setenv("UNFREEZE_MINUTES", "60")
    consent.set_frozen(False)
    assert not consent.frozen() and consent.until_file().exists()
    consent._until = 0.0                                          # a restart forgets memory; the file keeps the timer
    assert consent.unfrozen_until() > time.time() + 3500
    monkeypatch.setattr(consent.time, "time", lambda: consent.unfrozen_until() + 1)
    assert consent.frozen() and consent.frozen_file().exists() and not consent.until_file().exists()
    with pytest.raises(consent.ChangesOff):
        consent.ENGINE.create("t", "s", {}, None)


def test_unfreeze_minutes_zero_means_no_timer(monkeypatch):
    monkeypatch.setenv("UNFREEZE_MINUTES", "0")
    consent.set_frozen(False)
    assert consent.unfrozen_until() == 0 and not consent.until_file().exists() and not consent.frozen()


def test_the_page_shows_when_changes_freeze_again(monkeypatch):
    monkeypatch.setenv("UNFREEZE_MINUTES", "60")
    consent.set_frozen(False)
    web = TestClient(confirm_app.app(), follow_redirects=False)
    assert "freeze again by themselves at" in web.get("/confirm").text


def test_the_frozen_refusal_gives_claude_the_link_to_send(monkeypatch):
    monkeypatch.setenv("CONFIRM_URL", "https://confirm.example.com")
    consent.set_frozen(True)
    with pytest.raises(consent.ChangesOff, match="https://confirm.example.com/confirm"):
        consent.ENGINE.create("t", "s", {}, None)


async def test_a_ticket_that_is_already_running_says_so_and_does_not_start_twice():
    gate = asyncio.Event()
    count = []

    async def slow(p, s):
        count.append(1)
        await gate.wait()
        return "ok"
    t = consent.ENGINE.create("t", "s", {}, slow)
    consent.ENGINE.decide(t.id, True, "a@b.c")
    first = asyncio.create_task(consent.ENGINE.run_if_approved(t.id))
    await asyncio.sleep(0.05)
    assert (await consent.ENGINE.run_if_approved(t.id))[0] == "running"
    gate.set()
    assert (await first)[0] == "done" and len(count) == 1


async def test_an_error_message_that_is_not_json_is_still_a_clean_refusal():
    install({("POST", "/api/v1/deployments/dep1234567/cancel"): lambda r: httpx.Response(400, text="<html>nope</html>")})
    with pytest.raises(coolify.CoolifyError, match="refused the request"):
        await coolify.cancel("dep1234567")


async def test_diagnose_survives_a_failing_deployment_lookup():
    install({("GET", "/api/v1/resources"): (200, [{"type": "application", "name": "bad", "uuid": APP, "status": "exited"}]),
             ("GET", f"/api/v1/deployments/applications/{APP}"): (500, {})})
    assert "bad" in await coolify.diagnose()


async def test_a_toolerror_raised_inside_a_tool_passes_through_untouched(monkeypatch):
    async def boom():
        raise ToolError("our own message")
    monkeypatch.setattr(coolify, "overview", boom)
    with pytest.raises(ToolError, match="our own message"):
        await CALL("coolify_overview", {})


async def test_a_ticket_still_works_when_the_name_lookup_fails():
    install({("GET", f"/api/v1/applications/{APP}"): (500, {}), ("POST", "/api/v1/deploy"): (200, {"deployments": [{"deployment_uuid": "d" * 8}]})})
    task = asyncio.create_task(CALL("coolify_deploy", {"id": APP}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    consent.ENGINE.decide(t.id, True, "a@b.c")
    assert text(await task).startswith("Done:") and t.summary == f"Deploy id {APP}"


async def test_a_value_that_changes_after_approval_is_refused_and_bad_values_never_become_tickets():
    with pytest.raises(ConsentError := consent.ConsentError):
        await server.run_env_set({"value_sha256": "0" * 64, "id": APP, "key": "A", "is_literal": True}, "different value")
    install({})
    for bad in ("x" * 4001, "has\x00null"):
        with pytest.raises(ToolError):
            await CALL("coolify_env_set", {"id": APP, "key": "A", "value": bad})
    assert consent.ENGINE.open_tickets() == []


async def test_clients_that_never_logged_in_are_dropped_after_an_hour(monkeypatch):
    monkeypatch.setenv("LOGIN_HASH", "h")
    p = auth.PassphraseOAuth("https://ops.test", ["claude.ai"])
    old = client("stale")
    old.client_id_issued_at = 1000                       # long ago
    await p.register_client(old)
    await p.register_client(client("new"))
    assert "stale" not in p.clients and "new" in p.clients
