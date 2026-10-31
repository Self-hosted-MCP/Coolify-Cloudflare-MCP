"""Single-user OAuth: the AI app registers, the owner types their passphrase once, the app gets tokens.
Same design as the Shared Browser MCP: one scope."""
import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.auth.provider import (
    AccessToken, AuthorizationCode, AuthorizationParams, AuthorizeError, RefreshToken, RegistrationError,
    TokenError, construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from . import config

SCOPE = "ops"


def oauth_file() -> Path:
    return config.data_dir() / "oauth.json"


def private_write(path: Path, text: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def hash_passphrase(passphrase: str, salt: bytes | None = None, rounds: int = 600_000) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, rounds)
    return f"pbkdf2:{rounds}:{salt.hex()}:{digest.hex()}"


def check_passphrase(passphrase: str, stored: str) -> bool:
    try:
        stored = stored.replace("$", ":")
        _, rounds, salt, _digest = stored.split(":")
        return hmac.compare_digest(hash_passphrase(passphrase, bytes.fromhex(salt), int(rounds)), stored)
    except Exception:
        return False


def passphrase_ok(passphrase: str) -> bool:
    """LOGIN_HASH wins. LOGIN_PASSPHRASE (plain) is only for testing on your own computer, and only with ACCESS_ENFORCE=0."""
    if config.env("LOGIN_HASH"):
        return check_passphrase(passphrase, config.env("LOGIN_HASH"))
    plain = config.env("LOGIN_PASSPHRASE")
    if config.enforcing():
        return False
    return bool(plain) and hmac.compare_digest(passphrase.encode(), plain.encode())


def token_key(token: str) -> str:
    """oauth.json keeps only a fingerprint of each token, so a copy of the file can't be used to log in."""
    return hashlib.sha256(token.encode()).hexdigest()


class PassphraseOAuth:
    ACCESS_TTL = 3600
    REFRESH_TTL = 30 * 24 * 3600
    MAX_CLIENTS = 50
    MAX_PENDING = 100

    def __init__(self, public_url: str, redirect_hosts: list[str]):
        self.public_url = public_url.rstrip("/")
        self.redirect_hosts = [h.lower() for h in redirect_hosts]
        self.lock = threading.Lock()
        self.pending: dict[str, tuple[float, str, AuthorizationParams]] = {}
        self.codes: dict[str, AuthorizationCode] = {}
        self.failures: list[float] = []
        self.by_source: dict[str, list[float]] = {}   # wrong passphrases per source address
        self.attempts: dict[str, int] = {}   # wrong passphrases per login link
        self.pairing_until = 0.0             # a NEW app can only connect while the owner has opened this window
        data = json.loads(oauth_file().read_text()) if oauth_file().exists() else {}
        self.clients = {k: OAuthClientInformationFull.model_validate(v) for k, v in data.get("clients", {}).items()}
        self.access = {k: AccessToken.model_validate(v) for k, v in data.get("access", {}).items()}
        self.refresh = {k: RefreshToken.model_validate(v) for k, v in data.get("refresh", {}).items()}
        self.approved: set[str] = set(data.get("approved", []))   # apps that finished a passphrase login

    def save(self) -> None:
        now = time.time()
        self.access = {k: v for k, v in self.access.items() if not v.expires_at or v.expires_at > now}
        self.refresh = {k: v for k, v in self.refresh.items() if not v.expires_at or v.expires_at > now}
        private_write(oauth_file(), json.dumps({
            "clients": {k: v.model_dump(mode="json") for k, v in self.clients.items()},
            "access": {k: v.model_dump(mode="json") for k, v in self.access.items()},
            "refresh": {k: v.model_dump(mode="json") for k, v in self.refresh.items()},
            "approved": sorted(self.approved),
        }, indent=1))

    def redirect_ok(self, uri) -> bool:
        text = str(uri)
        p = urlparse(text)
        if "\\" in text or p.username is not None or p.password is not None:   # no user-info or backslash tricks, whatever the host says
            return False
        host = (p.hostname or "").lower()
        if host in ("localhost", "127.0.0.1", "::1"):
            return p.scheme in ("http", "https")
        return p.scheme == "https" and host in self.redirect_hosts      # exact hosts only: a sub-domain is not trusted

    async def get_client(self, client_id: str):
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        bad = [str(u) for u in (client_info.redirect_uris or []) if not self.redirect_ok(u)]
        if bad:
            raise RegistrationError("invalid_redirect_uri", f"Redirect not allowed: {', '.join(bad)}")
        client_info.client_id_issued_at = client_info.client_id_issued_at or int(time.time())   # without a time it would look ancient and be dropped
        with self.lock:
            cutoff = time.time() - 3600
            for cid in [c for c, v in self.clients.items()
                        if (v.client_id_issued_at or 0) < cutoff and not self.logged_in(c)]:
                del self.clients[cid]
            while len(self.clients) >= self.MAX_CLIENTS:
                waiting = [c for c in self.clients if not self.logged_in(c)]
                if not waiting:   # never push out an app that is logged in
                    raise RegistrationError("invalid_client_metadata", "Too many apps are registered. Try again later.")
                del self.clients[min(waiting, key=lambda k: self.clients[k].client_id_issued_at or 0)]
            self.clients[client_info.client_id] = client_info
            self.save()

    def logged_in(self, client_id: str) -> bool:
        return client_id in self.approved or any(
            t.client_id == client_id for t in [*self.access.values(), *self.refresh.values()])

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        if not self.redirect_ok(params.redirect_uri):
            raise AuthorizeError("invalid_request", "Redirect not allowed")
        req = secrets.token_urlsafe(24)
        with self.lock:
            self.pending = {k: v for k, v in self.pending.items() if v[0] > time.time()}
            self.codes = {k: v for k, v in self.codes.items() if v.expires_at > time.time()}
            self.attempts = {k: v for k, v in self.attempts.items() if k in self.pending}
            if len(self.pending) >= self.MAX_PENDING:
                raise AuthorizeError("temporarily_unavailable", "Too many logins are open. Try again in a few minutes.")
            self.pending[req] = (time.time() + 600, client.client_id, params)
        return f"{self.public_url}/login?req={req}"

    def describe(self, req: str) -> tuple[str, str] | None:
        entry = self.pending.get(req)
        if not entry or entry[0] < time.time():
            return None
        client = self.clients.get(entry[1])
        return (client.client_name if client else None) or "An AI app", urlparse(str(entry[2].redirect_uri)).hostname or "?"

    def locked_out(self, source: str = "") -> bool:
        cutoff = time.time() - 900
        self.failures = [t for t in self.failures if t > cutoff]
        self.by_source = {k: [t for t in v if t > cutoff] for k, v in self.by_source.items()}
        self.by_source = {k: v for k, v in self.by_source.items() if v}
        if source and len(self.by_source.get(source, [])) >= 10:   # one address cannot lock the owner out
            return True
        return len(self.failures) >= 60   # many wrong tries overall; one link only gets 5, one address 10 (see complete_login)

    def pairing_open(self) -> bool:
        return time.time() < self.pairing_until

    def open_pairing(self, minutes: int = 5) -> float:
        self.pairing_until = time.time() + max(1, min(minutes, 15)) * 60
        return self.pairing_until

    def complete_login(self, req: str, passphrase: str, source: str = "") -> str | None:
        """Redirect URL on success, None on a wrong passphrase."""
        with self.lock:
            if self.locked_out(source):
                raise PermissionError("Too many wrong tries. Wait 15 minutes.")
            entry = self.pending.get(req)
            if not entry or entry[0] < time.time():
                raise LookupError("This login link expired. Start the connection again in your AI app.")
            _, client_id, params = entry
            if client_id not in self.approved and not self.pairing_open():
                # A new app cannot connect, even with the right passphrase, unless the owner opened the window on their page.
                # This stops a stranger's Claude from asking the owner to type his passphrase for their connection.
                raise PermissionError("A new app can only connect while pairing is open. On your Confirm page press "
                                      "Allow a new app, then log in again from your AI app.")
            if not passphrase_ok(passphrase):
                self.failures.append(time.time())
                if source:
                    self.by_source.setdefault(source, []).append(time.time())
                self.attempts[req] = self.attempts.get(req, 0) + 1
                if self.attempts[req] >= 5:   # this link is burnt
                    self.pending.pop(req, None); self.attempts.pop(req, None)
                return None
            del self.pending[req]
            self.attempts.pop(req, None)
            self.approved.add(client_id)
            self.save()
            code = secrets.token_urlsafe(32)
            self.codes[code] = AuthorizationCode(
                code=code, scopes=params.scopes or [SCOPE], expires_at=time.time() + 300, client_id=client_id,
                code_challenge=params.code_challenge, redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=params.resource, subject="owner")
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    async def load_authorization_code(self, client, authorization_code: str):
        code = self.codes.get(authorization_code)
        if code and code.client_id == client.client_id and code.expires_at > time.time():
            return code
        return None

    def issue(self, client_id: str, scopes: list[str], resource: str | None) -> OAuthToken:
        now = int(time.time())
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        a_key, r_key = token_key(access), token_key(refresh)
        self.access[a_key] = AccessToken(token=a_key, client_id=client_id, scopes=scopes,
                                         expires_at=now + self.ACCESS_TTL, resource=resource, subject="owner")
        self.refresh[r_key] = RefreshToken(token=r_key, client_id=client_id, scopes=scopes,
                                           expires_at=now + self.REFRESH_TTL, resource=resource, subject="owner")
        self.save()
        return OAuthToken(access_token=access, token_type="Bearer", expires_in=self.ACCESS_TTL,
                          refresh_token=refresh, scope=" ".join(scopes))

    async def exchange_authorization_code(self, client, authorization_code: AuthorizationCode) -> OAuthToken:
        with self.lock:
            if self.codes.pop(authorization_code.code, None) is None:
                raise TokenError("invalid_grant", "Code already used")
            return self.issue(client.client_id, authorization_code.scopes, authorization_code.resource)

    async def load_refresh_token(self, client, refresh_token: str):
        tok = self.refresh.get(token_key(refresh_token))
        if tok and tok.client_id == client.client_id and (not tok.expires_at or tok.expires_at > time.time()):
            return tok.model_copy(update={"token": refresh_token})
        return None

    async def exchange_refresh_token(self, client, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        with self.lock:
            if self.refresh.pop(token_key(refresh_token.token), None) is None:
                raise TokenError("invalid_grant", "Refresh token already used")
            return self.issue(client.client_id, scopes or refresh_token.scopes, refresh_token.resource)

    async def load_access_token(self, token: str):
        tok = self.access.get(token_key(token))
        if tok and (not tok.expires_at or tok.expires_at > time.time()) and self.for_us(tok.resource):
            return tok.model_copy(update={"token": token})
        return None

    def for_us(self, resource) -> bool:
        if not resource:
            return True
        r = str(resource).rstrip("/").lower()
        return r in (self.public_url.lower(), f"{self.public_url.lower()}/mcp")

    async def revoke_token(self, token) -> None:
        self.disconnect(token.client_id)

    def apps(self) -> list[dict]:
        """The AI apps that finished a passphrase login, for the Connected apps list on the owner's Confirm page."""
        out = []
        with self.lock:
            approved, clients = sorted(self.approved), dict(self.clients)
            all_tokens = [*self.access.values(), *self.refresh.values()]
        for cid in approved:
            c = clients.get(cid)
            tokens = [t for t in all_tokens if t.client_id == cid]
            out.append({"id": cid, "name": (c.client_name if c else None) or "An AI app",
                        "since": int(c.client_id_issued_at or 0) if c else 0,
                        "signed_in": bool(tokens)})
        return out

    def disconnect(self, client_id: str, forget: bool = False) -> None:
        with self.lock:
            self.access = {k: v for k, v in self.access.items() if v.client_id != client_id}
            self.refresh = {k: v for k, v in self.refresh.items() if v.client_id != client_id}
            if forget:
                self.clients.pop(client_id, None)
                self.approved.discard(client_id)
            self.save()


LOGIN_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ops login</title><style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#161616;--mut:#666;--line:#d9d9d9;--acc:#161616;--err:#b00020}}
@media(prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#f2f2f2;--mut:#9a9a9a;--line:#333;--acc:#f2f2f2;--err:#ff6b81}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;display:grid;min-height:100vh;place-items:center;padding:16px}}
main{{width:100%;max-width:380px}}h1{{font-size:1.3rem;margin:0 0 .25rem}}p{{color:var(--mut);margin:.25rem 0 1rem}}
input{{width:100%;box-sizing:border-box;padding:.7rem;font:inherit;border:1px solid var(--line);border-radius:8px;background:transparent;color:inherit}}
button{{margin-top:.75rem;width:100%;padding:.7rem;font:inherit;border:0;border-radius:8px;background:var(--acc);color:var(--bg);cursor:pointer}}
.err{{color:var(--err)}}</style></head><body><main>{body}</main></body></html>"""


def login_page(provider: PassphraseOAuth, req: str, error: str = "") -> str:
    from html import escape
    info = provider.describe(req)
    if not info:
        body = f"<h1>Coolify-Cloudflare MCP</h1><p class='err'>{escape(error or 'This login link expired. Start the connection again in your AI app.')}</p>"
    else:
        name, host = info
        body = (f"<h1>Coolify-Cloudflare MCP</h1><p>{escape(name)} wants to connect. It goes back to {escape(host)} after login.</p>"
                + (f"<p class='err'>{escape(error)}</p>" if error else "")
                + f"<form method='post' action='/login'><input type='hidden' name='req' value='{escape(req)}'>"
                  "<input type='password' name='passphrase' placeholder='Passphrase' autocomplete='current-password' autofocus required>"
                  "<button>Log in</button></form>")
    return LOGIN_HTML.format(body=body)
