# Questions people ask

Quick answers, grouped. The first sentence answers; a link goes deeper.

**Contents:** [The basics](#the-basics) · [Your data and safety](#your-data-and-safety) · [Compatibility](#compatibility) · [Running it](#running-it) · [Passwords and keys](#passwords-and-keys) · [Still have a question?](#still-have-a-question)

## The basics

<details>
<summary><b>Is it free?</b></summary>

Yes. The software is free and open source (Apache-2.0). You run it on a server you already have. Your AI app may need its own plan.

</details>

<details>
<summary><b>Do I need to know how to code?</b></summary>

No code, but you do need to make API tokens and set environment variables in Coolify and Cloudflare. [Setup on your computer](setup-computer.md) is a safe first step, and your AI coding agent can walk you through it with [AGENTS.md](../AGENTS.md).

</details>

<details>
<summary><b>What does it actually do?</b></summary>

It gives your AI a free look at Coolify (apps, deployments, logs) and Cloudflare (DNS, tunnels, rule sets). When the AI wants to change something, it makes a ticket and waits for your tap on a separate page. See [how-it-works.md](how-it-works.md).

</details>

<details>
<summary><b>Who is it for?</b></summary>

People who run apps on their own server with Coolify and keep their domains on Cloudflare, and want an AI to help from a laptop or a phone.

</details>

<details>
<summary><b>Is it made by Coolify or Cloudflare?</b></summary>

No. It is not made by or affiliated with Coolify or Cloudflare. Their names are trademarks of their owners and are used only to say what this works with.

</details>

<details>
<summary><b>Does it send my data anywhere?</b></summary>

No. Nothing is collected, there is no account and no tracking. It calls your own Coolify, Cloudflare's API, and your server over SSH if you switch the terminal on. See [privacy.md](privacy.md).

</details>

## Your data and safety

<details>
<summary><b>What if the AI gets it wrong?</b></summary>

It cannot change anything alone. Every change is a ticket you read and tap. If you tap something wrong, roll back from Coolify or fix the record in Cloudflare. See [undo-and-backups.md](undo-and-backups.md).

</details>

<details>
<summary><b>Can I undo a change?</b></summary>

There is no undo button. Many changes can be reversed by hand: roll back a deploy, delete a record, put a setting back. Each ticket shows the old and new value for settings and DNS records, so you know what to put back. See [undo-and-backups.md](undo-and-backups.md).

</details>

<details>
<summary><b>What can the AI not do?</b></summary>

It cannot delete apps, services or databases, change commands, Dockerfiles, labels or git addresses, or change Cloudflare outside DNS records and one tunnel's routes. See [tools.md](tools.md).

</details>

<details>
<summary><b>Can the AI see my passwords and tokens?</b></summary>

No tool takes or returns one. Environment variable values are never listed, and secret-looking text is shown as `***`. Hiding is best effort, so start with a `read` Coolify token. See [safety.md](safety.md).

</details>

<details>
<summary><b>What does "Allow all" do?</b></summary>

A button on a ticket page. While its window is on (10 minutes by default, set by `ALLOW_ALL_MINUTES`), new tickets are approved without a tap, deletes included. It is not offered on tickets that need a typed word, and Freeze ends the window at once. It lives in memory only, so a restart ends it too. If you never want it, set `ALLOW_ALL_MINUTES=0`.

</details>

<details>
<summary><b>How do I stop everything right now?</b></summary>

Press **Freeze** on the Confirm page. For a harder stop, set `READ_ONLY=1`, delete the tokens, remove the SSH key, or stop the app in Coolify.

</details>

<details>
<summary><b>Who can open the Confirm page?</b></summary>

Only people who pass Cloudflare Zero Trust with an email on `CONFIRM_ALLOWED_EMAILS`. The server checks Cloudflare's signed token itself, so a wrong Zero Trust rule is not enough to get in.

</details>

<details>
<summary><b>Can a website press my Confirm buttons?</b></summary>

No. Each ticket has its own page and buttons, with a form token tied to you and the ticket, same-origin checks, no scripts and no framing.

</details>

<details>
<summary><b>What happens if someone steals my AI app's login?</b></summary>

They can read what the read tools read, but they cannot change anything without your tap on the Confirm page. Delete the token, change the passphrase and reconnect.

</details>

<details>
<summary><b>Has the code been audited?</b></summary>

Not by anyone outside the project. It had three rounds of review by separate AI agents and every finding was fixed with a test. See [threat-model.md](threat-model.md).

</details>

<details>
<summary><b>What is the terminal, and is it safe?</b></summary>

An optional shell on your server over SSH, in tmux. It is the strongest tool here, because whatever the SSH user can do, typed text can do. Every keystroke batch is a ticket you read. Leave it off unless you want it. See [safety.md](safety.md#the-terminal-honestly).

</details>

## Compatibility

<details>
<summary><b>Which AI apps work with it?</b></summary>

It was built for the Claude apps and tested there. Any app that can add a remote MCP server over streamable HTTP with OAuth should work. See [connect-your-ai.md](connect-your-ai.md).

</details>

<details>
<summary><b>Does it work on the Claude phone app?</b></summary>

Yes, once you add it as a connector on the Claude website. Connectors added there show up in the phone app. You need the server version over `https://`.

</details>

<details>
<summary><b>Which Coolify versions work?</b></summary>

Tested on Coolify 4.5.3. Other 4.x versions may work. If an answer from Coolify does not match, please open an issue.

</details>

<details>
<summary><b>Does it work without Cloudflare?</b></summary>

Coolify reading and changes work with no Cloudflare settings. The Cloudflare tools need the account, zone and token settings. The Confirm page itself needs Cloudflare Zero Trust unless you run the local test.

</details>

<details>
<summary><b>Does it work on Windows?</b></summary>

The server runs in Docker on a Linux server. The local test on Windows is not tested.

</details>

<details>
<summary><b>Does it need Docker?</b></summary>

On a server, yes: the setup uses Docker Compose through Coolify. On your computer for the test, no: it runs with `uv`.

</details>

## Running it

<details>
<summary><b>Computer or server?</b></summary>

Computer for a read-only try-out. Server for the real thing, so it is always on and works from your phone.

</details>

<details>
<summary><b>Why two addresses?</b></summary>

The AI app's door must be reachable by the AI app. The Confirm page must only be reachable by you. They need opposite locks.

</details>

<details>
<summary><b>What does it cost to run?</b></summary>

About 100 MB of memory and under 1% of a processor. The container is limited to 256 MB and half a processor.

</details>

<details>
<summary><b>How do I update it?</b></summary>

Pull the new code and redeploy the app in Coolify. See [updates.md](updates.md).

</details>

<details>
<summary><b>How do I remove it?</b></summary>

Delete the app and its volume in Coolify, delete the tokens and the SSH key, and remove the connector from your AI app. See [privacy.md](privacy.md#deleting-everything).

</details>

<details>
<summary><b>Where do I report a bug or a security problem?</b></summary>

Bugs go in an [issue](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=bug_report.yml). Security problems go in a private report: [SECURITY.md](../SECURITY.md).

</details>

<details>
<summary><b>Can I run more than one copy?</b></summary>

Run exactly one. Open tickets and the Allow all window live in memory, so a second copy would not know about them.

</details>

<details>
<summary><b>Which languages does it speak?</b></summary>

English only. The Confirm page and the tool texts are in English. Not supported yet.

</details>

## Passwords and keys

<details>
<summary><b>Where do my tokens live?</b></summary>

In environment variables in Coolify with **Is Literal** on. Never in files, commits, notes or chats.

</details>

<details>
<summary><b>How do I make the login hash?</b></summary>

Run `sh scripts/hash-passphrase.sh`. It asks for your passphrase and prints only the hash, which goes into `LOGIN_HASH`.

</details>

<details>
<summary><b>What if I forget the passphrase?</b></summary>

Make a new hash with the same script, put it into `LOGIN_HASH`, redeploy, and log in again from your AI app.

</details>

<details>
<summary><b>Which Coolify permissions does it need?</b></summary>

`read` to look. `read:sensitive` only if you want app logs. `deploy` for deploys and restarts. `write` only for settings and variables. Never `root`.

</details>

## Still have a question?

Open a [Question](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=question.yml).
