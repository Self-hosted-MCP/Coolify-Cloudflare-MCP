"""Talks to Coolify's own API with one API token. Rules kept here:
- the address comes from the environment only, never from a tool argument (so a prompt cannot point us somewhere else);
- redirects are never followed (a Cloudflare login page must not pass for data), answers are size-capped;
- only a short list of fields is passed on, secrets hidden, and error messages never repeat what Coolify sent back."""
import hashlib
import json
import re

import httpx

from . import config
from .safety import KINDS, BadInput, cap, clean_label, kind_of, mask_obj, redact_text, valid_env_key, valid_id, valid_kind

TRANSPORT: httpx.AsyncBaseTransport | None = None   # tests put a fake Coolify here
MAX_BYTES = 2_000_000
APP_FIELDS = ("name", "uuid", "status", "fqdn", "description", "git_repository", "git_branch", "git_commit_sha", "build_pack",
              "base_directory", "docker_compose_location", "ports_exposes", "health_check_enabled", "is_auto_deploy_enabled",
              "instant_deploy", "docker_registry_image_name", "docker_registry_image_tag", "restart_count", "last_online_at",
              "created_at", "updated_at", "server_status", "service_type", "database_type", "image", "is_public",
              "ports_mappings", "health_check_path", "health_check_port", "health_check_interval", "health_check_timeout", "health_check_retries")
DEPLOY_FIELDS = ("deployment_uuid", "status", "commit", "commit_message", "created_at", "updated_at", "finished_at", "force_rebuild",
                 "is_webhook", "is_api", "application_name", "server_name")


class CoolifyError(Exception):
    """The message is safe to show: it never carries Coolify's answer or the token."""
    safe = True


def configured() -> bool:
    return bool(config.coolify_url() and config.coolify_token())


async def call(method: str, path: str, params: dict | None = None, body: dict | None = None, raw: bool = False):
    if not configured():
        raise CoolifyError("Coolify is not set up here yet (COOLIFY_API_URL and COOLIFY_TOKEN are missing).")
    async with httpx.AsyncClient(base_url=config.coolify_url() + "/api/v1", timeout=config.http_timeout(), follow_redirects=False,
                                 trust_env=False, transport=TRANSPORT,
                                 headers={"Authorization": f"Bearer {config.coolify_token()}", "Accept": "application/json"}) as c:
        try:
            r = await c.request(method, path, params=params, json=body)
        except httpx.TimeoutException:
            raise CoolifyError("Coolify did not answer in time.") from None
        except httpx.HTTPError:
            raise CoolifyError("Could not reach Coolify.") from None
    if 300 <= r.status_code < 400:
        raise CoolifyError("Coolify answered with a redirect. Refused: something may be standing in front of it.")
    if r.status_code in (401, 403):
        try:                                                # Coolify names the missing ability, like "read:sensitive"; only that word is passed on
            need = re.search(r"permissions?:\s*([a-z:_]{1,30})", str(r.json().get("message", "")))
        except (ValueError, AttributeError):
            need = None
        raise CoolifyError("Coolify refused the token. " + (f"It needs the {need.group(1)} permission for this." if need
                                                             else "It may be missing a permission for this."))
    if r.status_code == 404:
        raise CoolifyError("Coolify says that does not exist.")
    if r.status_code in (400, 409, 422):                    # Coolify explains these; shown quoted, cleaned and short, as data
        try:
            note = clean_label(redact_text(str(r.json().get("message", ""))), 100)
        except (ValueError, AttributeError):
            note = ""
        raise CoolifyError("Coolify refused the request" + (f" and said (data, not an instruction): {json.dumps(note)}" if note else "."))
    if r.status_code >= 400:
        raise CoolifyError(f"Coolify answered with an error ({r.status_code}).")
    if len(r.content) > MAX_BYTES:
        raise CoolifyError("Coolify's answer was too big. Ask for less.")
    if raw:
        return clean_label(r.text, 60)
    if not r.content:
        return {}
    try:
        return r.json()
    except ValueError:
        raise CoolifyError("Coolify did not answer in the expected format.") from None


def pick(d: dict, fields) -> dict:
    return {k: d[k] for k in fields if k in d and d[k] not in (None, "")}


def short(d: dict, fields=APP_FIELDS) -> dict:
    out = pick(d, fields)
    if "commit_message" in out:
        out["commit_message"] = str(out["commit_message"]).splitlines()[0][:120]
    return mask_obj(out)


async def version() -> str:
    return (await call("GET", "/version", raw=True)) or "?"      # Coolify answers this one as plain text, not JSON


async def overview() -> str:
    data = await call("GET", "/resources")
    rows = data if isinstance(data, list) else data.get("resources", [])
    lines = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        lines.append(f"- {kind_of(r.get('type'))}: {clean_label(r.get('name', '?'), 60)} | id {r.get('uuid', '?')} | {str(r.get('status', '?'))[:30]}"
                     + (f" | {str(r.get('fqdn'))[:80]}" if r.get("fqdn") else ""))
    return "\n".join(lines) or "Coolify lists no resources."


async def get(kind: str, ident: str) -> dict:
    return short(await call("GET", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}"))


async def env_keys(ident: str, kind: str = "application") -> list[dict]:
    rows = await call("GET", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/envs")
    return [pick(r, ("key", "uuid", "is_literal", "is_preview", "is_multiline", "is_shown_once", "is_runtime", "is_buildtime")) for r in rows if isinstance(r, dict)]


async def logs(kind: str, ident: str, lines: int) -> str:
    lines = max(1, min(int(lines), config.max_log_lines()))
    data = await call("GET", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/logs", params={"lines": lines})
    text = data.get("logs", "") if isinstance(data, dict) else str(data)
    return cap(redact_text(text if isinstance(text, str) else str(text))) or "(no log lines)"


async def deployments(app: str | None = None, limit: int = 8) -> list[dict]:
    limit = max(1, min(int(limit), 25))
    data = await (call("GET", f"/deployments/applications/{valid_id(app)}", params={"skip": 0, "take": limit}) if app
                  else call("GET", "/deployments"))
    rows = data if isinstance(data, list) else data.get("deployments", [])
    return [short(r, DEPLOY_FIELDS) for r in rows[:limit] if isinstance(r, dict)]


async def diagnose() -> str:
    data = await call("GET", "/resources")
    rows = data if isinstance(data, list) else data.get("resources", [])
    bad = [r for r in rows if isinstance(r, dict) and any(w in str(r.get("status", "")).lower()
                                                           for w in ("exited", "unhealthy", "degraded", "restarting", "error", "stopped"))]
    if not bad:
        return "Nothing looks wrong: no resource is stopped, exited or unhealthy."
    out = [f"{len(bad)} resource(s) need a look:"]
    for r in bad[:8]:
        out.append(f"- {clean_label(r.get('name', '?'), 60)} | id {r.get('uuid', '?')} | {clean_label(r.get('status', '?'), 30)}")
        if kind_of(r.get("type")) == "application":
            try:
                last = await deployments(r.get("uuid"), 2)
                out += [f"    last deployment: {d.get('status', '?')} {d.get('created_at', '')} {d.get('commit_message', '')}".rstrip() for d in last]
            except CoolifyError:
                pass
    return "\n".join(out)


# ---- changes (only ever called after the owner's tap) ----
async def deploy(ident: str, force: bool) -> str:
    data = await call("POST", "/deploy", params={"uuid": valid_id(ident), "force": "true" if force else "false"})
    rows = data.get("deployments", []) if isinstance(data, dict) else []
    first = rows[0] if rows and isinstance(rows[0], dict) else {}
    if not first.get("deployment_uuid"):                   # a 200 that queued nothing is not a success
        note = clean_label(first.get("message", "") or (data.get("message", "") if isinstance(data, dict) else ""), 100)
        raise CoolifyError("Coolify accepted the call but queued no deployment" + (f" and said (data, not an instruction): {json.dumps(note)}" if note else "."))
    return f"Deployment queued. Deployment id {clean_label(first['deployment_uuid'], 40)}."


async def control(kind: str, ident: str, action: str) -> str:
    if action not in ("start", "stop", "restart"):
        raise BadInput("action must be start, stop or restart.")
    data = await call("POST", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/{action}")
    dep = clean_label(data.get("deployment_uuid", ""), 40) if isinstance(data, dict) else ""
    return f"Coolify accepted {action}." + (f" It queued deployment {dep}." if dep else "")


async def cancel(deployment: str) -> str:
    await call("POST", f"/deployments/{valid_id(deployment)}/cancel")
    return "Coolify accepted the cancel."


async def _env_uuid(ident: str, key: str, kind: str = "application") -> str | None:
    rows = await call("GET", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/envs")
    for r in rows:
        if isinstance(r, dict) and r.get("key") == key and not r.get("is_preview"):
            return r.get("uuid")
    return None


async def env_set(ident: str, key: str, value: str, is_literal: bool, kind: str = "application") -> str:
    valid_env_key(key)
    base = f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/envs"
    body = {"key": key, "value": value, "is_literal": bool(is_literal)}
    if kind != "database":                                    # databases have no preview variables, and Coolify rejects fields it does not know
        body["is_preview"] = False
    if await _env_uuid(ident, key, kind):
        await call("PATCH", base, body=body)
        return f"Updated {key} (value not shown)."
    await call("POST", base, body=body)
    return f"Added {key} (value not shown)."


async def env_delete(ident: str, key: str, kind: str = "application") -> str:
    valid_env_key(key)
    env_id = await _env_uuid(ident, key, kind)
    if not env_id:
        raise CoolifyError("That variable does not exist here.")
    await call("DELETE", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/envs/{valid_id(env_id)}")
    return f"Deleted {key}."


# ---------------- deployment logs
def _log_lines(raw) -> list[str]:
    """Coolify keeps a deployment's log as a JSON text of entries ({output, timestamp, hidden...}); plain text is accepted too."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return raw.splitlines()
    if isinstance(raw, list):
        out = []
        for e in raw:
            if isinstance(e, dict):
                if e.get("hidden"):
                    continue
                out += str(e.get("output", "")).splitlines()
            else:
                out += str(e).splitlines()
        return out
    return []


async def deployment(ident: str, lines: int) -> str:
    """One deployment: its status and the END of its log (where a failure shows). Secret-looking text hidden, length capped."""
    lines = max(1, min(int(lines), config.max_log_lines()))
    data = await call("GET", f"/deployments/{valid_id(ident)}")
    if not isinstance(data, dict):
        raise CoolifyError("Coolify did not answer in the expected format.")
    head = json.dumps(short(data, DEPLOY_FIELDS), indent=1, ensure_ascii=False)
    tail = _log_lines(data.get("logs"))[-lines:]
    body = cap(redact_text("\n".join(tail))) if tail else "(no log lines)"
    return f"{head}\nLast {len(tail)} log lines:\n{body}"


# ---------------- servers, registries, cleanup (the server address is never shown)
REGISTRY_RE = re.compile(r"[a-z0-9][a-z0-9.-]{0,98}[a-z0-9](:\d{2,5})?", re.ASCII)


async def servers() -> list[dict]:
    rows = await call("GET", "/servers")
    return [pick(r, ("name", "uuid", "description")) for r in rows if isinstance(r, dict)]


async def registries(server: str) -> dict:
    data = await call("GET", f"/servers/{valid_id(server)}/registries")
    rows = data.get("registries", []) if isinstance(data, dict) else []
    out = {"registries": [pick(r, ("registry", "logged_in", "source")) for r in rows if isinstance(r, dict)]}
    if isinstance(data, dict) and data.get("error"):
        out["error"] = clean_label(data["error"], 120)               # an unreadable server must not look like "no logins"
    return out


async def registry_check(server: str, registry: str) -> str:
    if not isinstance(registry, str) or not REGISTRY_RE.fullmatch(registry):
        raise BadInput("That is not a valid registry name, like ghcr.io.")
    data = await call("POST", f"/servers/{valid_id(server)}/registries/{registry}/check")
    return clean_label(data.get("message", "Checked.") if isinstance(data, dict) else "Checked.", 120)


async def docker_cleanup(server: str) -> str:
    """Removes unused images and build leftovers. Never volumes, never networks, whatever is asked."""
    await call("POST", f"/servers/{valid_id(server)}/docker-cleanup/run", body={"delete_unused_volumes": False, "delete_unused_networks": False})
    return "Coolify started a Docker cleanup. We asked it to keep volumes and networks (not yet checked against the real Coolify)."


# ---------------- rollback
TAG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


async def rollback_images(ident: str) -> dict:
    data = await call("GET", f"/applications/{valid_id(ident)}/rollback-images")
    imgs = data.get("images", []) if isinstance(data, dict) else []
    return {"current": clean_label(data.get("current", ""), 80) if isinstance(data, dict) else "",
            "images": [pick(i, ("tag", "created_at", "is_current", "source")) for i in imgs[:30] if isinstance(i, dict)]}


async def rollback(ident: str, version: str) -> str:
    if not isinstance(version, str) or not TAG_RE.fullmatch(version):
        raise BadInput("That is not a valid image tag or commit.")
    data = await call("POST", f"/applications/{valid_id(ident)}/rollback", body={"commit": version})
    dep = clean_label(data.get("deployment_uuid", ""), 40) if isinstance(data, dict) else ""
    if not dep:
        raise CoolifyError("Coolify accepted the call but queued no rollback.")
    return f"Rollback queued. Deployment id {dep}."


# ---------------- app settings: a short allow-list, each value checked
def _bool(v):
    if isinstance(v, bool):
        return v
    if str(v).strip().lower() in ("true", "1", "yes", "on"):
        return True
    if str(v).strip().lower() in ("false", "0", "no", "off"):
        return False
    raise BadInput("That setting takes true or false.")


def _int(lo, hi):
    def check(v):
        try:
            if not re.fullmatch(r"[0-9]{1,6}", str(v).strip()):          # plain ASCII digits only (int() would also take full-width ones)
                raise ValueError
            n = int(str(v).strip())
        except ValueError:
            raise BadInput(f"That setting takes a whole number from {lo} to {hi}.") from None
        if not lo <= n <= hi:
            raise BadInput(f"That setting takes a whole number from {lo} to {hi}.")
        return n
    return check


def _pattern(regex, hint, limit=200):
    rx = re.compile(regex, re.ASCII)

    def check(v):
        v = str(v).strip()
        if len(v) > limit or not rx.fullmatch(v) or ".." in v:
            raise BadInput(f"That value is not allowed here. {hint}")
        return v
    return check


def _ports(regex, hint, pair=False):
    base = _pattern(regex, hint)

    def check(v):
        v = base(v)
        for chunk in v.split(","):
            for part in chunk.replace("127.0.0.1:", "").split(":"):
                if not 1 <= int(part) <= 65535:
                    raise BadInput("A port number is 1 to 65535.")
        return v
    return check


HOST = r"[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
# name -> (checker, careful?, the field Coolify shows it under). Commands, Dockerfiles, labels, git addresses and webhook secrets are NOT here on purpose.
SETTINGS = {
    "is_auto_deploy_enabled": (_bool, False, "is_auto_deploy_enabled"),
    "health_check_enabled": (_bool, False, "health_check_enabled"),
    "health_check_path": (_pattern(r"/[A-Za-z0-9_./-]{0,100}", "A path like /health."), False, "health_check_path"),
    "health_check_port": (lambda v: str(_int(1, 65535)(v)), False, "health_check_port"),        # Coolify takes this one as text
    "health_check_interval": (_int(1, 3600), False, "health_check_interval"),
    "health_check_timeout": (_int(1, 600), False, "health_check_timeout"),
    "health_check_retries": (_int(1, 20), False, "health_check_retries"),
    "ports_exposes": (_ports(r"\d{1,5}(,\d{1,5}){0,9}", "Port numbers separated by commas."), True, "ports_exposes"),
    "ports_mappings": (_ports(r"(127\.0\.0\.1:)?\d{1,5}:\d{1,5}(,(127\.0\.0\.1:)?\d{1,5}:\d{1,5}){0,9}",
                              "Pairs like 8080:80 (public) or 127.0.0.1:8080:80 (this server only), separated by commas."), True, "ports_mappings"),
    "domains": (_pattern(rf"https?://{HOST}(:\d{{1,5}})?(/[A-Za-z0-9_./-]*)?(,https?://{HOST}(:\d{{1,5}})?(/[A-Za-z0-9_./-]*)?){{0,4}}",
                         "Up to five web addresses like https://app.example.com, separated by commas.", 400), True, "fqdn"),
    "docker_compose_location": (_pattern(r"/[A-Za-z0-9_./-]{0,150}", "A path like /docker-compose.yml."), True, "docker_compose_location"),
    "base_directory": (_pattern(r"/[A-Za-z0-9_./-]{0,150}", "A path like /app."), True, "base_directory"),
    "git_branch": (_pattern(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,99}", "A branch name like main."), True, "git_branch"),
    "docker_registry_image_tag": (_pattern(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", "An image tag like latest."), True, "docker_registry_image_tag"),
}


def check_setting(name: str, value):
    if name not in SETTINGS:
        raise BadInput("That setting cannot be changed here. Allowed: " + ", ".join(sorted(SETTINGS)) + ".")
    return SETTINGS[name][0](value)


async def current_setting(ident: str, name: str) -> str:
    try:
        data = await call("GET", f"/applications/{valid_id(ident)}")
        return clean_label(data.get(SETTINGS[name][2], ""), 120) if isinstance(data, dict) else ""
    except CoolifyError:
        return ""


def exposure(name: str, value) -> tuple[str, str]:
    """(a warning for the ticket, a word the owner must type). Settings that publish something or can lock the owner out."""
    if name == "ports_mappings" and any(not part.startswith("127.0.0.1:") for part in str(value).split(",")):
        return ("OPENS A PUBLIC PORT on the server's own address. Docker ignores the firewall, so this bypasses Cloudflare and Zero Trust. "
                "Use 127.0.0.1:HOST:CONTAINER to keep it on this server."), "public-port"
    if name == "domains":
        hosts = {re.sub(r"^https?://", "", d).split("/")[0].split(":")[0].lower() for d in str(value).split(",")}
        if hosts & set(config.protected_hostnames()):
            raise BadInput("That host name is one of this server's own doors, Coolify or SSH. Changing it here could lock the owner out. Use the Coolify dashboard.")
        return "Changes which web addresses reach this app.", ""
    return "", ""


async def set_setting(ident: str, name: str, value) -> str:
    value = check_setting(name, value)
    await call("PATCH", f"/applications/{valid_id(ident)}", body={name: value})
    return f"Setting {name} changed. Most settings only apply at the next deployment."


# ---------------- read-only extras
async def storages(kind: str, ident: str) -> list[dict]:
    """Volumes and file mounts: names and paths only, never file contents."""
    data = await call("GET", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/storages")
    rows = []
    if isinstance(data, dict):
        for group in ("persistent_storages", "file_storages"):
            rows += [dict(pick(r, ("uuid", "name", "mount_path", "host_path", "fs_path")), group=group) for r in data.get(group, []) if isinstance(r, dict)]
    return rows


async def scheduled_tasks(kind: str, ident: str) -> list[dict]:
    if kind not in ("application", "service"):
        raise BadInput("Scheduled tasks exist for applications and services.")
    rows = await call("GET", f"/{KINDS[kind]}/{valid_id(ident)}/scheduled-tasks")
    out = []
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, dict):
            item = pick(r, ("uuid", "name", "frequency", "enabled", "container", "timeout"))
            if r.get("command"):
                item["command"] = clean_label(redact_text(r["command"]), 120)
            out.append(item)
    return out


BACKUP_FIELDS = ("uuid", "enabled", "frequency", "save_s3", "number_of_backups_locally", "database_backup_retention_amount_locally",
                 "database_backup_retention_days_locally", "database_backup_retention_amount_s3", "database_backup_retention_days_s3")


async def backups(ident: str):
    data = await call("GET", f"/databases/{valid_id(ident)}/backups")
    rows = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
    return [pick(r, BACKUP_FIELDS) for r in rows if isinstance(r, dict)]


# ---------------- run now (tickets only)
async def backup_run(kind: str, ident: str, storage: str) -> str:
    """Run the volume backup that is already set up for a storage. Nothing new is created."""
    await call("POST", f"/{KINDS[valid_kind(kind)]}/{valid_id(ident)}/storages/{valid_id(storage)}/backups/run")
    return "Coolify started the backup."


async def task_run(kind: str, ident: str, task: str, expect: str | None = None) -> str:
    """Run one scheduled task that already exists, once, now. It runs its saved command inside its container.
    `expect` is the digest of the command the owner was shown: if the task was edited since, nothing runs."""
    if kind not in ("application", "service"):
        raise BadInput("Scheduled tasks exist for applications and services.")
    if expect is not None and task_digest(*(await task_raw(kind, ident, task))[1:]) != expect:
        raise CoolifyError("The task's command changed after the ticket was made. Nothing was run. Ask again.")
    await call("POST", f"/{KINDS[kind]}/{valid_id(ident)}/scheduled-tasks/{valid_id(task)}/execute")
    return "Coolify started the task."


def task_digest(command: str, container: str) -> str:
    return hashlib.sha256((command + "\0" + (container or "")).encode()).hexdigest()


async def task_raw(kind: str, ident: str, task: str) -> tuple[str, str, str]:
    """(name, the command exactly as saved, its container) of an existing task. Used for the digest and for showing it in full."""
    if kind not in ("application", "service"):
        raise BadInput("Scheduled tasks exist for applications and services.")
    rows = await call("GET", f"/{KINDS[kind]}/{valid_id(ident)}/scheduled-tasks")
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, dict) and r.get("uuid") == task:
            return clean_label(r.get("name", ""), 60), str(r.get("command", "")), str(r.get("container", "") or "")
    raise CoolifyError("That scheduled task does not exist.")
