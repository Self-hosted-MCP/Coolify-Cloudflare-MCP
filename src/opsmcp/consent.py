"""The double consent. A change is never done because Claude asked. It becomes a TICKET that the owner must tap on their Confirm page.

- The words on the ticket are built by this server from checked arguments, never taken from the model's own text.
- The exact checked arguments are fixed with a hash when the ticket is made, and checked again just before running.
- One ticket is one action. It can run once, only after a tap, only before it expires, and never twice.
- The action is done from the CHECKED arguments (the payload the hash covers), so the hash check is real.
- Freeze and READ_ONLY are checked again at the moment of running and when tapping, and Freeze cancels every open ticket.
- Asking is rate limited, the number of open tickets is limited, and a Freeze switch or READ_ONLY stops everything."""
import asyncio
import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from . import audit, config
from .safety import clean_label

MAX_OPEN = 5
MAX_SUMMARY = 900
MAX_DETAIL = 900
MAX_WORD = 260
LATE_GRACE = 120      # a ticket tapped just before it expires can still be collected for this many seconds


class ConsentError(Exception):
    """Safe to show."""
    safe = True


class WrongWord(ConsentError):
    """the owner typed the confirm word wrong."""


class ChangesOff(ConsentError):
    """Frozen or read-only."""


@dataclass
class Ticket:
    id: str
    tool: str
    summary: str
    payload: dict
    payload_hash: str
    runner: Callable[[dict, object], Awaitable[str]] = field(repr=False)   # runner(payload, secret): the ONLY thing that acts
    secret: object = field(default=None, repr=False)                      # a value the owner must not see on the page (never logged)
    detail: str = ""                                                      # shown on the ticket page only, never written to the log
    confirm_word: str = ""                                                # if set, the owner must type exactly this on the page to confirm
    log_summary: str = ""                                                 # what the log says instead of the summary (when the summary holds typed text)
    why: str = ""
    risk: str = "normal"                # "high" shows a red badge on the Confirm page
    created: float = field(default_factory=time.time)
    expires: float = 0.0
    status: str = "pending"             # pending, approved, denied, expired, running, done, failed
    decided_by: str = ""
    result: str = ""


def frozen_file():
    return config.data_dir() / "frozen"


def until_file():
    return config.data_dir() / "unfrozen_until"


_frozen_now = False      # kept in memory too, so a full or unwritable disk cannot stop Freeze from working
_until = 0.0             # when an Unfreeze runs out (0 = no timer); kept in a file too, so a restart keeps the timer


def unfrozen_until() -> float:
    global _until
    if not _until:
        try:
            _until = float(until_file().read_text().strip() or 0)
        except (OSError, ValueError):
            _until = 0.0
    return _until


def frozen() -> bool:
    if _frozen_now or frozen_file().exists():
        return True
    until = unfrozen_until()
    if until and time.time() >= until:           # the Unfreeze ran out: freeze again by itself
        set_frozen(True)
        audit.log("frozen", by="timer")
        return True
    return False


def set_frozen(value: bool) -> None:
    global _frozen_now, _until, _allow_all_until
    _frozen_now = value
    if value:
        _allow_all_until = 0.0                   # Freeze also ends Allow all
    minutes = config.unfreeze_minutes()
    _until = 0.0 if value or not minutes else time.time() + minutes * 60
    path = frozen_file()
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if value:
            path.write_text("frozen\n")
            until_file().unlink(missing_ok=True)
        else:
            path.unlink(missing_ok=True)
            if _until:
                until_file().write_text(f"{_until:.0f}\n")
            else:
                until_file().unlink(missing_ok=True)
    except OSError:
        audit.log("error", what="could not save the freeze flag; it holds until the next restart")


_allow_all_until = 0.0   # the "Allow all" window; memory only on purpose, so a restart ends it


def allow_all_until() -> float:
    """When the Allow all window ends, or 0 if it is not on."""
    global _allow_all_until
    if _allow_all_until and time.time() >= _allow_all_until:
        _allow_all_until = 0.0
        audit.log("allow all ended", by="timer")
    return _allow_all_until


def start_allow_all() -> float:
    global _allow_all_until
    minutes = config.allow_all_minutes()
    if not minutes or config.read_only() or frozen():
        return 0.0
    _allow_all_until = time.time() + minutes * 60
    return _allow_all_until


def stop_allow_all() -> bool:
    global _allow_all_until
    was = bool(_allow_all_until)
    _allow_all_until = 0.0
    return was


_secret = secrets.token_bytes(32)


def _key() -> bytes:
    k = config.env("SECRET_KEY")
    return k.encode() if k else _secret      # without SECRET_KEY the page's forms stop working after a restart; nothing else breaks


def csrf(scope: str, who: str) -> str:
    """A form token that only the page for this person and this ticket (or switch) carries."""
    return hmac.new(_key(), f"{scope}|{who}".encode(), hashlib.sha256).hexdigest()[:40]


def csrf_ok(scope: str, who: str, token: str) -> bool:
    return hmac.compare_digest(csrf(scope, who), token or "")


def payload_digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class Engine:
    def __init__(self):
        self.lock = threading.Lock()
        self.tickets: dict[str, Ticket] = {}
        self.asked: list[float] = []

    def _sweep(self) -> None:
        now = time.time()
        for t in self.tickets.values():
            if t.status in ("pending", "approved") and t.expires < now:
                t.status = "expired"
                t.secret = None
                audit.log("expired", ticket=t.id, tool=t.tool)
        for tid in [i for i, t in self.tickets.items() if t.expires + 3600 < now]:   # forget old tickets after an hour
            del self.tickets[tid]

    def create(self, tool: str, summary: str, payload: dict, runner, why: str = "", risk: str = "normal",
               detail: str = "", secret=None, confirm_word: str = "", log_summary: str = "") -> Ticket:
        if config.read_only():
            raise ChangesOff("This server is in read-only mode. Changes are switched off.")
        if frozen():
            raise ChangesOff(f"Changes are frozen. Send the owner this link so they can unfreeze them: {config.confirm_url()}/confirm")
        with self.lock:
            self._sweep()
            now = time.time()
            self.asked = [x for x in self.asked if x > now - 60]
            if len(self.asked) >= config.rate_limit_per_minute():
                raise ConsentError("Too many requests in a minute. Wait a little.")
            if sum(1 for t in self.tickets.values() if t.status in ("pending", "approved")) >= MAX_OPEN:
                raise ConsentError("There are already several changes waiting for the owner's tap. Let them deal with those first.")
            if len(summary) > MAX_SUMMARY or len(detail) > MAX_DETAIL or len(confirm_word) > MAX_WORD:     # never cut what the owner reads: refuse instead
                raise ConsentError("The ticket text would be too long to read safely. Use a shorter value.")
            self.asked.append(now)
            t = Ticket(id=secrets.token_urlsafe(12), tool=tool, summary=summary, payload=payload,
                       payload_hash=payload_digest(payload), runner=runner, secret=secret, detail=detail, confirm_word=confirm_word.strip(), log_summary=log_summary[:200],
                       why=clean_label(why or "", 160), risk=risk, expires=now + config.confirm_ttl())
            self.tickets[t.id] = t
            auto = bool(allow_all_until())
            if auto:                                   # the owner switched on Allow all: this one needs no tap
                t.status, t.decided_by = "approved", "allow-all"
                t.expires = max(t.expires, now + LATE_GRACE)
        audit.log("asked", ticket=t.id, tool=tool, summary=(log_summary or summary)[:200], risk=risk)
        if auto:
            audit.log("approved", ticket=t.id, tool=tool, by="allow-all window")
        return t

    def get(self, ticket_id: str) -> Ticket | None:
        with self.lock:
            self._sweep()
            return self.tickets.get(ticket_id)

    def cancel_all(self, reason: str) -> int:
        """Freeze: every open or approved ticket is cancelled."""
        n = 0
        with self.lock:
            for t in self.tickets.values():
                if t.status in ("pending", "approved"):
                    t.status = "denied"
                    t.secret = None
                    n += 1
        if n:
            audit.log("cancelled", count=n, reason=reason)
        return n

    def open_tickets(self) -> list[Ticket]:
        with self.lock:
            self._sweep()
            return sorted((t for t in self.tickets.values() if t.status == "pending"), key=lambda t: t.created)

    def decide(self, ticket_id: str, approve: bool, who: str, typed: str = "") -> str:
        """Only the Confirm page calls this, after Zero Trust and the form token have been checked."""
        with self.lock:
            self._sweep()
            t = self.tickets.get(ticket_id)
            if not t or t.status != "pending":
                raise ConsentError("That ticket is no longer open.")
            if approve and (config.read_only() or frozen()):
                raise ChangesOff("Changes are frozen or switched off, so nothing can be approved now.")
            if approve and t.confirm_word and typed.strip() != t.confirm_word:
                raise WrongWord("The word you typed does not match. Type it exactly to confirm.")
            t.status = "approved" if approve else "denied"
            t.decided_by = who
            if approve:
                t.expires = max(t.expires, time.time() + LATE_GRACE)
            else:
                t.secret = None
        audit.log("approved" if approve else "denied", ticket=t.id, tool=t.tool, by="owner")
        return t.status

    async def run_if_approved(self, ticket_id: str) -> tuple[str, str]:
        """(state, text). Runs the action once, only if it was approved and the checked arguments are unchanged."""
        with self.lock:
            self._sweep()
            t = self.tickets.get(ticket_id)
            if not t:
                return "unknown", "No such ticket (it may be old, or the server restarted). Nothing was done."
            if t.status == "pending":
                return "pending", "Still waiting for the owner's tap."
            if t.status == "denied":
                return "denied", "the owner said no. Nothing was done."
            if t.status == "expired":
                return "expired", "It was not confirmed in time. Nothing was done."
            if t.status in ("done", "failed"):
                return t.status, t.result
            if t.status == "running":
                return "running", "It is running now."
            if config.read_only() or frozen():                     # approved earlier, but changes were switched off since
                t.status = "denied"
                t.secret = None
                audit.log("refused", ticket=t.id, tool=t.tool, why="frozen or read-only at run time")
                return "denied", "Changes are frozen or switched off. Nothing was done."
            if payload_digest(t.payload) != t.payload_hash:        # approved, but the arguments are not what the owner saw
                t.status = "failed"
                t.secret = None
                t.result = "Refused: the request changed after it was approved."
                audit.log("refused", ticket=t.id, tool=t.tool, why="payload changed")
                return "failed", t.result
            t.status = "running"
        try:
            text = await t.runner(t.payload, t.secret)
            status = "done"
        except asyncio.CancelledError:                              # the client dropped the call: the result is unknown, never retried
            with self.lock:
                t.status, t.secret = "failed", None
                t.result = "The request was cut off while it ran, so the result is unknown. Check Coolify before asking again."
            audit.log("failed", ticket=t.id, tool=t.tool, result="cancelled while running")
            raise
        except Exception as exc:                                    # only our own error classes (marked safe) may show their text
            status, text = "failed", (f"It failed: {exc}" if getattr(exc, "safe", False) else "It failed inside the server.")
        with self.lock:
            t.status, t.result = status, text[:2000]
            t.secret = None                                        # the value is not kept once the action is over
        audit.log("ran" if status == "done" else "failed", ticket=t.id, tool=t.tool, result=text[:200])
        return status, t.result

    async def wait_and_run(self, t: Ticket, wait_seconds: int, page: str) -> str:
        deadline = time.time() + max(0, wait_seconds)
        while True:
            state, text = await self.run_if_approved(t.id)
            if state != "pending":
                return ("Done: " if state == "done" else "") + text
            if time.time() >= deadline:
                return (f"Waiting for the owner's tap. Nothing has been done yet.\nTicket: {t.id}\nWhat will happen: {t.summary}\n"
                        f"Ask the owner to open {page} and tap Confirm, then call ops_result with this ticket. "
                        f"It stays open for {max(1, int((t.expires - time.time()) // 60))} more minutes.")
            await asyncio.sleep(0.5)


ENGINE = Engine()
