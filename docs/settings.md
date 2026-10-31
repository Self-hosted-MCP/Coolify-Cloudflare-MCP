# Every setting

Every setting in `.env.example` appears here, and the docs test checks it.

## Where settings come from

Only environment variables. On a server, put them in Coolify's **Environment Variables** page and switch **Is Literal** on for every secret. On your computer, put them in a `.env` file (never commit it); `scripts/run-local-test.py` reads it. Settings are read when used, so there is no config file to edit.

## Required on a server

| Setting | Default | What it does |
|---|---|---|
| `PUBLIC_URL` | `http://localhost:8765` | Claude's door, the address your AI app connects to. Must be `https://` on a server. |
| `CONFIRM_URL` | `http://localhost:8766` | The address of your Confirm page (behind Zero Trust). |
| `LOGIN_HASH` | none | Secret. The hash of your login passphrase. Make it with `sh scripts/hash-passphrase.sh`. |
| `SECRET_KEY` | none | Secret. A long random string that signs the form tokens. |
| `CF_ACCESS_TEAM_DOMAIN` | none | Your Zero Trust team domain, like `yourteam.cloudflareaccess.com`. |
| `CF_ACCESS_AUD` | none | The Audience tag of the Zero Trust application that protects the Confirm page. |
| `CONFIRM_ALLOWED_EMAILS` | none | Comma list. The only emails the Confirm page accepts. |
| `COOLIFY_API_URL` | none | Where the server reaches Coolify's API, without `/api/v1`. |
| `COOLIFY_TOKEN` | none | Secret. A Coolify API token. Start with `read` only. |

## Cloudflare

| Setting | Default | What it does |
|---|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | none | Your Cloudflare account. Not secret. |
| `CLOUDFLARE_ZONE_ID` | none | The zone (domain) the tool may read and change. Not secret. |
| `CLOUDFLARE_READ_TOKEN` | none | Secret. A read-only token ("Read all resources" template), limited to your account and zone. |
| `CLOUDFLARE_ZONE_NAME` | none | The zone's name, like `example.com`. Every change must stay inside it. |
| `CLOUDFLARE_EDIT_TOKEN` | none | Secret. Only for DNS records and the tunnel's routes, only this zone and account. Leave empty to switch Cloudflare changes off. |
| `CLOUDFLARE_TUNNEL_ID` | none | The one tunnel whose routes can be changed. |
| `PROTECTED_HOSTNAMES` | none | Comma list of hosts that need a typed word to change. This server's own doors, Coolify, SSH and the zone are always protected. |
| `ROUTE_BLOCKED_PORTS` | none | Extra ports a route may never point at. SSH, Docker, Coolify and these two doors are always blocked. |
| `ROUTE_ALLOWED_PORTS` | none | Strict mode: when filled, a route may only point at these ports. |

## Terminal (optional)

Leave every `SSH_` line empty to switch the terminal off.

| Setting | Default | What it does |
|---|---|---|
| `SSH_HOST` | none | The server's address. |
| `SSH_PORT` | 22 | Its SSH port. |
| `SSH_USER` | none | A user made just for this tool. Never root and never your own. |
| `SSH_PRIVATE_KEY` | none | Secret. That user's own key. Write new lines as `\n`. |
| `SSH_KNOWN_HOSTS` | none | The server's public key line, so a look-alike machine is refused. |

## Safety

| Setting | Default | What it does |
|---|---|---|
| `READ_ONLY` | 0 | Anything that is not plainly `0`, `false`, `no` or `off` means no change can even be asked for. |
| `ACCESS_ENFORCE` | 1 | Zero Trust on the Confirm page. Stays on unless exactly `0`, `false`, `no` or `off`. Off is only for a local test, and then both doors listen on 127.0.0.1 only. |
| `ALLOWED_REDIRECT_HOSTS` | `claude.ai,claude.com` | The only places a login may send the AI app back to. |
| `LOGIN_PASSPHRASE` | none | For a local test only, and only with `ACCESS_ENFORCE=0`. 12 or more characters. Use `LOGIN_HASH` on a server. |

## Behaviour

| Setting | Default | What it does |
|---|---|---|
| `CONFIRM_WAIT_SECONDS` | 45 | How long a change tool waits for your tap before it hands back the ticket. |
| `CONFIRM_TTL_SECONDS` | 300 | How long a ticket stays open. |
| `UNFREEZE_MINUTES` | 60 | After an Unfreeze, changes freeze again by themselves after this long. 0 means never. |
| `ALLOW_ALL_MINUTES` | 10 | The **Allow all** button lets every change through without a tap for this long. 0 removes the button. |
| `OUTPUT_MAX_CHARS` | 8000 | Cap on the length of an answer. |
| `MAX_LOG_LINES` | 200 | Cap on log lines returned. |
| `RATE_LIMIT_PER_MINUTE` | 30 | Slows down runaway loops. |
| `HTTP_TIMEOUT_SECONDS` | 20 | How long to wait for Coolify or Cloudflare. |
| `ACTION_LOG_MAX_MB` | 2 | Size cap of the action log. The oldest lines go first. |

## Server

| Setting | Default | What it does |
|---|---|---|
| `HOST` | `0.0.0.0` | The address to listen on. |
| `PORT` | 8765 | Claude's door. |
| `ADMIN_PORT` | 8766 | The Confirm page. |
| `DATA_DIR` | `/data` | Where login tokens, the action log and the freeze flag are kept. |
| `TZ` | `UTC` | Time zone of the container. The action log is always written in UTC. |

## Files in the data folder

| File | What it holds |
|---|---|
| `actions.log` | The action log: what was asked, tapped, run or refused. No secret values. |
| `frozen` | Present while changes are frozen. |
| OAuth file | Fingerprints of the logins of your AI apps. Never the tokens themselves. |

**What next:** [Setup on your own server](setup-own-server.md) · [Safety](safety.md)
