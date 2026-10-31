"""One small action log: what was asked, what was approved or refused, what happened. Never secret values, never full logs.
Every line passes through the secret hider, and the file is capped."""
import json
import sys
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config
from .safety import clean_label, redact_text

UTC = ZoneInfo("UTC")
_lock = threading.Lock()


def log_file():
    return config.data_dir() / "actions.log"


def log(event: str, /, **fields) -> None:
    clean = {k: (clean_label(redact_text(v), 300) if isinstance(v, str) else v) for k, v in fields.items()}
    line = json.dumps({"t": f"{datetime.now(UTC):%Y-%m-%d %H:%M:%S}", "event": event, **clean}, ensure_ascii=False) + "\n"
    with _lock:
        try:
            path = log_file()
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
            limit = config.action_log_max_mb() * 1024 * 1024
            if path.stat().st_size > limit:
                lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
                path.write_text("".join(lines[len(lines) // 2:]), encoding="utf-8")
        except OSError:                      # a full or unwritable disk must never stop a Freeze or a refusal
            print(line.strip()[:300], file=sys.stderr)


def recent(limit: int = 30) -> list[str]:
    path = log_file()
    if not path.exists():
        return []
    with _lock:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for raw in reversed(lines):
        try:
            d = json.loads(raw)
            rest = " ".join(f"{k}={v}" for k, v in d.items() if k not in ("t", "event"))
            out.append(f"{d.get('t', '')} {d.get('event', '')} {rest}".strip())
        except ValueError:
            continue
    return out


def recent_events(limit: int = 30) -> list[dict]:
    """The same lines as recent(), as records, newest first."""
    path = log_file()
    if not path.exists():
        return []
    with _lock:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for raw in reversed(lines):
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        if isinstance(d, dict):
            d["t"] = d.get("t", "")
            out.append(d)
    return out
