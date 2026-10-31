# Threat model

What Coolify-Cloudflare-MCP protects against, and what it can't, so you can decide where to use it.

## What it protects

| Situation | What happens |
|---|---|
| An AI app asks for a change | It becomes a ticket. Nothing runs without your tap on the Confirm page |
| An AI app writes a misleading ticket | It can't. The server writes the ticket text from checked arguments |
| An AI app wants a secret | No tool takes one, and values are hidden in answers |
| A log, an app name or a DNS record contains instructions | Everything coming back is wrapped as data, and the server tells the AI not to follow it |
| A stranger reaches the Confirm page | It needs Cloudflare's signed token and your email, checked by the server itself |
| A stranger connects an AI app | A new app can only connect while you have opened pairing, and still needs the passphrase |
| Someone guesses the passphrase | Wrong tries are limited and slowed down |
| A web page tries to press your Confirm buttons | Same-origin checks, a form token tied to you and the ticket, no scripts, no framing |
| The AI asks for a bigger change than shown | The arguments are hashed when the ticket is made and checked again before running |

## What it can't protect

| Situation | Why, and what to do |
|---|---|
| You tap without reading | The tap is the last guard. Read every ticket. Careful tickets are marked red |
| Anyone controlling the server or Coolify | They can read the tokens. Use a machine only you control |
| What you let the AI read | It goes to your AI app's company. Use read-only tokens where you can |
| A stolen AI-app login | It can read what the read tools read, but cannot change anything without your tap |
| Secrets in unusual shapes | Hiding is best effort |
| A code bug in the public door | The door and the approval engine run in one process |
| Instructions hidden in your data | A known limit of AI models. See [safety.md](safety.md) |
| The optional terminal | It is a real shell. See [safety.md](safety.md#the-terminal-honestly) |

## Not audited yet

No one outside the project has audited the code. It had three rounds of review by separate AI agents, and every finding was fixed with a test. The tests also run against pretend services only; see [safety.md](safety.md) for what was and was not tried live.
