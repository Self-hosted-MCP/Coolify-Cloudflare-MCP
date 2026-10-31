# Connect your AI app

This server speaks MCP over HTTPS with a passphrase login. Any AI app that can add a custom MCP connector by web address can use it. Each section below says what you need, the steps, and how to check it.

## Before you start

Run the server first: [setup-computer.md](setup-computer.md) for a local try-out or [setup-own-server.md](setup-own-server.md) for the real thing. Open your Confirm page and press **Allow a new app**. A new app can only connect for 5 minutes after you press it, so a stranger cannot connect even with your passphrase.

## Claude website, desktop and phone app

Needs the server version over `https://`. These apps refuse sign-in over plain http.

1. Go to **Settings, Connectors, Add custom connector**.
2. Paste `https://your-ops-address/mcp` (Claude's door).
3. A login page opens. Type your passphrase.
4. Check: ask *"Show me the ops status."* It should list Coolify, Cloudflare and whether changes are frozen.

Connectors added on the website also show up in the phone app.

## Claude Code

For the local try-out:

```bash
claude mcp add --transport http coolify-cloudflare http://localhost:8775/mcp
```

For a server, use its `https://` address. Check: run `claude mcp list` and ask for the ops status.

## Other MCP apps (ChatGPT, Codex, Cursor, VS Code, Gemini CLI)

Any app that supports a remote MCP server over streamable HTTP with OAuth should work: add the `/mcp` address and log in with your passphrase. Not tested with these apps. If you try one, please tell us in a [Question](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=question.yml).

## When a change is asked

Your AI app shows you the ticket text and the Confirm page address. Open the Confirm page, read the ticket, and tap **Confirm** or **Deny**. Then ask the AI to check the result, or wait: it checks with `ops_result`.
