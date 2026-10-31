# Setup on your own server

Always on, so you can use it from your phone and the Claude website. It runs as one small container next to Coolify, and two Cloudflare tunnel hostnames carry its two doors out.

Do the steps in order and stop if a check fails.

**Contents:** [What you need](#what-you-need) · [Steps 1 to 4](#1-try-it-read-only-on-your-computer-first) · [Deploy with Coolify](#5-deploy-with-coolify) · [Tunnel hostnames](#6-add-the-two-tunnel-hostnames) · [Check it](#7-check-it) · [Add changes](#9-add-changes-only-when-you-want-them) · [Backups](#backups) · [What we tested](#what-we-tested)

## What you need

- A server with Coolify (4.5 was tested) and its API switched on.
- A domain on Cloudflare with a Cloudflare Tunnel already running to that server.
- Cloudflare Zero Trust (check Cloudflare for current plans).
- About an hour.

## 1. Try it read-only on your computer first

Follow [setup-computer.md](setup-computer.md). Check the real answers: `coolify_overview`, `coolify_get`, `coolify_logs`, `coolify_deployments`, `coolify_diagnose`, `ops_status`, `cloudflare_overview` and `cloudflare_routes`. Secrets must show as `***`.

## 2. Choose two hostnames

You need one for Claude's door and one for the Confirm page, for example `ops.example.com` and `confirm.example.com`. Use hard-to-guess names if you like. They are two different addresses on purpose: they need opposite locks.

## 3. Protect the Confirm page

In Cloudflare Zero Trust, make a **self-hosted application** for the Confirm hostname. Add a policy that allows only your own email. Note the application's **Audience tag**: it goes into `CF_ACCESS_AUD`. Your team domain goes into `CF_ACCESS_TEAM_DOMAIN`.

## 4. Make the passphrase hash and secret key

On your computer:

```bash
sh scripts/hash-passphrase.sh
```

It asks for your passphrase and prints only the hash. That is `LOGIN_HASH`. Make `SECRET_KEY` with `openssl rand -hex 32`. Keep both, and the passphrase, in a password manager.

## 5. Deploy with Coolify

1. Make a new Coolify project. Add a resource from a public or private Git repository with build pack **Docker Compose**, pointing at `docker-compose.yml` in this repo (your fork, or this one).
2. Put the variables from `.env.example` into Coolify's **Environment Variables** page. Switch **Is Literal** on for every secret. Use `READ_ONLY=1` and read-only tokens for the first run.
3. `COOLIFY_API_URL` is `http://host.docker.internal:8000` by default (the compose file maps that name to the server). Coolify's API must be on, and its **Allowed IPs** setting must let the container in.
4. Deploy.

## 6. Add the two tunnel hostnames

In the Cloudflare tunnel, add:

- Claude's door: `ops.example.com` to `http://localhost:8765`.
- The Confirm page: `confirm.example.com` to `http://localhost:8766` (the one behind Zero Trust).

Claude's door is public on purpose, with its own passphrase login. If a Cloudflare WAF rule would block Claude's connector, add a skip rule for Claude's door only. Add a Cloudflare rate-limit rule for `/register`, `/authorize` and `/login` on Claude's hostname.

## 7. Check it

Open `https://confirm.example.com/confirm`. You should be asked to log in through Zero Trust, and then see a Frozen page. Try it in a private window with a different email: you must be refused.

## 8. Connect your AI app

Press **Allow a new app** on the Confirm page, then add the connector. See [connect-your-ai.md](connect-your-ai.md).

## 9. Add changes only when you want them

- **Deploy and restart:** make a Coolify token with `deploy` (add `write` only for settings and variables). Never use `root`. Add `read:sensitive` only if you need app logs.
- **Cloudflare changes:** make a second token with DNS Edit for your domain and Cloudflare Tunnel Edit for the account, nothing else. Put it in `CLOUDFLARE_EDIT_TOKEN`, then set `CLOUDFLARE_ZONE_NAME` and `CLOUDFLARE_TUNNEL_ID`. Test on a throwaway host name first. A bad change to a protected host can cut off your own access; the Cloudflare audit log shows what changed and the dashboard is the way back.
- **Terminal:** only if you really want a shell on your server. Make a NEW user (not root, not you), install `tmux` 3.0 or newer, make an SSH key just for it, and fill the `SSH_` settings with the server's own public key line in `SSH_KNOWN_HOSTS`. The `server_numbers` check needs the `docker` group, and that group is as powerful as root. Read [the terminal section of safety.md](safety.md#the-terminal) first.

Then set `READ_ONLY=0` and redeploy. The server still starts frozen: unfreeze on the Confirm page when you want changes.

## Behind your own reverse proxy

The compose file publishes both ports on `127.0.0.1` only. Point your proxy or tunnel at them. Never publish port 8766 to the internet without Zero Trust in front.

## Backups

Back up the `data` volume (login records and the action log). Coolify's own backups are separate.

## Update, stop or remove it

See [updates.md](updates.md). To stop it, stop the app in Coolify. To remove it, delete the app and its volume, and delete the tokens and the SSH key.

## Open points worth knowing

- `host.docker.internal` also reaches other ports published on the server. Give the Coolify token only the abilities it needs, never `root`.
- Run `uvx pip-audit` before deploying and when you update.
- The Claude apps may not wait for your tap. The default wait is 45 seconds, and then Claude uses `ops_result` to check the ticket later.

## What we tested

| Where | Version | What ran |
|---|---|---|
| Ubuntu server with Docker | Coolify 4.5.3 | Deploy next to Coolify, read tools, a restart through a Confirm tap, a Deny, Freeze and unfreeze |
| Cloudflare | Zero Trust | Tunnel routes, an Access-protected Confirm page |

Cloudflare changes (DNS records and routes) and the terminal are covered by tests with pretend services, but were not run against a live account in this release.

**What next:** [Connect your AI app](connect-your-ai.md) · [Safety](safety.md) · [Updates](updates.md)
