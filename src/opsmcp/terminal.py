"""A terminal on the server, over SSH, as its own user with its own key. Looking is free, typing is a ticket.

HONEST LIMITS: the terminal is a shell. Whatever the SSH user can do, a typed command can do. If that user is in the `docker` group
(needed for `server_numbers`), it can start any container, which is root on the server. the owner's tap, and reading the text, is the guard.
The warning list below helps the owner read; it is a hint and never a guarantee.

- The server's own public key is pinned (SSH_KNOWN_HOSTS): a look-alike machine is refused, nothing is trusted on first use.
- Sessions are `tmux` sessions named ops-<name>, addressed with tmux's EXACT-match form (`=ops-name`), so `a` can never hit `ab`.
  The prefix is a convention, not a wall: a shell inside a pane can still run tmux on other sessions.
- Text is sent to the pane as hex bytes (`send-keys -H`): tmux never parses it, so a `;` or a backslash arrives exactly as written.
- Every argument is checked and quoted for a POSIX shell (the SSH user's login shell must be sh or bash, not fish or csh).
- The "server numbers" are a FIXED list of read-only commands. Nothing Claude writes is ever part of them.
- What the screen shows is data: secret-looking text is hidden over the whole captured pane, control codes are stripped, the length is capped.
- One SSH connection per operation, at most two at a time, and reads are rate limited, so the tool cannot starve the owner's own logins."""
import asyncio
import hashlib
import json
import re
import shlex
import time
import unicodedata
from contextlib import asynccontextmanager

import asyncssh

from . import config
from .safety import BadInput, cap, redact_text, strip_control

CONNECT = asyncssh.connect          # tests put a fake here
NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,29}")
KEYS = {"enter": "Enter", "ctrl-c": "C-c", "ctrl-d": "C-d", "escape": "Escape", "tab": "Tab", "up": "Up", "down": "Down"}
MAX_TEXT = 500
MAX_READ_LINES = 300
PANE_LINES = 300                    # how far back one look at the screen goes
CONNECTIONS = asyncio.Semaphore(2)
READS_PER_MINUTE = 60
_reads: list[float] = []
SHELL_NOTE = ("This is a SHELL on the server. Whatever its user can do, this text can do, and that user can start Docker containers, which is "
              "as powerful as root. The warnings below are hints, not a guarantee: read the text yourself.")
NUMBERS = [("disk", ["df", "-h", "/"]), ("memory", ["free", "-m"]), ("load", ["uptime"]), ("docker disk", ["docker", "system", "df"]),
           ("containers", ["docker", "stats", "--no-stream", "--format", "{{.Name}}  cpu {{.CPUPerc}}  mem {{.MemUsage}}"])]
RISKY = [(re.compile(p, re.I), why) for p, why in (
    (r"\brm\b[^\n]*(\s-[a-z]*[rf]|--recursive|--force)|\bfind\b[^\n]*-delete|\bshred\b|\btruncate\b", "removes files"),
    (r"\bmkfs|\bdd\s+if=|>\s*/dev/|\bwipefs\b", "writes to a disk"),
    (r"\bchmod\b|\bchown\b|\bsetfacl\b", "changes permissions"),
    (r"(curl|wget)[^|;\n]*\|\s*\S*(sh|python|perl|ruby)\b|\|\s*(ba|z)?sh\b|\bsource\s|(^|\s)\.\s+\S", "runs a downloaded or other script"),
    (r"\b(curl|wget)\b[^\n]*(\s-[a-zA-Z]*[oO]\b|--output|--remote-name)", "downloads a file"),
    (r"\bdocker\s+(rm|rmi|kill|stop|exec|run|cp|system\s+prune|volume|network|compose|build|save|load)\b", "starts, stops or removes containers or data"),
    (r"\b(shutdown|reboot|halt|poweroff|init\s+[06]|systemctl\s+(stop|disable|mask|reboot|poweroff))\b", "turns something off"),
    (r"\bsudo\b|\bsu\b|\bdoas\b", "asks for more power"),
    (r"authorized_keys|sshd_config|\bpasswd\b|\bcrontab\b|\bufw\b|\biptables\b|\bnft\b|\.bashrc|\.profile|\.bash_profile|/etc/", "changes access or startup files"),
    (r"\bbase64\b|\beval\b|\bnc\b|\bncat\b|\bsocat\b|\bbash\s+-c|\bsh\s+-c|\bpython3?\s+-c|\bperl\s+-e|\bruby\s+-e|\bxargs\b|\btee\b", "hides or runs something indirectly"),
    (r":\(\)\s*\{", "a fork bomb"), (r"[;&|`<>]|\$\(|\$\{", "chains commands or redirects"))]


class TerminalError(Exception):
    """Safe to show."""
    safe = True


def configured() -> bool:
    return bool(config.ssh_host() and config.ssh_user() and config.ssh_key() and config.ssh_known_hosts())


def check_name(name: str) -> str:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise BadInput("A terminal name is lower case letters, digits and dashes, starting with a letter (up to 30).")
    return name


def check_text(text: str) -> str:
    if not isinstance(text, str) or not text or len(text) > MAX_TEXT or any(ord(c) < 32 and c != "\t" for c in text) or "\x7f" in text:
        raise BadInput(f"Text for the terminal is 1 to {MAX_TEXT} characters on one line, no control characters. Use the keys option for Enter and Ctrl-C.")
    return text


def warnings(text: str) -> list[str]:
    return sorted({why for rx, why in RISKY if rx.search(text)})


def session(name: str) -> str:
    return "ops-" + check_name(name)


def exact(name: str) -> str:
    """tmux's exact-match session form. Without the `=`, tmux falls back to prefix matching and `ops-a` would find `ops-ab`."""
    return "=" + session(name)


def pane(name: str) -> str:
    return exact(name) + ":"


def line_digest(line: str) -> str:
    return hashlib.sha256(line.encode()).hexdigest()


def _rate() -> None:
    now = time.time()
    _reads[:] = [t for t in _reads if t > now - 60]
    if len(_reads) >= READS_PER_MINUTE:
        raise TerminalError("Too many terminal looks in a minute. Wait a little.")
    _reads.append(now)


async def _connect():
    if not configured():
        raise TerminalError("The terminal is not set up here (SSH host, user, key or known-hosts missing).")
    try:
        key = asyncssh.import_private_key(config.ssh_key())
        known = asyncssh.import_known_hosts(config.ssh_known_hosts())
        return await CONNECT(config.ssh_host(), port=config.ssh_port(), username=config.ssh_user(), client_keys=[key], known_hosts=known,
                             agent_path=None, config=None, connect_timeout=10, login_timeout=15, keepalive_interval=15)
    except (asyncssh.Error, OSError, ValueError):
        raise TerminalError("Could not open a safe connection to the server (is the key, the host or the pinned server key right? "
                            "For a port other than 22 the known-hosts line must start with [host]:port).") from None


@asynccontextmanager
async def connection():
    """One SSH connection for one operation, at most two at a time."""
    async with CONNECTIONS:
        conn = await _connect()
        try:
            yield conn
        finally:
            conn.close()
            try:
                await asyncio.wait_for(conn.wait_closed(), 5)
            except Exception:
                pass


def _q(arg) -> str:
    """Shell-quote one argument. A word starting with `=` is always quoted (zsh would expand it) even though sh would not need it."""
    arg = str(arg)
    q = shlex.quote(arg)
    return "'" + arg + "'" if q == arg and arg.startswith("=") else q


async def run(conn, args: list[str], timeout: int = 20) -> tuple[int, str]:
    """One fixed command on the server. Every part is quoted. Returns (exit code, output)."""
    try:
        done = await conn.run(" ".join(_q(a) for a in args), check=False, timeout=timeout, errors="replace")
    except (asyncssh.Error, OSError):
        raise TerminalError("The command did not finish in time or the connection broke.") from None
    return (done.exit_status if isinstance(done.exit_status, int) else -1), str(done.stdout or "") + str(done.stderr or "")


async def numbers() -> str:
    """Disk, memory, load, Docker space, containers. A fixed list: the only commands this tool ever runs on its own."""
    _rate()
    out = []
    async with connection() as conn:
        for title, args in NUMBERS:
            code, text = await run(conn, args)
            out.append(f"## {title}" + ("" if code == 0 else f" (exit {code})") + "\n" + cap(redact_text(text), 1500).strip())
    return "\n\n".join(out)


async def list_sessions() -> list[str]:
    _rate()
    async with connection() as conn:
        code, text = await run(conn, ["tmux", "list-sessions", "-F", "#{session_name}"])
    return [] if code != 0 else sorted(n[4:] for n in text.split() if n.startswith("ops-") and NAME_RE.fullmatch(n[4:]))


async def open_session(name: str) -> str:
    async with connection() as conn:
        code, _ = await run(conn, ["tmux", "has-session", "-t", exact(name)])
        if code == 0:
            raise TerminalError("That terminal is already open.")
        code, _ = await run(conn, ["tmux", "new-session", "-d", "-s", session(name), "-x", "200", "-y", "50"])
    if code != 0:
        raise TerminalError("Could not open the terminal (is tmux installed for that user?).")
    return f"Terminal {name} is open."


async def close_session(name: str) -> str:
    async with connection() as conn:
        code, _ = await run(conn, ["tmux", "kill-session", "-t", exact(name)])
    if code != 0:
        raise TerminalError("That terminal does not exist.")
    return f"Terminal {name} is closed."


async def _screen(conn, name: str) -> str:
    code, text = await run(conn, ["tmux", "capture-pane", "-p", "-J", "-t", pane(name), "-S", f"-{PANE_LINES}"])
    if code != 0:
        raise TerminalError("That terminal does not exist.")
    text = "\n".join(l.rstrip() for l in strip_control(text).splitlines())
    return redact_text(text).strip("\n")            # hidden over the whole captured pane first, then cut to the last lines


def prompt_context(screen: str) -> str:
    """The last three non-empty lines of the screen: what Enter would run (earlier lines of a continuation or a heredoc matter too).
    Shown to the owner in full and digested as-is; too long to show in full means refused."""
    lines = [l.strip() for l in screen.splitlines() if l.strip()]
    ctx = "\n".join(lines[-3:])
    if len(ctx) > 300:
        raise TerminalError("The lines at the prompt are too long to show in full. Clear the line first (ctrl-c), then ask again.")
    return ctx


def visible(text: str) -> str:
    """Text with line breaks, control and invisible characters written out as \\n, \\u202e ... so nothing about it is hidden."""
    return "".join(f"\\u{ord(c):04x}" if (unicodedata.category(c) in ("Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp") and c != "\n") else ("\\n" if c == "\n" else c) for c in text)


async def read(name: str, lines: int) -> str:
    lines = max(1, min(int(lines), MAX_READ_LINES))
    _rate()
    async with connection() as conn:
        screen = await _screen(conn, name)
    text = "\n".join(screen.splitlines()[-lines:])
    limit = config.output_max_chars()
    if len(text) > limit:                                         # a terminal's newest lines matter most: keep the tail
        text = f"[cut: {len(text) - limit} earlier characters]\n" + text[-limit:]
    return text or "(the screen is empty)"


async def prompt_line(name: str) -> str:
    """The last non-empty line of the screen: what Enter would run. Secret-looking text already hidden."""
    _rate()
    async with connection() as conn:
        return prompt_context(await _screen(conn, name))


async def write(name: str, text: str, key: str, expect: str | None = None) -> str:
    """Type text (as bytes, never run by us) and/or press one key. The caller has already had the owner's tap.
    `expect` is the digest of the prompt line the owner was shown; if the line is different now, nothing is typed."""
    check_name(name)
    if not text and not key:
        raise BadInput("Give text, a key, or both.")
    if key and key not in KEYS:
        raise BadInput("Allowed keys: " + ", ".join(sorted(KEYS)) + ".")
    if text:
        check_text(text)
    async with connection() as conn:
        if expect is not None and line_digest(prompt_context(await _screen(conn, name))) != expect:
            raise TerminalError("The line at the prompt changed after the ticket was made. Nothing was typed. Ask again.")
        if text:
            code, _ = await run(conn, ["tmux", "send-keys", "-t", pane(name), "-H", *[f"{b:02x}" for b in text.encode("utf-8")]])
            if code != 0:
                raise TerminalError("Typing failed: that terminal may not exist, or tmux on the server may be older than 3.0 (it cannot type from hex).")
        if key:
            code, _ = await run(conn, ["tmux", "send-keys", "-t", pane(name), KEYS[key]])
            if code != 0:
                raise TerminalError("That terminal does not exist.")
    return f"Typed into {name}" + (f" and pressed {key}." if key else ".")


def describe(text: str, key: str) -> str:
    bits = ([f"type {json.dumps(text)}"] if text else []) + ([f"press {key}"] if key else [])
    return " and ".join(bits)
