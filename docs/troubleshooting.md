# If something goes wrong

For when something does not work. Find what you see, then follow the fix.

**Contents:** [Starting the server](#starting-the-server) · [Connecting your AI app](#connecting-your-ai-app) · [Logging in](#logging-in) · [The Confirm page](#the-confirm-page) · [Tickets](#tickets) · [Coolify](#coolify) · [Cloudflare](#cloudflare) · [The terminal](#the-terminal) · [Still stuck?](#still-stuck)

## Starting the server

**What you see:** `Set LOGIN_HASH (run: coolify-cloudflare-mcp hash)...`
**Why:** The server will not start without a login hash.
**Fix:** Run `sh scripts/hash-passphrase.sh`, copy the hash into `LOGIN_HASH`, and start again. (For a local test only, `LOGIN_PASSPHRASE` with `ACCESS_ENFORCE=0` also works.)

**What you see:** `The Confirm page needs CF_ACCESS_TEAM_DOMAIN, CF_ACCESS_AUD and CONFIRM_ALLOWED_EMAILS...`
**Why:** With Zero Trust enforced, all three settings are required.
**Fix:** Fill them from your Zero Trust application (see [setup-own-server.md](setup-own-server.md), step 3).

**What you see:** `Set SECRET_KEY (a long random string).`
**Fix:** Make one with `openssl rand -hex 32` and set `SECRET_KEY`.

## Connecting your AI app

**What you see:** The Claude app says it cannot connect, or the login fails.
**Why:** The Claude apps refuse sign-in over plain `http://`, and a new app can only connect while pairing is open.
**Fix:** Use an `https://` address for `PUBLIC_URL`, press **Allow a new app** on the Confirm page, then add the connector again within 5 minutes.

**What you see:** Your AI says the tools are not there.
**Fix:** Start a new chat after adding the connector, and switch the connector on for that chat.

## Logging in

**What you see:** Wrong passphrase, or "locked".
**Why:** Wrong tries are limited per login link, per address and overall, and slowed down.
**Fix:** Wait a few minutes, then start the login again from your AI app.

## The Confirm page

**What you see:** "Not through Zero Trust." or a 401.
**Why:** The request did not carry Cloudflare's signed token for your email.
**Fix:** Open the Confirm hostname in your browser and log in through Zero Trust. Check `CF_ACCESS_AUD`, `CF_ACCESS_TEAM_DOMAIN` and `CONFIRM_ALLOWED_EMAILS`.

**What you see:** Buttons do nothing or are refused.
**Fix:** Use the page from its own address, not inside another page or app that hides the referrer.

**What you see:** "Changes are frozen."
**Fix:** That is the starting state. Open the Confirm page and press **Unfreeze**.

## Coolify

**What you see:** A message about a missing Coolify permission.
**Fix:** Logs need `read:sensitive`. Deploys need `deploy`. Settings and variables need `write`. Make the token with the smallest permission that fits.

**What you see:** Coolify cannot be reached.
**Fix:** Check `COOLIFY_API_URL` (no `/api/v1`), that Coolify's API is switched on, and that its **Allowed IPs** setting lets the container in. The default `http://host.docker.internal:8000` needs the `extra_hosts` line in `docker-compose.yml`.

## Cloudflare

**What you see:** "That is not your account or zone."
**Fix:** Check `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID` and `CLOUDFLARE_ZONE_NAME`.

**What you see:** Changes are off for Cloudflare.
**Fix:** Set `CLOUDFLARE_EDIT_TOKEN` and `CLOUDFLARE_TUNNEL_ID`. Without the edit token only reading works.

## Tickets

**What you see:** The tool answers "Waiting for the owner's tap" and the AI stops.
**Why:** You have not tapped yet. The tool waits 45 seconds, then hands back the ticket.
**Fix:** Open the Confirm page, tap **Confirm**, then ask the AI to check the ticket. It uses `ops_result`.

**What you see:** The ticket expired.
**Why:** A ticket stays open for 5 minutes.
**Fix:** Ask the AI to make the change again.

**What you see:** "The word you typed does not match."
**Fix:** Type the word exactly as shown on the ticket, usually the host name.

**What you see:** The result says "result unknown".
**Why:** The call was cut off while the change was running. It is never retried.
**Fix:** Check Coolify or Cloudflare to see whether the change happened, then ask again if needed.

**What you see:** "several changes waiting".
**Fix:** At most 5 tickets can be open. Tap or deny the open ones.

## The terminal

**What you see:** The terminal tools say it is not set up.
**Fix:** Fill every `SSH_` setting. Leave them all empty to switch it off.

**What you see:** The SSH login is refused or the host is not trusted.
**Why:** `SSH_KNOWN_HOSTS` pins the server's own key, and a different key is refused.
**Fix:** Run `ssh-keyscan -t ed25519 your-host`, check the key against the server console, and put the line in `SSH_KNOWN_HOSTS`.

**What you see:** Text arrives wrong or the terminal fails to open.
**Fix:** `tmux` must be 3.0 or newer on the server (`tmux -V`), and the SSH user's shell must be `sh` or `bash`.

**What you see:** `server_numbers` shows an error for Docker.
**Why:** The SSH user is not in the `docker` group. That group is as powerful as root, so leaving it out is safer.
**Fix:** Accept the error, or read [the terminal section of safety.md](safety.md#the-terminal) before changing it.

## Still stuck?

Open a [Something doesn't work](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=bug_report.yml) issue. Include the version (`__version__` in `src/opsmcp/__init__.py`), how you run it, and the exact error. Leave out passwords, keys and private data.
