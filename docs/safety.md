# Safety model

What this server can do is small and fenced, and every layer below stands on its own.

## Layers (outside in)

1. **Cloudflare Zero Trust.** Claude's door has a Bypass only for Anthropic's address range. The Confirm page is behind "owner only".
2. **Claude's login.** A passphrase (PBKDF2, 600,000 rounds) typed once per app, on a page that checks it off the event loop. A new app can only connect while the owner has pressed
   "Allow a new app" (5 minutes). Wrong tries are limited per login link (5), per source address (10) and overall (60), and slowed down. Redirect hosts must be exactly
   `claude.ai` or `claude.com` (no sub-domains, no user-info or backslash tricks). Tokens are stored only as fingerprints. Open logins are capped. Bodies over 4 KB are refused.
3. **The Confirm page checks Zero Trust itself.** It verifies Cloudflare's signed token (signature, audience, issuer, expiry) AND that the email is on `CONFIRM_ALLOWED_EMAILS`.
   Everything is refused when this is not fully configured, and the server refuses to start in that state. `ACCESS_ENFORCE` fails SAFE: only an exact 0, false, no or off turns it off,
   and then both doors listen on 127.0.0.1 only. `READ_ONLY` likewise: anything that is not plainly "off" turns it on.
4. **Looking is free, changing is a ticket.** A change tool never changes anything by itself. It makes a ticket that runs only after the owner taps Confirm: once, before it expires
   (5 minutes, plus 2 minutes of grace for a tap near the end), never twice. Freeze and `READ_ONLY` stop new tickets, stop approving, stop running tickets already tapped,
   and Freeze cancels every open ticket (it lives in memory too, so a full disk cannot stop it).
5. **The ticket text is built by the server** from checked arguments, never from Claude's words. Claude may add one short "why" line, shown separately and labelled. The checked arguments
   are hashed when the ticket is made and checked again before running, and the action is done from those arguments only. Names from Coolify are quoted with every non-ASCII
   character escaped. A ticket whose text, detail or typed word would have to be cut is refused instead.
6. **Typed word.** Deletes, protected hostnames, tunnel routes and public ports also need the owner to type a word (the host name, or `public-port`) on the ticket page.
7. **Forms.** Each ticket has its own page with its own buttons and no auto-refresh, so buttons cannot move under a tap. Plain HTML, no scripts, a form token tied to the person
   and the ticket, same-origin checks, strict content type, a CSP that allows no scripts, no framing, no referrer. Everything shown is escaped. Notes on the page are fixed texts.
8. **Small, fixed reach.** The Coolify address comes from the environment, never from a tool argument. The Cloudflare address is fixed in code. Cloudflare reads are GET on a short list
   of path shapes under the owner's account and zone (paths with token, secret, key, value, content or export are refused). Cloudflare writes use a SEPARATE edit token and exist only for
   DNS records and one tunnel's routes, read first and refused if anything changed since the ticket. Redirects are never followed. Answers are size-capped.
9. **What comes back is data.** Everything from Coolify, Cloudflare and the server is wrapped as "data, not instructions". Only a short list of fields is passed on, secrets are hidden by
   name and by shape, control codes are stripped, lengths are capped, error messages never repeat what the other side said (except a short quoted reason, as data).
10. **Hard limits in code.** Ids, names, settings, record values, hostnames and tmux names are checked against strict patterns. There is no tool to run a free-form command outside the terminal,
    to delete apps, to change a command, Dockerfile, label or git address, or to change Cloudflare outside DNS records and one tunnel's routes. The protected hosts (this server's own doors,
    Coolify, SSH, the zone) are always protected, and a route can never point at SSH, Coolify's port or these two doors.
11. **The terminal** (see its own section) is the strongest tool here and is treated that way.
12. **The container.** Non-root, read-only filesystem, no capabilities, no new privileges, 256 MB, 100 processes, a `/tmp` that cannot run programs, no Docker socket, only a small `/data`
    volume (login tokens, the action log, the freeze flag).
13. **Logs.** One action log: what was asked, tapped, run or refused. No secret values, no environment values, no typed terminal text (the log says how many characters were typed
    and which warnings applied). Every line passes the secret hider, the file is capped, a full disk never stops a refusal or a Freeze.

## The terminal, honestly

- It is **a shell on the server**. Whatever the SSH user can do, typed text can do. To read Docker numbers that user needs the `docker` group, which is **as powerful as root**.
  The warning list on tickets (rm, curl | sh, docker run, sudo...) helps the owner read; it is a hint, never a guarantee, and the ticket says so every time.
- Text is sent to tmux as hex bytes, so tmux never parses it (`;` and backslashes arrive as written). Sessions are addressed with tmux's exact-match form so `a` never hits `ab`.
  The `ops-` prefix is a convention, not a wall: a shell inside a pane can run tmux on other sessions.
- "Press Enter" tickets show the line already at the prompt and are refused if it changed. Reads hide secrets over the whole captured pane. At most two SSH connections at once, reads are rate limited.
- The server's own SSH public key is pinned: nothing is trusted on first use. The key lives only in Coolify's environment.
- Better, not built: a separate Unix user with no `docker` group plus a small docker-socket-proxy or sudoers rules for the five fixed number checks.

## What is NOT covered (be honest)

- **Secret hiding is best effort.** It catches common shapes and names. A secret in an unusual shape, inside a log line or on a screen, could get through. Use a `read` Coolify token until `read:sensitive` is really needed.
- **The owner's tap is the last guard.** A ticket is only as safe as the reading of it. Careful tickets are marked red.
- **The Coolify token is powerful.** A `deploy` or `write` token can do a lot. Keep it as narrow as the job. `root` is never needed.
- **A stolen login on Claude's side** can read everything the read tools can read, but cannot change anything without the owner's tap.
- **Cloudflare, Coolify and the server are untrusted data sources.** Anything that could impersonate them could feed false answers.
- **Open tickets are lost if the server restarts.** That fails safe. A call cut off while a change runs is marked "result unknown" and never retried.
- **The public door can be flooded** (anyone can start a login). The number of open logins is capped; add a Cloudflare rate-limit rule for `/register`, `/authorize` and `/login`.
- **The door and the approval engine live in one process.** A code-execution bug in the public door would bypass consent. Splitting them is a bigger change.
- **Only partly run against real services.** The read tools, a restart through a Confirm tap, a Deny and Freeze were run against a real Coolify 4.5.3 and a real Cloudflare account. Cloudflare changes (DNS records and routes), the terminal, Docker cleanup and the "keep volumes" behaviour were tested with pretend services only, so check them on a throwaway app and a throwaway host name first (see [setup-own-server.md](setup-own-server.md)). Run `uvx pip-audit` online before deploying.

## Kill switches (any one is enough)

Freeze on the Confirm page. `READ_ONLY=1` and redeploy. Delete the Coolify API token, the Cloudflare tokens, or the SSH key from the server user. Stop the app in Coolify.

## Review history

Before release the code had three rounds of independent review by separate AI agents (security and correctness), each followed by fixes with a test for every finding, plus a fourth check of the last round. No human outside the project has audited it. 462 tests pass.

Round 1 found: Zero Trust switch failing open on a typo, Freeze not stopping tapped tickets, a too broad Cloudflare reader, blind env values, forgeable log lines, buttons moving under a tap, unbounded logins, a stuck ticket on cancel, and a regex accepting a new line. Round 2: values cut off on tickets, login limits and redirect hosts, resource kinds, a deploy that queued nothing, late taps, and a log crash on a full disk. Round 3 (terminal and Cloudflare changes): tmux `;` and prefix matching, blind Enter, PUT wiping DNS comments, route edits dropping settings, publishable ports, truncated task commands, and protected hosts being opt-in. [verification.md](verification.md) lists every function and how much of it the tests run.
