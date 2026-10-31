# Setup on your computer

For when you want to try it, free, with read-only tokens. About 15 minutes. Nothing here can change your server, because the tokens only read and the tool starts frozen.

## Before you start

- A Mac, Linux or Windows computer.
- A running Coolify with its API switched on (**Settings, Advanced, API Access**).
- A Cloudflare account with a domain on it (optional; skip Cloudflare if you only want Coolify).
- An AI app that can add a custom MCP connector over a web address.

Your computer must be able to reach Coolify's API. If Coolify is on a server you can reach by SSH, open a tunnel and leave it running:

```bash
ssh -f -N -L 127.0.0.1:8000:localhost:8000 your-server
```

Then use `http://127.0.0.1:8000` as `COOLIFY_API_URL`.

## 1. Install uv and get the code

Mac and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then:

```bash
git clone https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP
cd Coolify-Cloudflare-MCP
uv sync
```

## 2. Make read-only tokens

1. In Coolify: **Keys & Tokens, API tokens**. Make a token with only the `read` permission. Add `read:sensitive` later only if you need app logs.
2. In Cloudflare: **My Profile, API Tokens, Create Token**, template **Read all resources**, limited to your account and your domain.

## 3. Fill the settings

```bash
cp .env.example .env
```

Open `.env` and fill `COOLIFY_API_URL`, `COOLIFY_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID` and `CLOUDFLARE_READ_TOKEN`. For the login, add a line `LOGIN_PASSPHRASE=` with 12 or more characters (this plain form only works in this local test). Set `READ_ONLY=1` to be extra safe. Leave the edit token, the SSH lines and the tunnel id empty.

## 4. Start it

```bash
uv run python scripts/run-local-test.py
```

You should see a warning that `ACCESS_ENFORCE` is off (test mode) and that both doors listen on `127.0.0.1` only. That is right for a local test.

## 5. Connect your AI app

See [connect-your-ai.md](connect-your-ai.md). The address is `http://localhost:8775/mcp`.

## 6. Check it works

Ask your AI app: *"Show me the status of the ops tools."* It should report Coolify and Cloudflare as ready and changes as frozen. Then ask for a Coolify overview.

## Where things are

Your tokens are in `.env` (never commit it; `.gitignore` already skips it). Login records and the action log are in `./data`.

## Keep it running

The local test stops when you close the terminal. That is fine for a try-out. For always on, use [setup-own-server.md](setup-own-server.md).

## Use it from your phone

Not with this local test. The Claude phone app needs an `https://` address, so use the server setup in [setup-own-server.md](setup-own-server.md). Do not expose the local test to the internet with a tunnel: it runs with Zero Trust off.

## Update

```bash
git pull
uv sync
```

## Remove it

Delete the folder. If you made tokens, delete them in Coolify and Cloudflare.

## What we tested

| Where | Version | What ran |
|---|---|---|
| macOS | Coolify 4.5.x, Python 3.14 | Read tools against a real Coolify and Cloudflare account; tests with pretend services |
| Linux (CI) | Python 3.11 and 3.14 | The test suite |

Windows is not tested.

**What next:** [Connect your AI app](connect-your-ai.md) · [Setup on your own server](setup-own-server.md)
