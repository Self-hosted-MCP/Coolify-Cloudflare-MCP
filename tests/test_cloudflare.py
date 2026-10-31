import httpx
import pytest

from opsmcp import cloudflare

ACCT, ZONE = "a" * 32, "b" * 32


@pytest.fixture(autouse=True)
def cf(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "cf-read-token-xyz")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", ACCT)
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", ZONE)


@pytest.mark.parametrize("path", [
    "/user/tokens", f"/accounts/{'c' * 32}/members", f"/accounts/{ACCT}/cfd_tunnel/{'t' * 16}/token", f"/accounts/{ACCT}/workers/scripts",
    f"/accounts/{ACCT}/storage/kv/namespaces/{'k' * 16}/values/x", f"/zones/{ZONE}/dns_records/export", f"/zones/{ZONE}/dns_records\n", f"/zones/{ZONE}/../../user", f"/zones/{ZONE}//dns_records", f"/zones/{ZONE}/./x",
    f"/zones/{ZONE}/dns_records?x=1", f"/zones/{ZONE}/dns_records#x", "https://evil.test/x", "/zones/short/dns_records", "", None])
def test_paths_outside_our_account_and_zone_are_refused(path):
    with pytest.raises(cloudflare.CloudflareError):
        cloudflare.check_path(path)


def test_our_own_paths_are_allowed():
    for p in (f"/zones/{ZONE}/dns_records", f"/accounts/{ACCT}/cfd_tunnel", f"/accounts/{ACCT}/access/apps", f"/zones/{ZONE}/settings/ssl",
              f"/accounts/{ACCT}/cfd_tunnel/{'t' * 16}", f"/accounts/{ACCT}/audit_logs", f"/accounts/{ACCT}/r2/buckets"):
        assert cloudflare.check_path(p) == p


async def test_get_sends_only_a_get_with_the_read_token_and_does_not_follow_redirects():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"success": True, "result": [{"name": "x", "type": "A", "content": "1.2.3.4"}]})
    cloudflare.TRANSPORT = httpx.MockTransport(handler)
    out = await cloudflare.get(f"/zones/{ZONE}/dns_records", {"per_page": "5"})
    assert out["success"] and seen[0].method == "GET" and seen[0].headers["authorization"] == "Bearer cf-read-token-xyz"
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(302, headers={"location": "https://evil.test"}))
    with pytest.raises(cloudflare.CloudflareError):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")


async def test_overview_survives_one_failing_section():
    def handler(request):
        if request.url.path.endswith("rulesets"):
            return httpx.Response(403, json={})
        return httpx.Response(200, json={"success": True, "result": [{"name": "n", "type": "A", "content": "c", "proxied": True, "status": "healthy"}]})
    cloudflare.TRANSPORT = httpx.MockTransport(handler)
    out = await cloudflare.overview()
    assert "DNS records" in out and "could not read" in out


async def test_cloudflare_error_text_is_short_and_redacted():
    cloudflare.TRANSPORT = httpx.MockTransport(lambda r: httpx.Response(200, json={"success": False, "errors": [{"message": "bad token=abcd1234secretvalue"}]}))
    with pytest.raises(cloudflare.CloudflareError) as exc:
        await cloudflare.get(f"/zones/{ZONE}/dns_records")
    assert "abcd1234secretvalue" not in str(exc.value)
