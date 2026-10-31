"""Settings come from environment variables only, read when they are used (so tests can change them).
Secrets (LOGIN_HASH, SECRET_KEY, COOLIFY_TOKEN, the Cloudflare tokens) live in Coolify, never in files."""
import os
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_int(name: str, default: int) -> int:
    try:
        return int(env(name) or default)
    except ValueError:
        return default


def env_list(name: str, default: str = "") -> list[str]:
    return [x.strip().lower() for x in (env(name) or default).split(",") if x.strip()]


OFF_WORDS = ("0", "false", "no", "off")


def flag(name: str, default: str = "0") -> bool:
    return env(name, default).lower() in ("1", "true", "on", "yes")


def safe_flag(name: str, default_on: bool) -> bool:
    """For switches where the SAFE answer is "on" (Zero Trust, read-only): a typo never turns them off.
    Empty means the default. Only an exact 0, false, no or off switches it off; anything else switches it on."""
    value = env(name).lower()
    if not value:
        return default_on
    return value not in OFF_WORDS


def data_dir() -> Path:
    return Path(env("DATA_DIR", "/data")).expanduser()


def public_url() -> str:           # Claude's door, for example https://ops.example.com
    return env("PUBLIC_URL", "http://localhost:8765").rstrip("/")


def confirm_url() -> str:          # the owner's Confirm page, behind Zero Trust
    return env("CONFIRM_URL", "http://localhost:8766").rstrip("/")


def redirect_hosts() -> list[str]:
    return env_list("ALLOWED_REDIRECT_HOSTS", "claude.ai,claude.com")


def coolify_url() -> str:          # like https://coolify.example.com (no /api/v1, no trailing slash)
    return env("COOLIFY_API_URL").rstrip("/")


def coolify_token() -> str:
    return env("COOLIFY_TOKEN")


def cf_account() -> str:
    return env("CLOUDFLARE_ACCOUNT_ID")


def cf_zone() -> str:
    return env("CLOUDFLARE_ZONE_ID")


def cf_read_token() -> str:
    return env("CLOUDFLARE_READ_TOKEN")


def cf_edit_token() -> str:        # used ONLY after the owner's tap, for DNS records and tunnel routes
    return env("CLOUDFLARE_EDIT_TOKEN")


def cf_zone_name() -> str:         # like example.com: every change must stay inside it
    return env("CLOUDFLARE_ZONE_NAME").lower().strip(".")


def cf_tunnel_id() -> str:         # the one tunnel whose routes can be changed
    return env("CLOUDFLARE_TUNNEL_ID")


def _host_of(url: str) -> str:
    from urllib.parse import urlparse
    return (urlparse(url).hostname or "").lower().strip(".")


def protected_hostnames() -> list[str]:
    """Hosts a change could cut the owner off from: the ones they list, plus (always) this server's own doors, Coolify, SSH and the zone itself."""
    listed = [h.strip(".") for h in env_list("PROTECTED_HOSTNAMES")]
    own = [_host_of(public_url()), _host_of(confirm_url()), _host_of(coolify_url()), ssh_host().lower().strip("."), cf_zone_name()]
    return sorted({h for h in listed + own if h and h not in ("localhost", "127.0.0.1")})


def route_hard_blocked_ports() -> set[int]:
    """Never published by a route, whatever else is set: SSH, Docker's own API, Coolify's own ports and this server's two doors."""
    return {22, 2375, 2376, 6001, 6002, 8000, port(), admin_port()}


def route_blocked_ports() -> set[int]:
    """Also blocked unless the owner lists them in ROUTE_ALLOWED_PORTS: the usual proxy dashboard port and anything they add."""
    extra = {int(x) for x in env_list("ROUTE_BLOCKED_PORTS") if x.isdigit()}
    return route_hard_blocked_ports() | {8080} | extra


def route_allowed_ports() -> set[int]:
    """Strict mode: when ROUTE_ALLOWED_PORTS is set, a route may ONLY point at these ports (and never at a hard-blocked one)."""
    return {int(x) for x in env_list("ROUTE_ALLOWED_PORTS") if x.isdigit()}


def read_only() -> bool:           # no change can even be asked for. A typo means ON.
    return safe_flag("READ_ONLY", False)


def enforcing() -> bool:           # Zero Trust on the Confirm page. A typo means ON.
    return safe_flag("ACCESS_ENFORCE", True)


def confirm_wait() -> int:         # how long a change tool waits for the tap before it hands back a ticket
    return env_int("CONFIRM_WAIT_SECONDS", 45)


def unfreeze_minutes() -> int:     # after an Unfreeze, changes freeze again by themselves after this long. 0 = never
    return max(0, env_int("UNFREEZE_MINUTES", 60))


def allow_all_minutes() -> int:    # the "Allow all" button on a ticket lets every change through without a tap for this long. 0 = no button
    return max(0, env_int("ALLOW_ALL_MINUTES", 10))


def confirm_ttl() -> int:          # how long a ticket stays open
    return env_int("CONFIRM_TTL_SECONDS", 300)


def output_max_chars() -> int:
    return env_int("OUTPUT_MAX_CHARS", 8000)


def max_log_lines() -> int:
    return env_int("MAX_LOG_LINES", 200)


def rate_limit_per_minute() -> int:
    return env_int("RATE_LIMIT_PER_MINUTE", 30)


def http_timeout() -> float:
    return env_int("HTTP_TIMEOUT_SECONDS", 20)


def action_log_max_mb() -> int:
    return env_int("ACTION_LOG_MAX_MB", 2)


def host() -> str:
    return env("HOST", "0.0.0.0")


def port() -> int:
    return env_int("PORT", 8765)


def admin_port() -> int:
    return env_int("ADMIN_PORT", 8766)


def allowed_emails() -> list[str]:     # the only Zero Trust identities that may use the Confirm page
    return env_list("CONFIRM_ALLOWED_EMAILS")


# ---- the terminal (SSH to the server, its own user and key)
def ssh_host() -> str:
    return env("SSH_HOST")


def ssh_port() -> int:
    return env_int("SSH_PORT", 22)


def ssh_user() -> str:
    return env("SSH_USER")


def ssh_key() -> str:              # the private key text; "\\n" written as two characters is turned into a new line
    return env("SSH_PRIVATE_KEY").replace("\\n", "\n")


def ssh_known_hosts() -> str:      # the server's own public key line, so a look-alike machine is refused
    return env("SSH_KNOWN_HOSTS").replace("\\n", "\n")
