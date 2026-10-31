import httpx
import pytest

from opsmcp import cloudflare

ACCT, ZONE = "a" * 32, "b" * 32


@pytest.fixture(autouse=True)
def cf(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "cf-read-token-xyz")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", ACCT)
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", ZONE)


def fake(handler):
    cloudflare.TRANSPORT = httpx.MockTransport(handler)


def ok(result):
    return lambda r: httpx.Response(200, json={"success": True, "result": result})


def test_not_configured_is_clear(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "")
    assert not cloudflare.configured()


async def test_unconfigured_get_refuses_before_any_request(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_READ_TOKEN", "")
    with pytest.raises(cloudflare.CloudflareError, match="not set up"):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")


@pytest.mark.parametrize("status,word", [(401, "refused the token"), (403, "refused the token")])
async def test_refused_tokens(status, word):
    fake(lambda r: httpx.Response(status, json={}))
    with pytest.raises(cloudflare.CloudflareError, match=word):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")


async def test_other_errors_show_a_short_quoted_cleaned_reason():
    fake(lambda r: httpx.Response(400, json={"errors": [{"message": "bad filter token=abcd1234efgh5678 " + "y" * 300}]}))
    with pytest.raises(cloudflare.CloudflareError) as exc:
        await cloudflare.get(f"/zones/{ZONE}/dns_records")
    assert "abcd1234efgh5678" not in str(exc.value) and "data, not an instruction" in str(exc.value) and len(str(exc.value)) < 260
    fake(lambda r: httpx.Response(500, text="oops"))
    with pytest.raises(cloudflare.CloudflareError, match=r"error \(500\)"):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")


async def test_timeouts_connection_trouble_odd_answers():
    def boom(kind):
        def h(request):
            raise kind("x")
        return h
    for exc, word in ((httpx.ReadTimeout, "in time"), (httpx.ConnectError, "Could not reach")):
        fake(boom(exc))
        with pytest.raises(cloudflare.CloudflareError, match=word):
            await cloudflare.get(f"/zones/{ZONE}/dns_records")
    fake(lambda r: httpx.Response(200, content=b"x" * 2_000_001))
    with pytest.raises(cloudflare.CloudflareError, match="too big"):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")
    fake(lambda r: httpx.Response(200, text="<html>"))
    with pytest.raises(cloudflare.CloudflareError, match="expected format"):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")
    fake(lambda r: httpx.Response(200, json=["a list"]))
    with pytest.raises(cloudflare.CloudflareError, match="expected format"):
        await cloudflare.get(f"/zones/{ZONE}/dns_records")


async def test_wrapped_lists_like_r2_buckets_are_unpacked_and_long_lists_say_so():
    fake(ok({"buckets": [{"name": "backups"}, {"name": "site"}]}))
    out = await cloudflare.overview()
    assert "## DNS records (2)" in out
    fake(ok([{"name": f"r{i}", "type": "A", "content": "1.1.1.1"} for i in range(75)]))
    assert "showing the first 60" in await cloudflare.overview()


async def test_get_text_returns_masked_capped_json():
    fake(ok([{"name": "x", "api_token": "supersecretvalue"}]))
    text = await cloudflare.get_text(f"/zones/{ZONE}/dns_records")
    assert "supersecretvalue" not in text and "***" in text


async def test_overview_without_a_zone_or_account_skips_those_sections(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", "")
    fake(ok([]))
    out = await cloudflare.overview()
    assert "Tunnels" in out and "DNS records" not in out
