<h1 align="center">Coolify-Cloudflare-MCP</h1>

<p align="center"><b>Let your AI look at your Coolify server and your Cloudflare freely, and change things only after you tap Confirm.<br>Works with Claude and any MCP app. Self-hosted, private, you stay in control.</b></p>

<p align="center">
<a href="#credits"><img src="https://img.shields.io/badge/-open%20source-brightgreen" alt="Open source"></a>
<a href="https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/stargazers"><img src="https://img.shields.io/github/stars/Self-hosted-MCP/Coolify-Cloudflare-MCP?style=flat" alt="GitHub stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License: Apache-2.0"></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"></a>
<a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-server-black" alt="MCP server"></a>
<a href="docs/connect-your-ai.md"><img src="https://img.shields.io/badge/works%20with-any%20MCP%20app-orange" alt="Works with any MCP app"></a>
<a href="#choose-how-to-run-it"><img src="https://img.shields.io/badge/self--hosted-computer%20%C2%B7%20own%20server-green" alt="Self-hosted"></a>
</p>

<p align="center">
<a href="https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/actions/workflows/tests.yml"><img src="https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
<a href="https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/releases/latest"><img src="https://img.shields.io/github/v/release/Self-hosted-MCP/Coolify-Cloudflare-MCP" alt="Latest release"></a>
<a href="https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/commits/main"><img src="https://img.shields.io/github/last-commit/Self-hosted-MCP/Coolify-Cloudflare-MCP" alt="Last commit"></a>
</p>

<p align="center"><b>Free and open source under the Apache-2.0 license.</b> Use it, fork it and change it, and keep the credit. See <a href="#credits">Credits</a>.</p>

<p align="center">
<a href="#quick-start-about-15-minutes">Quick start</a> ·
<a href="#choose-how-to-run-it">Ways to run it</a> ·
<a href="docs/connect-your-ai.md">Connect your AI app</a> ·
<a href="#safety-and-privacy">Safety and privacy</a> ·
<a href="docs/examples.md">Things to ask</a> ·
<a href="#all-the-guides">All guides</a>
</p>

<details>
<summary><b>Table of contents</b></summary>

- [Safety and privacy](#safety-and-privacy)
- [How it works, in one picture](#how-it-works-in-one-picture)
- [Words you'll see](#words-youll-see)
- [Choose how to run it](#choose-how-to-run-it)
- [What it can do](#what-it-can-do)
- [Quick start (about 15 minutes)](#quick-start-about-15-minutes)
- [All the guides](#all-the-guides)
- [Not supported yet](#not-supported-yet)
- [Help and feedback](#help-and-feedback)
- [Contributors](#contributors)
- [Credits](#credits)

</details>

> [!NOTE]
> Works with [Coolify](https://coolify.io) and [Cloudflare](https://www.cloudflare.com). Not made by or affiliated with Coolify or Cloudflare.

Coolify-Cloudflare-MCP is a small server you run yourself. It gives your AI app two things. First, a free look at everything: your apps, deployments, logs, DNS records, tunnels and rule sets. Second, a way to ask for changes, like a deploy, a restart or a new DNS record. A change never happens because the AI asked. It becomes a **ticket**, and nothing runs until you open your own **Confirm page** and tap **Confirm**.

This is for people who run apps on their own server with Coolify and keep their domains on Cloudflare, and who want an AI to help check on things from a laptop or a phone without handing it the keys.

```
You: Why is my "blog" app showing as unhealthy?
AI:  It crashed 4 minutes ago. The last deployment log ends with "Error: port 3000 already in use".
     I can restart it. That needs your tap on the Confirm page.

You: Yes, restart it.
AI:  I made ticket T-4821: "Restart app blog". Open your Confirm page and tap Confirm.
     (you tap Confirm)
AI:  Done. The blog is running again and the health check is green.
```

## Safety and privacy

> [!WARNING]
> This server can change a real server and a real Cloudflare account. The safety comes from the Confirm page, so **read every ticket before you tap**, and start with the read-only tokens. Read [docs/safety.md](docs/safety.md) first.

- **Looking is free, changing is a ticket.** Every change waits for your tap on a separate page. One tap, one action, never a batch.
- **The AI never writes the ticket.** The server builds the text from checked arguments, so the AI cannot hide what a change really does.
- **Frozen on request.** One button on the Confirm page freezes every change, and `READ_ONLY=1` removes the ability to even ask.
- **Secrets stay hidden.** Passwords, tokens and keys show as `***` in answers and logs. No tool takes a password.
- **Two locks on the Confirm page.** It sits behind Cloudflare Zero Trust, and the server checks the signed token and your email itself.
- **Small, fenced reach.** Cloudflare changes cover only DNS records and one tunnel's routes, only inside one zone, and always with a separate edit token. Coolify cannot delete apps through this tool.
- **Nothing collected.** No account, no cloud service of ours, no tracking. The only outside calls go to your own Coolify and to Cloudflare's API.
- **You see everything.** One action log records what was asked, tapped, run or refused, without secret values.
- **Not a sandbox.** If you switch on the optional terminal, it is a real shell on your server. Read [the honest section](docs/safety.md#the-terminal-honestly).

More in [docs/safety.md](docs/safety.md), [docs/privacy.md](docs/privacy.md) and [docs/threat-model.md](docs/threat-model.md).

## How it works, in one picture

```
Your AI app (Claude, ...)
   │  MCP over HTTPS, passphrase login
   ▼
Door 1: Coolify-Cloudflare-MCP (port 8765)  ──►  Coolify API   (apps, logs, deploys)
   │                                        ──►  Cloudflare API (DNS, tunnels, rule sets)
   │ a change becomes a ticket              ──►  SSH, optional   (terminal on the server)
   ▼
Door 2: Confirm page (port 8766, behind Zero Trust)  ◄──  you, on your phone or computer
```

More in [docs/how-it-works.md](docs/how-it-works.md).

## Words you'll see

| Word | What it means here |
|---|---|
| **Ticket** | A change waiting for your tap. It says exactly what will happen. |
| **Confirm page** | Your own web page where you tap Confirm or Deny on a ticket. |
| **Frozen** | No change can run. The server starts frozen, and you unfreeze it on the Confirm page. |
| **Typed word** | For risky tickets (deletes, tunnel routes) you must also type a word, like the host name. |
| **Coolify** | A self-hosted platform for running apps on your own server. |
| **Zero Trust** | Cloudflare's login gate. It keeps strangers away from the Confirm page. |
| **AI app** | Claude or any app that can use tools through MCP. |
| **MCP** | Model Context Protocol: how AI apps plug into tools like this one. |

## Choose how to run it

| Way | Where it runs | On your phone | Cost | Guide |
|---|---|---|---|---|
| **1. Your computer (test)** | Mac, Windows or Linux, read-only try-out | No | Free | [setup-computer.md](docs/setup-computer.md) |
| **2. Your own server** | The same server as Coolify, in Docker, behind a Cloudflare tunnel | Yes, always on | Free (your server) | [setup-own-server.md](docs/setup-own-server.md) |

> [!CAUTION]
> The server version has a public address that Claude connects to, plus a Confirm page behind Zero Trust. A wrong Cloudflare setup could expose the Confirm page. Follow [setup-own-server.md](docs/setup-own-server.md) in order and stop if a check fails.

> [!TIP]
> Not sure? Start with **1**: nothing leaves your computer except calls to your own Coolify and Cloudflare. Using an AI coding agent like Claude Code? [AGENTS.md](AGENTS.md) explains the project to it.

## What it can do

40 tools in two groups. All of them are listed in [docs/tools.md](docs/tools.md).

**Look (free, nothing changes)**
- **Coolify:** overview of apps, services and databases, one resource's details, environment variable names (never values), logs, deployments and their build logs, what looks unhealthy, servers, registries, volumes, scheduled tasks and backups.
- **Cloudflare:** DNS records, rule sets, tunnels and their routes, Zero Trust apps, and a short list of other read-only paths.
- **Server (optional, over SSH):** disk, memory, load and Docker space, and what a terminal shows.
- **This tool:** its own status and its action log.

**Change (each one is a ticket that needs your tap)**
- **Coolify:** deploy, start, stop or restart, cancel a deployment, set an environment variable, change one setting, roll back, clean up Docker, run a backup or a scheduled task.
- **Cloudflare:** create, change or delete one DNS record, add, change or remove one tunnel route.
- **Terminal (optional):** open one, type into it, close it.

## Quick start (about 15 minutes)

This is the safe try-out on your computer, with read-only tokens. For the real thing on a server, see [setup-own-server.md](docs/setup-own-server.md).

1. Install [uv](https://docs.astral.sh/uv/), then get the code:

   ```bash
   git clone https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP
   cd Coolify-Cloudflare-MCP
   uv sync
   ```

2. Make a Coolify API token with only the `read` permission, and a Cloudflare token from the "Read all resources" template. Copy `.env.example` to `.env` and fill in the read-only values. [docs/setup-computer.md](docs/setup-computer.md) shows each step.

3. Start it:

   ```bash
   uv run python scripts/run-local-test.py
   ```

   You should see the server start on `127.0.0.1`. It starts frozen, so nothing can change.

4. Connect your AI app. See [docs/connect-your-ai.md](docs/connect-your-ai.md).

5. Ask your AI app: *"Give me an overview of my Coolify apps."*

## All the guides

| Guide | Read it when |
|---|---|
| [Setup on your computer](docs/setup-computer.md) | You want to try it, free, with read-only tokens |
| [Setup on your own server](docs/setup-own-server.md) | You want it always on, next to Coolify |
| [Connect your AI app](docs/connect-your-ai.md) | It's running and you want to use it in your app |
| [Things to ask](docs/examples.md) | You want ideas |
| [Every tool](docs/tools.md) | You want to know what the AI can do |
| [Every setting](docs/settings.md) | You want to change how it behaves |
| [Safety](docs/safety.md) | Before you let an AI change anything |
| [Undo and backups](docs/undo-and-backups.md) | You want to take a change back, or back things up |
| [Threat model](docs/threat-model.md) | You want to know what it protects against, and what not |
| [Privacy](docs/privacy.md) | You want to know what is kept and where |
| [How it works](docs/how-it-works.md) | You want to know how it works inside |
| [Function-by-function check](docs/verification.md) | You want to see how much of the code the tests run |
| [Updates](docs/updates.md) | You want the newest version |
| [Questions people ask](docs/faq.md) | You have a quick question |
| [Troubleshooting](docs/troubleshooting.md) | Something doesn't work |
| [Roadmap](docs/roadmap.md) | You want to know what's planned |
| [SECURITY.md](SECURITY.md) | You found a security problem |
| [CHANGELOG.md](CHANGELOG.md) | You want to know what changed in each version |
| [CONTRIBUTING.md](CONTRIBUTING.md) | You want to report a bug or send a fix |
| [CONTRIBUTORS.md](CONTRIBUTORS.md) | You want to see who helped, or be added |
| [GOVERNANCE.md](GOVERNANCE.md) | You want to know how decisions are made |
| [SUPPORT.md](SUPPORT.md) | You need help and don't know where to ask |
| [AGENTS.md](AGENTS.md) | You (or your AI coding agent) want to change the code or set it up |
| [.env.example](.env.example) | You want every setting in one file |

## Not supported yet

- **Creating and deleting apps, services and databases.** Each type needs its own careful design. Use the Coolify dashboard.
- **Cloudflare changes outside DNS records and tunnel routes.** Zero Trust, WAF and R2 changes can lock you out, so the Cloudflare dashboard is the right place.
- **Reload Compose.** Coolify has no clear API call for it.
- **Traffic and security graphs.** They use a different Cloudflare API.
- **Hosting-company one-click deploys and a Claude Desktop extension.** The server needs a tunnel and Zero Trust, so these do not fit yet.

## Help and feedback

| You want to | Go to |
|---|---|
| Fix a problem yourself | [Troubleshooting](docs/troubleshooting.md) |
| Report a bug | [Something doesn't work](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=bug_report.yml) |
| Ask a question or share an idea | [Question or idea](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=question.yml) |
| Report a security problem, privately | [Private report](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/security/advisories/new) ([SECURITY.md](SECURITY.md)) |

Issues are public, so leave out passwords, keys and private data.

## Contributors

Thank you to everyone who helped. Code, bug reports, ideas, docs and design all count. See [CONTRIBUTORS.md](CONTRIBUTORS.md), and add yourself when you send a pull request.

## Credits

Coolify-Cloudflare-MCP was made by [Self-hosted-MCP](https://github.com/Self-hosted-MCP). Coolify and Cloudflare are trademarks of their owners; this project isn't made by or affiliated with them.

You're welcome to use, fork, change and build on it under the Apache License 2.0 (Apache-2.0) and the notices in [NOTICE](NOTICE). In short:

- Keep [LICENSE](LICENSE), [NOTICE](NOTICE) and the copyright lines.
- Mark your version as changed.

GitHub's "Cite this repository" button uses [CITATION.cff](CITATION.cff).

## No warranty

Coolify-Cloudflare-MCP is free software you run yourself. It comes as is, with no warranty: you use it at your own risk, and no author is responsible for lost or damaged data, or for changes you confirm (the [license](LICENSE) says so in full). Keep a backup anyway.

## License

[Apache License 2.0](LICENSE) (Apache-2.0), with the notices in [NOTICE](NOTICE). Copyright 2026 Self-hosted-MCP and Coolify-Cloudflare-MCP contributors.
