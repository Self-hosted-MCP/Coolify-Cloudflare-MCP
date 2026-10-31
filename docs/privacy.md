# Privacy

What is kept, where, and who can see it.

## What leaves your computer or server

Nothing goes to us. There is no account, no cloud service of ours and no tracking. The server makes these calls and no others:

- To your own Coolify, with your Coolify token.
- To Cloudflare's API (`api.cloudflare.com`), with your Cloudflare tokens.
- Over SSH to your server, only if you switch the terminal on.
- To your AI app's company, indirectly: see the next section.

## What the AI app sees

Whatever your AI reads for you goes to the company that runs your AI app. That includes app names, domains, deployment logs, DNS records and anything a terminal shows. Secrets are hidden on a best-effort basis, so use a `read` Coolify token and read-only Cloudflare token until you need more, and do not put anything in your logs that you would not want an AI company to see.

## What's kept

| What | Where | Who can read it |
|---|---|---|
| Your tokens and SSH key | Environment variables in Coolify | Whoever can open Coolify |
| Login records of AI apps (fingerprints) | `/data` volume | Whoever controls the server |
| The action log | `/data` volume | Whoever controls the server |
| Open tickets | Memory only | Gone after a restart |

## Logs of the program itself

One action log: what was asked, tapped, run or refused, with a timestamp in UTC. It never holds secret values, environment values or typed terminal text (it records how many characters were typed). The file is capped by `ACTION_LOG_MAX_MB`. Container logs are capped at about 15 MB.

## Deleting everything

1. Stop and delete the app in Coolify.
2. Delete its `data` volume.
3. Delete the Coolify token, both Cloudflare tokens, and the SSH key from the server user.
4. Remove the connector from your AI app, and the Zero Trust application if you no longer need it.

**What next:** [Safety](safety.md) · [Threat model](threat-model.md)
