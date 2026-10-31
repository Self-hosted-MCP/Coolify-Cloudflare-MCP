"""The second lock, behind Cloudflare Zero Trust, for the owner's Confirm page.

Zero Trust adds a signed token (the Cf-Access-Jwt-Assertion header) to every request it lets through. This module checks
that token itself AND that it names the owner's own email, so the page refuses anything that did not come through Zero Trust as
the owner, even if a Zero Trust rule is wrong or someone reaches the server another way.

ACCESS_ENFORCE is ON unless it is set to 0 (only for trying it on your own computer). When it is on but not fully configured
(CF_ACCESS_TEAM_DOMAIN, CF_ACCESS_AUD, CONFIRM_ALLOWED_EMAILS), everything is refused: it fails closed."""
import asyncio
import logging

import jwt

from . import config

HEADER = "cf-access-jwt-assertion"
log = logging.getLogger("opsmcp.access")
_client = None


def enforcing() -> bool:
    return config.enforcing()


def team() -> str:
    return config.env("CF_ACCESS_TEAM_DOMAIN").replace("https://", "").strip("/")


def aud() -> str:
    return config.env("CF_ACCESS_AUD")


def configured() -> bool:
    return bool(team() and aud() and config.allowed_emails())


def _keys():
    global _client
    if _client is None:
        _client = jwt.PyJWKClient(f"https://{team()}/cdn-cgi/access/certs", cache_keys=True, lifespan=3600)
    return _client


def verify(token: str, signing_key=None) -> dict | None:
    """The token's claims when it is signed by this team's Zero Trust, made for this application, not expired, and names an
    allowed email. None in every other case. Never raises."""
    try:
        key = signing_key if signing_key is not None else _keys().get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=aud(), issuer=f"https://{team()}",
                            options={"require": ["exp", "iat", "aud", "iss"]}, leeway=30)
    except Exception as exc:
        log.warning("access token refused: %s", type(exc).__name__)
        return None
    email = str(claims.get("email", "")).lower()
    if email not in config.allowed_emails():
        log.warning("access token refused: email not allowed")
        return None
    return claims


async def who(headers) -> dict | None:
    """Claims of the person using the page, or None if refused. With enforcement off (local test only) a fixed test identity."""
    if not enforcing():
        return {"email": "test@localhost", "sub": "test"}
    if not configured():
        return None
    token = headers.get(HEADER, "")
    if not token:
        return None
    return await asyncio.to_thread(verify, token)
