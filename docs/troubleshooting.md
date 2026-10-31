# If something goes wrong

Find what you see, then follow the fix.

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

## Still stuck?

Open a [Something doesn't work](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=bug_report.yml) issue. Include the version (`__version__` in `src/opsmcp/__init__.py`), how you run it, and the exact error. Leave out passwords, keys and private data.
