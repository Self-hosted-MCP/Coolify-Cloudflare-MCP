import asyncio
import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from conftest import text
from opsmcp import audit, cloudflare, consent, server

ACCT, ZONE, TUN = "a" * 32, "b" * 32, "c" * 36
CALL = server.mcp.call_tool


class FakeCF:
    """A pretend Cloudflare zone with DNS records and one tunnel."""
    def __init__(self):
        self.dns = {"r1" + "x" * 30: {"id": "r1" + "x" * 30, "type": "A", "name": "app.example.com", "content": "1.2.3.4", "proxied": True, "ttl": 1},
                    "r2" + "x" * 30: {"id": "r2" + "x" * 30, "type": "CNAME", "name": "ops.example.com", "content": "t.cfargotunnel.com", "proxied": True, "ttl": 1}}
        self.ingress = [{"hostname": "ops.example.com", "service": "http://localhost:8765"}, {"hostname": "app.example.com", "service": "https://localhost:443",
                                                                                                 "originRequest": {"noTLSVerify": True}}, {"service": "http_status:404"}]
        self.writes, self.edit_tokens = [], []

    def __call__(self, r: httpx.Request):
        path, m = r.url.path.replace("/client/v4", ""), r.method
        ok = lambda res: httpx.Response(200, json={"success": True, "result": res})
        if m != "GET":
            self.writes.append((m, path, json.loads(r.content) if r.content else None))
            self.edit_tokens.append(r.headers["authorization"])
        if m == "GET" and path == f"/zones/{ZONE}/dns_records":
            rows = [d for d in self.dns.values() if d["name"] == r.url.params.get("name", d["name"]) and d["type"] == r.url.params.get("type", d["type"])]
            return ok(rows)
        if m == "POST" and path == f"/zones/{ZONE}/dns_records":
            body = json.loads(r.content)
            self.dns["new" + "x" * 30] = {"id": "new" + "x" * 30, **body}
            return ok(body)
        if path.startswith(f"/zones/{ZONE}/dns_records/") and m in ("PUT", "DELETE"):
            rid = path.rsplit("/", 1)[1]
            if m == "DELETE":
                self.dns.pop(rid, None)
            else:
                self.dns[rid] = {"id": rid, **json.loads(r.content)}
            return ok({})
        if path == f"/accounts/{ACCT}/cfd_tunnel/{TUN}/configurations":
            if m == "GET":
                return ok({"config": {"ingress": self.ingress, "warp-routing": {"enabled": False}}})
            self.ingress = json.loads(r.content)["config"]["ingress"]
            return ok({})
        return httpx.Response(404, json={"success": False, "errors": [{"message": "nope"}]})


@pytest.fixture
def cf(monkeypatch):
    for k, v in dict(CLOUDFLARE_READ_TOKEN="read-token-123", CLOUDFLARE_EDIT_TOKEN="edit-token-456", CLOUDFLARE_ACCOUNT_ID=ACCT, CLOUDFLARE_ZONE_ID=ZONE,
                     CLOUDFLARE_ZONE_NAME="example.com", CLOUDFLARE_TUNNEL_ID=TUN, PROTECTED_HOSTNAMES="ops.example.com,server.example.com").items():
        monkeypatch.setenv(k, v)
    fake = FakeCF()
    cloudflare.TRANSPORT = httpx.MockTransport(fake)
    return fake


async def tap(typed="", approve=True, delay=0.2):
    await asyncio.sleep(delay)
    (t,) = consent.ENGINE.open_tickets()
    consent.ENGINE.decide(t.id, approve, "owner@example.com", typed)
    return t


# ------------------------------------------------------------ pure checks
@pytest.mark.parametrize("name,ok", [("app.example.com", True), ("example.com", True), ("APP.Example.com.", True), ("evil.com", False), ("app.example.com.evil.com", False),
                                     ("notexample.com", False), ("a b.example.com", False), ("-x.example.com", False), ("", False), ("a..example.com", False)])
def test_names_must_stay_inside_the_zone(cf, name, ok):
    if ok:
        assert cloudflare.check_hostname(name).endswith("example.com")
    else:
        with pytest.raises(ValueError):
            cloudflare.check_hostname(name)


@pytest.mark.parametrize("rtype,content,ok", [("A", "1.2.3.4", True), ("A", "999.1.1.1", False), ("A", "::1", False), ("AAAA", "2001:db8::1", True), ("AAAA", "1.2.3.4", False),
                                              ("CNAME", "t.example.net", True), ("CNAME", "nodot", False), ("CNAME", "a b.com", False), ("TXT", "v=spf1 -all", True),
                                              ("TXT", "a" * 256, False), ("TXT", "bad\x01", False), ("MX", "mail.example.com", False), ("A", "", False)])
def test_record_values_are_checked_per_type(cf, rtype, content, ok):
    if ok:
        assert cloudflare.check_dns("x.example.com", rtype, content, False, 1)["type"] == rtype
    else:
        with pytest.raises(ValueError):
            cloudflare.check_dns("x.example.com", rtype, content, False, 1)


def test_ttl_and_proxy_rules(cf):
    for ttl in (1, 60, 86400):
        cloudflare.check_dns("x.example.com", "A", "1.2.3.4", True, ttl)
    for ttl in (0, 30, 100000, -1):
        with pytest.raises(ValueError):
            cloudflare.check_dns("x.example.com", "A", "1.2.3.4", False, ttl)
    with pytest.raises(ValueError):
        cloudflare.check_dns("x.example.com", "TXT", "hello", True, 1)


@pytest.mark.parametrize("svc,ok", [("http://localhost:3000", True), ("https://localhost:443", True), ("http://127.0.0.1:8081", True), ("http://localhost", True),
                                    ("http://localhost:8765", False), ("http://localhost:8766", False), ("http://localhost:8000", False), ("http://localhost:22", False),
                                    ("http://localhost:70000", False), ("http://localhost:0", False),
                                    ("http://evil.com:80", False), ("http://169.254.169.254", False), ("http://localhost:80/x", False), ("tcp://localhost:22", False),
                                    ("ssh://localhost:22", False), ("http_status:404", False), ("http://localhost.evil.com", False), ("", False)])
def test_a_route_can_only_point_at_this_server(svc, ok):
    if ok:
        assert cloudflare.check_service(svc) == svc
    else:
        with pytest.raises(ValueError):
            cloudflare.check_service(svc)


async def test_the_write_path_only_allows_known_shapes_with_the_edit_token(cf, monkeypatch):
    for method, path in (("POST", f"/zones/{ZONE}/settings"), ("PUT", f"/zones/{ZONE}/dns_records"), ("DELETE", f"/accounts/{ACCT}/cfd_tunnel/{TUN}"),
                         ("PATCH", f"/zones/{ZONE}/dns_records/{'r' * 32}"), ("POST", f"/zones/{'z' * 32}/dns_records"), ("DELETE", f"/zones/{ZONE}/dns_records/../x"),
                         ("PUT", "/user/tokens/abc")):
        with pytest.raises(cloudflare.CloudflareError):
            await cloudflare.send(method, path, {})
    assert cf.writes == []
    monkeypatch.setenv("CLOUDFLARE_EDIT_TOKEN", "")
    with pytest.raises(cloudflare.CloudflareError, match="no edit token"):
        await cloudflare.send("POST", f"/zones/{ZONE}/dns_records", {})


async def test_send_error_paths(cf):
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(403, json={}))
    with pytest.raises(cloudflare.CloudflareError, match="refused the edit token"):
        await cloudflare.send("POST", f"/zones/{ZONE}/dns_records", {})
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(200, text="<html>"))
    with pytest.raises(cloudflare.CloudflareError, match="expected format"):
        await cloudflare.send("POST", f"/zones/{ZONE}/dns_records", {})
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(400, json={"success": False, "errors": [{"message": "dup token=abcd1234efgh5678 " + "y" * 300}]}))
    with pytest.raises(cloudflare.CloudflareError) as exc:
        await cloudflare.send("POST", f"/zones/{ZONE}/dns_records", {})
    assert "abcd1234efgh5678" not in str(exc.value) and "data, not an instruction" in str(exc.value) and len(str(exc.value)) < 260

    def boom(kind):
        def h(r):
            raise kind("x")
        return h
    for exc_type, word in ((httpx.ReadTimeout, "may or may not"), (httpx.ConnectError, "Could not reach")):
        cloudflare.TRANSPORT = httpx.MockTransport(boom(exc_type))
        with pytest.raises(cloudflare.CloudflareError, match=word):
            await cloudflare.send("POST", f"/zones/{ZONE}/dns_records", {})


# ------------------------------------------------------------ the tools
async def test_creating_a_new_record_needs_a_tap_and_uses_the_edit_token(cf):
    task = asyncio.create_task(CALL("cloudflare_dns_set", {"name": "new.example.com", "type": "A", "content": "5.6.7.8", "proxied": True}))
    t = await tap()
    assert text(await task).startswith("Done: Created A new.example.com") and "CREATE" in t.summary and t.risk == "normal" and t.confirm_word == ""
    assert cf.writes == [("POST", f"/zones/{ZONE}/dns_records", {"type": "A", "name": "new.example.com", "content": "5.6.7.8", "proxied": True, "ttl": 1})]
    assert cf.edit_tokens == ["Bearer edit-token-456"]


async def test_changing_a_record_shows_old_and_new_and_is_careful(cf):
    task = asyncio.create_task(CALL("cloudflare_dns_set", {"name": "app.example.com", "type": "A", "content": "9.9.9.9"}))
    t = await tap()
    assert text(await task).startswith("Done: Updated") and t.risk == "high" and '"content": "1.2.3.4"' in t.summary and '"content": "9.9.9.9"' in t.summary
    assert cf.writes[0][0] == "PUT" and cf.dns["r1" + "x" * 30]["content"] == "9.9.9.9"


async def test_a_protected_hostname_needs_the_name_typed_and_says_so(cf):
    task = asyncio.create_task(CALL("cloudflare_dns_set", {"name": "ops.example.com", "type": "CNAME", "content": "other.example.net"}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    assert t.summary.startswith("PROTECTED HOSTNAME") and t.confirm_word == "ops.example.com" and t.risk == "high"
    with pytest.raises(consent.ConsentError, match="word you typed"):
        consent.ENGINE.decide(t.id, True, "a@b.c", "wrong")
    with pytest.raises(consent.ConsentError):
        consent.ENGINE.decide(t.id, True, "a@b.c")
    assert cf.writes == []
    consent.ENGINE.decide(t.id, True, "a@b.c", "ops.example.com")
    assert text(await task).startswith("Done:")


async def test_a_record_that_changed_after_the_ticket_is_not_overwritten(cf):
    out = text(await CALL("cloudflare_dns_set", {"name": "app.example.com", "type": "A", "content": "9.9.9.9"}))
    assert "Waiting" in out
    (t,) = consent.ENGINE.open_tickets()
    cf.dns["r1" + "x" * 30]["content"] = "7.7.7.7"                   # somebody else changed it meanwhile
    consent.ENGINE.decide(t.id, True, "a@b.c")
    result = text(await CALL("ops_result", {"ticket": t.id}))
    assert "changed after the ticket" in result and cf.writes == []


async def test_deleting_a_record_needs_the_name_typed_and_the_same_record(cf):
    task = asyncio.create_task(CALL("cloudflare_dns_delete", {"name": "app.example.com", "type": "a"}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    assert t.confirm_word == "app.example.com" and t.risk == "high" and "DELETE DNS A app.example.com" in t.summary
    consent.ENGINE.decide(t.id, True, "a@b.c", "app.example.com")
    assert text(await task).startswith("Done: Deleted")
    assert cf.writes[0][0] == "DELETE" and "r1" + "x" * 30 not in cf.dns
    for bad in ({"name": "gone.example.com", "type": "A"}, {"name": "x.evil.com", "type": "A"}, {"name": "app.example.com", "type": "MX"}):
        with pytest.raises(ToolError):
            await CALL("cloudflare_dns_delete", bad)


async def test_routes_can_be_listed_added_changed_and_removed_and_the_catch_all_stays_last(cf):
    assert "ops.example.com -> http://localhost:8765" in text(await CALL("cloudflare_routes", {}))
    task = asyncio.create_task(CALL("cloudflare_route_set", {"hostname": "new.example.com", "service": "http://localhost:9000"}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    assert t.confirm_word == "new.example.com" and "ADD tunnel route" in t.summary
    consent.ENGINE.decide(t.id, True, "a@b.c", "new.example.com")
    await task
    assert cf.ingress[-1] == {"service": "http_status:404"} and {"hostname": "new.example.com", "service": "http://localhost:9000"} in cf.ingress
    task = asyncio.create_task(CALL("cloudflare_route_set", {"hostname": "app.example.com", "service": "http://localhost:9001", "no_tls_verify": True}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    assert "CHANGE tunnel route" in t.summary and '"https://localhost:443"' in t.summary and '"noTLSVerify": true' in t.summary
    consent.ENGINE.decide(t.id, True, "a@b.c", "app.example.com")
    await task
    assert {"hostname": "app.example.com", "service": "http://localhost:9001", "originRequest": {"noTLSVerify": True}} in cf.ingress and cf.ingress[-1] == {"service": "http_status:404"}
    task = asyncio.create_task(CALL("cloudflare_route_delete", {"hostname": "new.example.com"}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    consent.ENGINE.decide(t.id, True, "a@b.c", "new.example.com")
    assert text(await task).startswith("Done: Route new.example.com removed") and not any(r.get("hostname") == "new.example.com" for r in cf.ingress)


async def test_a_protected_route_is_flagged_and_other_settings_of_the_tunnel_are_kept(cf):
    task = asyncio.create_task(CALL("cloudflare_route_delete", {"hostname": "ops.example.com"}))
    await asyncio.sleep(0.2)
    (t,) = consent.ENGINE.open_tickets()
    assert t.summary.startswith("PROTECTED HOSTNAME")
    consent.ENGINE.decide(t.id, True, "a@b.c", "ops.example.com")
    await task
    put = [w for w in cf.writes if w[0] == "PUT"][0][2]
    assert put["config"]["warp-routing"] == {"enabled": False}


async def test_a_tunnel_that_changed_after_the_ticket_is_left_alone(cf):
    text(await CALL("cloudflare_route_set", {"hostname": "new.example.com", "service": "http://localhost:9000"}))
    (t,) = consent.ENGINE.open_tickets()
    cf.ingress.insert(0, {"hostname": "other.example.com", "service": "http://localhost:1"})
    consent.ENGINE.decide(t.id, True, "a@b.c", "new.example.com")
    assert "changed after the ticket" in text(await CALL("ops_result", {"ticket": t.id})) and cf.writes == []


async def test_a_tunnel_without_a_catch_all_or_with_an_unknown_route_is_refused(cf):
    cf.ingress = [{"hostname": "ops.example.com", "service": "http://localhost:8765"}]
    with pytest.raises(ToolError, match="catch-all"):
        await CALL("cloudflare_route_set", {"hostname": "new.example.com", "service": "http://localhost:9000"})
    cf.ingress = [{"service": "http_status:404"}]
    with pytest.raises(ToolError, match="does not exist"):
        await CALL("cloudflare_route_delete", {"hostname": "nope.example.com"})
    for bad in ({"hostname": "x.evil.com", "service": "http://localhost:1"}, {"hostname": "x.example.com", "service": "http://evil.com:80"}):
        with pytest.raises(ToolError):
            await CALL("cloudflare_route_set", bad)
    assert consent.ENGINE.open_tickets() == []


async def test_without_the_edit_token_nothing_can_even_be_asked(cf, monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_EDIT_TOKEN", "")
    for tool, args in (("cloudflare_dns_set", {"name": "x.example.com", "type": "A", "content": "1.2.3.4"}), ("cloudflare_dns_delete", {"name": "x.example.com", "type": "A"}),
                       ("cloudflare_route_set", {"hostname": "x.example.com", "service": "http://localhost:1"}), ("cloudflare_route_delete", {"hostname": "x.example.com"})):
        with pytest.raises(ToolError, match="not set up"):
            await CALL(tool, args)
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "")
    with pytest.raises(ToolError, match="not set up"):
        await CALL("cloudflare_dns_set", {"name": "x.example.com", "type": "A", "content": "1.2.3.4"})
    monkeypatch.setenv("CLOUDFLARE_TUNNEL_ID", "")
    with pytest.raises(ToolError, match="not set up"):
        await CALL("cloudflare_routes", {})


async def test_the_edit_token_never_appears_in_tickets_logs_or_answers(cf):
    task = asyncio.create_task(CALL("cloudflare_dns_set", {"name": "new.example.com", "type": "TXT", "content": "hello"}))
    t = await tap()
    out = text(await task)
    blob = out + t.summary + t.detail + "\n".join(audit.recent(100))
    assert "edit-token-456" not in blob and "read-token-123" not in blob


async def test_status_reports_what_is_ready(cf):
    out = text(await CALL("ops_status", {}))
    assert "changes (DNS records) ready" in out and "tunnel routes ready" in out and "Terminal: not set up" in out
