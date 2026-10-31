import asyncio

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from conftest import APP, install, text
from opsmcp import audit, auth, consent, coolify, server

CALL = server.mcp.call_tool


async def tap(approve=True, delay=0.2):
    await asyncio.sleep(delay)
    (t,) = consent.ENGINE.open_tickets()
    consent.ENGINE.decide(t.id, approve, "owner@example.com")
    return t


async def test_cancel_control_and_env_delete_go_through_a_ticket_and_reach_coolify_once():
    fake = install({("GET", f"/api/v1/applications/{APP}"): (200, {"name": "studio", "uuid": APP}),
                    ("POST", "/api/v1/deployments/dep1234567/cancel"): (200, {}),
                    ("POST", f"/api/v1/applications/{APP}/restart"): (200, {}),
                    ("GET", f"/api/v1/applications/{APP}/envs"): (200, [{"key": "A", "uuid": "envuuid0001"}]),
                    ("DELETE", f"/api/v1/applications/{APP}/envs/envuuid0001"): (200, {})})
    for tool, args, risk in (("coolify_cancel_deployment", {"deployment_id": "dep1234567"}, "high"),
                             ("coolify_control", {"kind": "application", "id": APP, "action": "restart"}, "normal"),
                             ("coolify_env_delete", {"id": APP, "key": "A"}, "high")):
        task = asyncio.create_task(CALL(tool, args))
        t = await tap()
        assert text(await task).startswith("Done:") and t.risk == risk
    assert [r.method for r in fake.seen if r.method in ("POST", "DELETE")] == ["POST", "POST", "DELETE"]


async def test_starting_an_app_says_that_coolify_will_queue_a_deployment():
    install({("GET", f"/api/v1/applications/{APP}"): (200, {"name": "studio", "uuid": APP}), ("POST", f"/api/v1/applications/{APP}/start"): (200, {})})
    task = asyncio.create_task(CALL("coolify_control", {"kind": "application", "id": APP, "action": "start"}))
    t = await tap()
    await task
    assert "queues a deployment" in t.summary


async def test_the_remaining_read_tools_answer_and_wrap_their_output():
    install({("GET", f"/api/v1/applications/{APP}/envs"): (200, [{"key": "A", "value": "secretvalue", "uuid": "u1"}]),
             ("GET", "/api/v1/resources"): (200, []),
             ("GET", "/api/v1/deployments"): (200, [{"deployment_uuid": "d1", "status": "in_progress"}])})
    for tool, args, needle in (("coolify_env_list", {"id": APP}, '"A"'), ("coolify_diagnose", {}, "Nothing looks wrong"), ("coolify_deployments", {}, "in_progress")):
        out = text(await CALL(tool, args))
        assert needle in out and out.startswith("[Content from Coolify.") and out.rstrip().endswith("[End of content from Coolify.]") and "secretvalue" not in out


async def test_ops_log_and_cloudflare_overview(monkeypatch):
    audit.log("hello", n=1)
    assert "hello" in text(await CALL("ops_log", {"limit": 5}))
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "t")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "a" * 32)
    from opsmcp import cloudflare
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(200, json={"success": True, "result": [{"name": "tun", "status": "healthy", "id": "i"}]}))
    out = text(await CALL("cloudflare_overview", {}))
    assert "Tunnels" in out and out.startswith("[Content from Cloudflare.")


async def test_status_in_every_state(monkeypatch):
    install({("GET", "/api/v1/version"): (500, {})})
    out = text(await CALL("ops_status", {}))
    assert "Coolify: PROBLEM" in out and "allowed, each needs the owner's tap" in out
    consent.set_frozen(True)
    assert "FROZEN" in text(await CALL("ops_status", {}))
    monkeypatch.setenv("READ_ONLY", "1")
    assert "read-only" in text(await CALL("ops_status", {}))
    monkeypatch.setenv("COOLIFY_TOKEN", "")
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    out = text(await CALL("ops_status", {}))
    assert "Coolify: not set up" in out and "NOT READY" in out and "Cloudflare: not set up" in out


async def test_an_unexpected_error_inside_a_tool_gives_a_generic_message_and_logs_only_its_type(monkeypatch):
    async def boom():
        raise RuntimeError("secret detail token=abcd1234efgh5678")
    monkeypatch.setattr(coolify, "overview", boom)
    with pytest.raises(ToolError) as exc:
        await CALL("coolify_overview", {})
    assert "abcd1234efgh5678" not in str(exc.value) and "Nothing was changed" in str(exc.value)
    assert "RuntimeError" in "\n".join(audit.recent(10)) and "abcd1234efgh5678" not in "\n".join(audit.recent(10))


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("LOGIN_HASH", auth.hash_passphrase("pass", rounds=1000))
    return TestClient(server.mcp.streamable_http_app(), base_url="http://localhost:8765", follow_redirects=False)


def test_health_and_the_login_page_basics(web):
    assert web.get("/health").text == "ok"
    page = web.get("/login?req=nothing")
    assert page.status_code == 200 and "expired" in page.text and page.headers["x-frame-options"] == "DENY" and page.headers["cache-control"] == "no-store"


async def test_login_post_paths(web, monkeypatch):
    prov = server.PROVIDER
    from mcp.shared.auth import OAuthClientInformationFull
    from mcp.server.auth.provider import AuthorizationParams
    from pydantic import AnyUrl
    c = OAuthClientInformationFull(client_id="web1", client_name="Claude", redirect_uris=[AnyUrl("https://claude.ai/cb")])
    await prov.register_client(c)
    req = (await prov.authorize(c, AuthorizationParams(state="s", scopes=["ops"], code_challenge="x" * 43, redirect_uri=AnyUrl("https://claude.ai/cb"),
                                                       redirect_uri_provided_explicitly=True))).split("req=")[1]
    assert web.post("/login", data={"req": req, "passphrase": "pass"}).status_code == 403          # pairing closed
    prov.open_pairing(5)
    real_sleep = asyncio.sleep
    monkeypatch.setattr(asyncio, "sleep", lambda s: real_sleep(0))
    assert web.post("/login", data={"req": req, "passphrase": "wrong"}).status_code == 401
    ok = web.post("/login", data={"req": req, "passphrase": "pass"})
    assert ok.status_code == 302 and ok.headers["location"].startswith("https://claude.ai/cb?code=")
    assert web.post("/login", content=b"x" * 5000, headers={"content-type": "application/x-www-form-urlencoded"}).status_code == 413


def test_main_refuses_to_start_when_unconfigured_and_runs_when_ready(monkeypatch):
    monkeypatch.setattr("sys.argv", ["x"])
    with pytest.raises(SystemExit, match="LOGIN_HASH"):
        server.main()
    monkeypatch.setenv("LOGIN_HASH", "h")
    monkeypatch.setenv("ACCESS_ENFORCE", "1")
    with pytest.raises(SystemExit, match="CF_ACCESS"):
        server.main()
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", "t.cloudflareaccess.com")
    monkeypatch.setenv("CF_ACCESS_AUD", "aud")
    monkeypatch.setenv("CONFIRM_ALLOWED_EMAILS", "a@b.c")
    monkeypatch.setenv("SECRET_KEY", "")
    with pytest.raises(SystemExit, match="SECRET_KEY"):
        server.main()
    monkeypatch.setenv("SECRET_KEY", "long-secret-value-long-secret-value")
    seen = {}
    monkeypatch.setattr(server.confirm_app, "start", lambda p: seen.update(confirm=True))
    monkeypatch.setattr(server.mcp, "run", lambda *a, **kw: seen.update(host=kw["host"]))
    server.main()
    assert seen == {"confirm": True, "host": "0.0.0.0"}


def test_main_in_test_mode_binds_to_loopback_and_warns(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["x"])
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    monkeypatch.setenv("LOGIN_PASSPHRASE", "twelve-characters-ok")
    seen = {}
    monkeypatch.setattr(server.confirm_app, "start", lambda p: None)
    monkeypatch.setattr(server.mcp, "run", lambda *a, **kw: seen.update(host=kw["host"]))
    server.main()
    assert seen["host"] == "127.0.0.1" and "WARNING" in capsys.readouterr().err


def test_the_hash_command_prints_only_a_hash(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["x", "hash"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "my passphrase")
    server.main()
    out = capsys.readouterr().out.strip()
    assert out.startswith("pbkdf2:") and "my passphrase" not in out and auth.check_passphrase("my passphrase", out)
