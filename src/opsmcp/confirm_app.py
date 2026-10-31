"""the owner's Confirm page. Its own port, reachable only through a Cloudflare tunnel address that sits behind Zero Trust "owner only".
Every request must carry Cloudflare's signed token naming an allowed email. Forms are plain HTML (no scripts), every change needs
a form token tied to the person and the ticket, and cross-site posts are refused."""
import html
import threading
import time
from urllib.parse import urlparse

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Route

from . import access, audit, config, consent

PROVIDER = None
HEADERS = {
    # same-origin, not no-referrer: with no-referrer Chrome sends "Origin: null" on the page's own forms, and the cross-site check refuses every tap.
    "Cache-Control": "no-store", "Referrer-Policy": "same-origin", "X-Frame-Options": "DENY", "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
}
NOTES = {"confirmed": "Confirmed.", "denied": "Denied.", "gone": "That ticket is no longer open.", "frozen": "Changes are frozen.",
         "unfrozen": "Changes are allowed again.", "typed": "The word you typed did not match, so nothing was confirmed.", "off": "Changes are frozen or switched off, so nothing can be confirmed now.", "pairing": "New apps can connect for 5 minutes.", "disconnected": "App disconnected.",
         "allall": "Confirmed. Allow all is on: changes need no tap until it ends or you press Stop.", "allstopped": "Allow all stopped. Each change needs your tap again.", "allno": "Allow all could not start (frozen, read-only or switched off)."}
CSS = """:root{color-scheme:dark;
--bg:oklch(.19 .012 260);--surface:oklch(.245 .014 260);--fg:oklch(.95 .006 260);--mut:oklch(.74 .012 260);--line:oklch(.34 .014 260);
--go:oklch(.75 .16 152);--on-go:oklch(.17 .03 152);--go-soft:oklch(.28 .05 152);--stop:oklch(.72 .16 22);--on-stop:oklch(.17 .03 22);--stop-soft:oklch(.28 .05 22);
--warn:oklch(.86 .1 85);--warn-soft:oklch(.3 .05 80);--warn-line:oklch(.5 .08 80);--cold-soft:oklch(.28 .03 245);--ink:oklch(.93 .006 260);--on-ink:oklch(.2 .012 260);
--shadow:0 1px 2px #0006}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scrollbar-color:var(--line) transparent;accent-color:var(--go)}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:20px 16px 48px;caret-color:var(--go)}
::selection{background:var(--go);color:var(--on-go)}
main{max-width:34rem;margin:0 auto}
h1{font-size:1.75rem;line-height:1.15;font-weight:700;letter-spacing:-.02em;margin:.25rem 0 1.25rem;text-wrap:balance}
h2{font-size:.8125rem;font-weight:650;letter-spacing:.02em;color:var(--mut);margin:2rem 0 .6rem;text-transform:none}
p{margin:0}.mut{color:var(--mut);font-size:.9375rem}b{font-weight:650}
a{color:inherit;text-underline-offset:.2em}
a.back{display:inline-flex;align-items:center;gap:.35rem;min-height:44px;color:var(--mut);text-decoration:none;font-size:.9375rem}
a.back:hover{color:var(--fg)}
svg{width:1.25rem;height:1.25rem;flex:none;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}
.note{background:var(--go-soft);border:1px solid var(--line);border-radius:12px;padding:.7rem .9rem;margin:0 0 1rem;font-size:.9375rem}
.panel{border-radius:16px;padding:1rem 1.1rem 1.1rem;margin:0 0 .75rem;border:1px solid var(--line);background:var(--surface)}
.panel.frozen{background:var(--cold-soft)}.panel.open{background:var(--go-soft)}.panel.hot{background:var(--warn-soft);border-color:var(--warn-line);color:var(--warn)}
.state{display:flex;align-items:center;gap:.6rem;font-size:1.1875rem;font-weight:650;line-height:1.25;margin:0 0 .3rem}
.panel.hot .mut{color:inherit;opacity:.9}
.req{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:1rem 1.1rem;margin:0 0 .75rem;box-shadow:var(--shadow)}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin:0 0 .5rem}
.badge{display:inline-flex;align-items:center;font-size:.8125rem;font-weight:600;border-radius:99px;padding:.1rem .65rem;background:var(--go-soft);color:var(--go)}
.badge.hi{background:var(--stop-soft);color:var(--stop)}
.time{font-size:.875rem;color:var(--mut);font-variant-numeric:tabular-nums}
.sum{font-size:1.1875rem;font-weight:620;line-height:1.35;margin:.1rem 0 .4rem;word-break:break-word;text-wrap:pretty}
.empty{display:flex;align-items:center;gap:.6rem;padding:.9rem 1.1rem;border:1px dashed var(--line);border-radius:16px;color:var(--mut);margin:0 0 .75rem}
.row{display:flex;gap:.75rem;margin-top:.9rem}.row form{flex:1;display:block}
button,a.btn{display:flex;align-items:center;justify-content:center;width:100%;min-height:52px;padding:.7rem 1rem;border-radius:14px;border:1.5px solid var(--line);background:transparent;color:var(--fg);font:inherit;font-weight:620;text-decoration:none;cursor:pointer;transition:background-color .15s cubic-bezier(.22,1,.36,1),transform .1s}
button:active,a.btn:active{transform:scale(.985)}
button:hover,a.btn:hover{background:color-mix(in oklch,var(--fg) 6%,transparent)}
button.go{background:var(--go);border-color:var(--go);color:var(--on-go)}button.go:hover{background:color-mix(in oklch,var(--go) 88%,var(--fg))}
button.stop{border-color:var(--stop);color:var(--stop)}button.stop.solid{background:var(--stop);color:var(--on-stop)}button.stop.solid:hover{background:color-mix(in oklch,var(--stop) 88%,var(--fg))}
button.ink{background:var(--ink);border-color:var(--ink);color:var(--on-ink)}button.ink:hover{background:color-mix(in oklch,var(--ink) 88%,var(--bg))}
button.quiet{min-height:44px;font-weight:550;color:var(--mut)}
a.btn.primary{background:var(--ink);border-color:var(--ink);color:var(--on-ink)}
button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--go);outline-offset:2px}
.panel form{margin-top:.9rem}
.list{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden}
.item{display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.75rem 1.1rem}.item+.item{border-top:1px solid var(--line)}
.item.stack{flex-direction:column;align-items:stretch}.item.stack form,.item.stack button{width:100%}.item form{flex:none}.item button{min-height:40px;width:auto;padding:.3rem .9rem;font-size:.9375rem}
.dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;background:var(--mut);margin-right:.5rem;vertical-align:.05em}.dot.ok{background:var(--go)}
.mut b{color:var(--fg)}
details{margin-top:2rem}summary{cursor:pointer;min-height:44px;display:flex;align-items:center;font-size:.8125rem;font-weight:650;letter-spacing:.02em;color:var(--mut);list-style:none}
summary::-webkit-details-marker{display:none}summary::after{content:"";width:.5rem;height:.5rem;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(45deg);margin:-.2rem 0 0 .6rem;transition:transform .2s}details[open] summary::after{transform:rotate(225deg);margin-top:.2rem}
.log{list-style:none;margin:.25rem 0 0;padding:0}.log li{display:grid;grid-template-columns:5.2rem 1fr;gap:.6rem;padding:.55rem 0;border-top:1px solid var(--line);font-size:.9375rem}
.log time{color:var(--mut);font-size:.8125rem;font-variant-numeric:tabular-nums;padding-top:.1rem}.log .d{color:var(--mut);word-break:break-word}.log .t-go{color:var(--go)}.log .t-stop{color:var(--stop)}
input[name=typed]{width:100%;min-height:52px;padding:.6rem .8rem;margin:.5rem 0 .2rem;font:inherit;color:var(--fg);background:var(--bg);border:1.5px solid var(--line);border-radius:12px}
.why{margin:.3rem 0 0}.fine{font-size:.875rem;color:var(--mut);margin:.7rem 0 0}
.sep{border:0;border-top:1px solid var(--line);margin:1.1rem 0 .2rem}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}"""



ICONS = {
    "lock": "<svg viewBox='0 0 24 24' aria-hidden='true'><rect x='5' y='11' width='14' height='9' rx='2'/><path d='M8 11V8a4 4 0 0 1 8 0v3'/></svg>",
    "check": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='12' r='9'/><path d='m8.5 12.5 2.5 2.5 4.5-5'/></svg>",
    "bolt": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M13 3 5 13.5h6L10 21l8-10.5h-6z'/></svg>",
    "inbox": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M4 13.5 6.5 5h11L20 13.5V19H4z'/><path d='M4 13.5h5l1 2h4l1-2h5'/></svg>",
    "back": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M15 6l-6 6 6 6'/></svg>",
}
HEAD = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='color-scheme' content='dark'><meta name='theme-color' content='#14161c'><title>Confirm</title><style>" + CSS + "</style></head><body><main>")
TAIL = "</main></body></html>"
GO_EVENTS = {"ran", "approved", "unfrozen", "allow all started"}
STOP_EVENTS = {"denied", "failed", "refused", "cancelled", "frozen", "expired", "error", "allow all stopped"}


def e(value) -> str:
    return html.escape(str(value), quote=True)


def left(t) -> str:
    s = max(0, int(t.expires - time.time()))
    return f"{s // 60}:{s % 60:02d} left"


def when(stamp: str) -> str:
    """'2026-10-30 16:19:27' -> '16:19' today, or '30 Oct 16:19' on another day."""
    try:
        day, clock = stamp.split(" ")
        if day == time.strftime("%Y-%m-%d"):
            return clock[:5]
        y, m, d = day.split("-")
        return f"{int(d)} {('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec').split()[int(m) - 1]} {clock[:5]}"
    except (ValueError, IndexError):
        return stamp


def describe(d: dict) -> tuple[str, str]:
    """One log record in plain words: (headline, detail)."""
    ev, by = d.get("event", ""), d.get("by", "")
    auto = "allow-all" in by
    detail = d.get("summary") or d.get("result") or d.get("why") or d.get("reason") or ""
    if ev == "asked":
        return "Claude asked for a change", detail
    if ev == "approved":
        return ("Allowed automatically (Allow all)" if auto else "You confirmed"), ""
    if ev == "denied":
        return "You denied it", ""
    if ev == "ran":
        return "Done", detail
    if ev == "failed":
        return "It failed", detail
    if ev == "expired":
        return "Nobody tapped in time", ""
    if ev == "cancelled":
        return "Open requests were cancelled", d.get("reason", "")
    if ev == "frozen":
        return ("Changes froze by themselves" if by == "timer" else "You froze changes"), ""
    if ev == "unfrozen":
        return "You unfroze changes", ""
    if ev == "allow all started":
        return "You turned on Allow all", f"until {d.get('until', '')}" if d.get("until") else ""
    if ev == "allow all stopped":
        return "You stopped Allow all", ""
    if ev == "allow all ended":
        return "Allow all ended by itself", ""
    if ev == "pairing opened":
        return "You let a new app connect", ""
    if ev == "app disconnected":
        return "You disconnected an app", ""
    return ev.capitalize(), detail


def activity_html() -> str:
    rows = []
    for d in audit.recent_events(40):
        if d.get("event") == "tool":                    # plain look-ups are not changes; they would only bury the real story
            continue
        head, detail = describe(d)
        tone = " t-go" if d.get("event") in GO_EVENTS else " t-stop" if d.get("event") in STOP_EVENTS else ""
        rows.append(f"<li><time>{e(when(d.get('t', '')))}</time><div><span class='{tone.strip()}'>{e(head)}</span>"
                    f"{('<div class=d>' + e(detail) + '</div>') if detail else ''}</div></li>")
        if len(rows) >= 15:
            break
    body = "".join(rows) or "<li><time></time><div class='d'>Nothing yet.</div></li>"
    return f"<details><summary>Recent activity</summary><ul class='log'>{body}</ul></details>"


def page(who: str, note: str = "") -> str:
    tickets = consent.ENGINE.open_tickets()
    cards = []
    for t in tickets:
        careful = t.risk == "high"
        cards.append(
            f"<div class='req'><div class='meta'><span class='badge{' hi' if careful else ''}'>{'Careful' if careful else 'Change'}</span>"
            f"<span class='time'>{left(t)}</span></div><div class='sum'>{e(t.summary)}</div>"
            f"<div class='row'><a class='btn primary' href='/confirm/{e(t.id)}'>Review</a></div></div>")
    waiting = "".join(cards) or f"<div class='empty'>{ICONS['inbox']}<span>All clear. Nothing is waiting for you.</span></div>"
    frozen = consent.frozen()
    until = consent.unfrozen_until()
    all_until = consent.allow_all_until()
    hot = ""
    if all_until:
        hot = (f"<div class='panel hot'><div class='state'>{ICONS['bolt']}<span>ALLOW ALL is on until {time.strftime('%H:%M', time.localtime(all_until))}.</span></div>"
               f"<p class='mut'>Every change Claude asks for runs with no tap. After that, each change needs a tap again.</p>"
               f"<form method='post' action='/allow-all/stop'><input type='hidden' name='csrf' value='{consent.csrf('allowall', who)}'>"
               f"<button class='stop solid'>Stop Allow all now</button></form></div>")
    if frozen:
        switch = (f"<div class='panel frozen'><div class='state'>{ICONS['lock']}<span>Changes are FROZEN.</span></div>"
                  f"<p class='mut'>Frozen: Claude can still look, but cannot ask for any change.</p>")
    else:
        timer = f" They freeze again by themselves at {time.strftime('%H:%M', time.localtime(until))}." if until else ""
        switch = (f"<div class='panel open'><div class='state'>{ICONS['check']}<span>Changes are allowed.</span></div>"
                  f"<p class='mut'>Each one still needs your tap.{timer}</p>")
    switch += (f"<form method='post' action='/freeze'><input type='hidden' name='csrf' value='{consent.csrf('freeze', who)}'>"
               f"<button class='{'ink' if frozen else 'stop'}'>{'Unfreeze' if frozen else 'Freeze all changes'}</button></form></div>")
    apps_html = ""
    if PROVIDER:
        pairing = "open for a few minutes" if PROVIDER.pairing_open() else "closed"
        items = "".join(
            f"<div class='item'><span><span class='dot{' ok' if a['signed_in'] else ''}'></span>{e(a['name'])} <span class='mut'>{'signed in' if a['signed_in'] else 'not signed in'}</span></span>"
            f"<form method='post' action='/apps/disconnect'><input type='hidden' name='csrf' value='{consent.csrf('apps', who)}'>"
            f"<input type='hidden' name='id' value='{e(a['id'])}'><button class='stop'>Disconnect</button></form></div>"
            for a in PROVIDER.apps()) or "<div class='item mut'>No app is connected.</div>"
        apps_html = (f"<h2>Connected apps</h2><div class='list'>{items}"
                     f"<div class='item stack'><span class='mut'>New apps can connect: <b>{pairing}</b></span>"
                     f"<form method='post' action='/pairing'><input type='hidden' name='csrf' value='{consent.csrf('pairing', who)}'>"
                     f"<button>Allow a new app (5 minutes)</button></form></div></div>")
    return (HEAD + "<h1>Confirm</h1>" + (f"<p class='note' role='status'>{e(note)}</p>" if note else "")
            + f"<h2>Waiting for your tap</h2>{waiting}<h2>Switch</h2>{hot}{switch}{apps_html}{activity_html()}" + TAIL)



class ZeroTrustOnly(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/health":
            return PlainTextResponse("ok")
        claims = await access.who(request.headers)
        if not claims:
            return PlainTextResponse("Not through Zero Trust.", status_code=401, headers=HEADERS)
        request.state.who = str(claims.get("email", "")).lower()
        length = request.headers.get("content-length") or "0"
        if not (length.isascii() and length.isdigit()) or request.headers.get("transfer-encoding"):         # a body must say how long it is, so the size cap cannot be skipped
            return PlainTextResponse("A body must have a plain length.", status_code=411, headers=HEADERS)
        if int(length) > 4096:
            return PlainTextResponse("Too big.", status_code=413, headers=HEADERS)
        if request.method not in ("GET", "HEAD"):
            origin = request.headers.get("origin")
            if origin and urlparse(origin).netloc != request.headers.get("host", ""):
                return PlainTextResponse("Cross-site request refused.", status_code=403, headers=HEADERS)
            ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
            if ctype != "application/x-www-form-urlencoded":
                return PlainTextResponse("Unsupported content type.", status_code=415, headers=HEADERS)
        response = await call_next(request)
        for k, v in HEADERS.items():
            response.headers.setdefault(k, v)
        return response


async def home(request: Request):
    return HTMLResponse(page(request.state.who, NOTES.get(request.query_params.get("n", ""), "")), headers=HEADERS)


def ticket_page(who: str, tid: str) -> str:
    """One ticket on its own page. It never reloads by itself, so the buttons cannot change under a tap."""
    t = consent.ENGINE.get(tid)
    head = HEAD + f"<a class='back' href='/confirm'>{ICONS['back']}<span>Back</span></a>"
    if not t or t.status != "pending":
        return head + f"<h1>Confirm</h1><div class='empty'>{ICONS['inbox']}<span>That ticket is no longer open.</span></div>" + TAIL
    careful = t.risk == "high"
    why = f"<p class='mut why'>Claude says: {e(t.why)}</p>" if t.why else ""
    detail = f"<p class='mut'>{e(t.detail)}</p>" if t.detail else ""
    typed = (f"<label class='mut' for='typed'>To confirm, type <b>{e(t.confirm_word)}</b> exactly:</label>"
             f"<input id='typed' form='ok' name='typed' autocomplete='off' autocapitalize='none' spellcheck='false' required>"
             if t.confirm_word else "")
    minutes = config.allow_all_minutes()
    every = (f"<hr class='sep'><form method='post' action='/confirm/{e(t.id)}/approve-all'><input type='hidden' name='csrf' value='{consent.csrf(t.id, who)}'>"
             f"<button class='quiet'>Confirm and allow all for {minutes} min</button></form>"
             f"<p class='fine'>Allow all: every change Claude asks for runs with no tap, deletes and DNS or route changes too, until the time is up or you press Stop.</p>"
             if minutes and not t.confirm_word else "")
    return (head + f"<h1>Confirm this?</h1><div class='req'><div class='meta'><span class='badge{' hi' if careful else ''}'>{'Careful' if careful else 'Change'}</span>"
            f"<span class='time'>{left(t)}. Reload to see the time.</span></div><div class='sum'>{e(t.summary)}</div>{detail}{why}{typed}"
            f"<div class='row'><form method='post' action='/confirm/{e(t.id)}/deny'><input type='hidden' name='csrf' value='{consent.csrf(t.id, who)}'>"
            f"<button class='stop'>Deny</button></form>"
            f"<form id='ok' method='post' action='/confirm/{e(t.id)}/approve'><input type='hidden' name='csrf' value='{consent.csrf(t.id, who)}'>"
            f"<button class='go'>Confirm</button></form></div>{every}</div>" + TAIL)


async def ticket_view(request: Request):
    return HTMLResponse(ticket_page(request.state.who, request.path_params["tid"]), headers=HEADERS)


async def decide(request: Request, approve: bool):
    who = request.state.who
    tid = request.path_params["tid"]
    form = await request.form()
    if not consent.csrf_ok(tid, who, str(form.get("csrf", ""))):
        return PlainTextResponse("Form token wrong or expired. Go back and reload the page.", status_code=403, headers=HEADERS)
    try:
        consent.ENGINE.decide(tid, approve, who, str(form.get("typed", "")))
        note = "confirmed" if approve else "denied"
    except consent.WrongWord:
        note = "typed"
    except consent.ChangesOff:
        note = "off"
    except consent.ConsentError:
        note = "gone"
    return RedirectResponse(f"/confirm?n={note}", status_code=303)


async def approve_all(request: Request):
    who = request.state.who
    tid = request.path_params["tid"]
    form = await request.form()
    if not consent.csrf_ok(tid, who, str(form.get("csrf", ""))):
        return PlainTextResponse("Form token wrong or expired. Go back and reload the page.", status_code=403, headers=HEADERS)
    t = consent.ENGINE.get(tid)
    if not t or t.confirm_word:                                 # a ticket that asks for a typed word is never part of this button
        return RedirectResponse("/confirm?n=gone", status_code=303)
    try:
        consent.ENGINE.decide(tid, True, who)
    except consent.ChangesOff:
        return RedirectResponse("/confirm?n=off", status_code=303)
    except consent.ConsentError:
        return RedirectResponse("/confirm?n=gone", status_code=303)
    until = consent.start_allow_all()
    if until:
        audit.log("allow all started", by="owner", until=time.strftime("%H:%M", time.localtime(until)))
    return RedirectResponse("/confirm?n=" + ("allall" if until else "allno"), status_code=303)


async def allow_all_stop(request: Request):
    form = await request.form()
    if not consent.csrf_ok("allowall", request.state.who, str(form.get("csrf", ""))):
        return PlainTextResponse("Form token wrong or expired.", status_code=403, headers=HEADERS)
    if consent.stop_allow_all():
        audit.log("allow all stopped", by="owner")
    return RedirectResponse("/confirm?n=allstopped", status_code=303)


async def approve(request: Request):
    return await decide(request, True)


async def deny(request: Request):
    return await decide(request, False)


async def freeze(request: Request):
    form = await request.form()
    if not consent.csrf_ok("freeze", request.state.who, str(form.get("csrf", ""))):
        return PlainTextResponse("Form token wrong or expired.", status_code=403, headers=HEADERS)
    now = not consent.frozen()
    if now:
        consent.set_frozen(True)                  # the memory flag is set first, so nothing new can start while we cancel
        consent.ENGINE.cancel_all("frozen")
    else:
        consent.set_frozen(False)
    audit.log("frozen" if now else "unfrozen", by="owner")
    return RedirectResponse("/confirm?n=" + ("frozen" if now else "unfrozen"), status_code=303)


async def pairing(request: Request):
    form = await request.form()
    if not PROVIDER or not consent.csrf_ok("pairing", request.state.who, str(form.get("csrf", ""))):
        return PlainTextResponse("Refused.", status_code=403, headers=HEADERS)
    PROVIDER.open_pairing(5)
    audit.log("pairing opened", by="owner")
    return RedirectResponse("/confirm?n=pairing", status_code=303)


async def disconnect(request: Request):
    form = await request.form()
    cid = str(form.get("id", ""))
    if not PROVIDER or not consent.csrf_ok("apps", request.state.who, str(form.get("csrf", ""))) or cid not in PROVIDER.approved:
        return PlainTextResponse("Refused.", status_code=403, headers=HEADERS)
    PROVIDER.disconnect(cid, forget=True)
    audit.log("app disconnected", by="owner")
    return RedirectResponse("/confirm?n=disconnected", status_code=303)


def app() -> Starlette:
    return Starlette(middleware=[Middleware(ZeroTrustOnly)], routes=[
        Route("/health", home),
        Route("/", lambda r: RedirectResponse("/confirm")),
        Route("/confirm", home),
        Route("/confirm/{tid}", ticket_view),
        Route("/confirm/{tid}/approve", approve, methods=["POST"]),
        Route("/confirm/{tid}/deny", deny, methods=["POST"]),
        Route("/confirm/{tid}/approve-all", approve_all, methods=["POST"]),
        Route("/allow-all/stop", allow_all_stop, methods=["POST"]),
        Route("/freeze", freeze, methods=["POST"]),
        Route("/pairing", pairing, methods=["POST"]),
        Route("/apps/disconnect", disconnect, methods=["POST"]),
    ])


def start(provider) -> None:
    global PROVIDER
    PROVIDER = provider
    server = uvicorn.Server(uvicorn.Config(app(), host="0.0.0.0" if access.enforcing() else "127.0.0.1", port=config.admin_port(), log_level="warning", access_log=False))
    server.install_signal_handlers = lambda: None
    threading.Thread(target=server.run, name="confirm", daemon=True).start()
