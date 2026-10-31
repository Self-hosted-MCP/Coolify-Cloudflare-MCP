# Questions people ask

Quick answers.

## The basics

<details>
<summary><b>Is it free?</b></summary>

Yes. The software is free and open source (Apache-2.0). You run it on a server you already have. Your AI app may need its own plan.

</details>

<details>
<summary><b>Do I need to know how to code?</b></summary>

You need to be comfortable making API tokens and setting environment variables in Coolify and Cloudflare. [Setup on your computer](setup-computer.md) is a safe first step.

</details>

<details>
<summary><b>Does it send my data anywhere?</b></summary>

No. Nothing is collected, there is no account and no tracking. It calls your own Coolify, Cloudflare's API, and your server over SSH if you switch the terminal on. What your AI app reads goes to the company that runs your AI app. See [privacy.md](privacy.md).

</details>

<details>
<summary><b>Which AI apps work with it?</b></summary>

It was built for the Claude apps and tested there. Any app that can add a remote MCP server over streamable HTTP with OAuth should work. See [connect-your-ai.md](connect-your-ai.md).

</details>

## Your data and safety

<details>
<summary><b>What if the AI gets it wrong?</b></summary>

It cannot change anything alone. Every change is a ticket you read and tap. If you tap something wrong, roll back from Coolify or fix the record in Cloudflare.

</details>

<details>
<summary><b>Can the AI see my passwords?</b></summary>

No tool takes or returns one. Environment variable values are never listed, and secret-looking text is shown as `***`. Hiding is best effort, so start with a `read` Coolify token. See [safety.md](safety.md).

</details>

<details>
<summary><b>What can it not do?</b></summary>

It cannot delete apps, change commands, Dockerfiles or git addresses, or change Cloudflare outside DNS records and one tunnel's routes. See [tools.md](tools.md).

</details>

<details>
<summary><b>What does "Allow all" do?</b></summary>

A button on a ticket page. While its window is on (10 minutes by default, set by `ALLOW_ALL_MINUTES`), new tickets are approved without a tap, deletes included. It is not offered on tickets that need a typed word, and Freeze ends the window at once. It lives in memory only, so a restart ends it too. If you never want it, set `ALLOW_ALL_MINUTES=0`.

</details>

<details>
<summary><b>How do I stop everything right now?</b></summary>

Press **Freeze** on the Confirm page. For a harder stop, set `READ_ONLY=1`, delete the tokens, remove the SSH key, or stop the app in Coolify.

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
<summary><b>How do I update or remove it?</b></summary>

See [updates.md](updates.md) and the end of [setup-own-server.md](setup-own-server.md).

</details>

## Still have a question?

Open a [Question](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=question.yml).
