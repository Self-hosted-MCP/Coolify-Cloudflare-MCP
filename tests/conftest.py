import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

COOLIFY_TOKEN = "7|AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdef"
APP = "abcd1234efgh5678ijkl9012"


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    for k in ("LOGIN_HASH", "LOGIN_PASSPHRASE", "SECRET_KEY", "READ_ONLY", "CF_ACCESS_TEAM_DOMAIN", "CF_ACCESS_AUD",
              "CONFIRM_ALLOWED_EMAILS", "CLOUDFLARE_READ_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_ZONE_ID"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ACCESS_ENFORCE", "0")
    monkeypatch.setenv("COOLIFY_API_URL", "https://coolify.test")
    monkeypatch.setenv("COOLIFY_TOKEN", COOLIFY_TOKEN)
    monkeypatch.setenv("CONFIRM_WAIT_SECONDS", "2")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-test-secret-key")
    from opsmcp import consent
    consent.ENGINE = consent.Engine()
    consent._frozen_now = False
    consent._until = 0.0
    consent._allow_all_until = 0.0
    yield
    from opsmcp import coolify, cloudflare
    coolify.TRANSPORT = None
    cloudflare.TRANSPORT = None


class Fake:
    """A pretend Coolify. routes: {("GET", "/api/v1/resources"): (200, json) or a function(request) -> Response}."""
    def __init__(self, routes):
        self.routes, self.seen = routes, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        hit = self.routes.get((request.method, request.url.path))
        if hit is None:
            return httpx.Response(404, json={"message": "nope"})
        if callable(hit):
            return hit(request)
        status, body = hit
        return httpx.Response(status, json=body)

    def calls(self, method, path):
        return [r for r in self.seen if r.method == method and r.url.path == path]


def install(routes) -> Fake:
    from opsmcp import coolify
    fake = Fake(routes)
    coolify.TRANSPORT = httpx.MockTransport(fake)
    return fake


def text(result) -> str:
    return "".join(c.text for c in result.content)
