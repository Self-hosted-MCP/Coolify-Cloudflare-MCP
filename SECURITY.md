# Security policy

Coolify-Cloudflare-MCP holds API tokens for your Coolify and Cloudflare, an optional SSH key for your server, and a passphrase hash, and it can change those systems after you tap Confirm.

Works with Coolify and Cloudflare. Not made by or affiliated with them. Problems in Coolify or Cloudflare themselves go to those projects.

## Supported versions

Only the newest release gets security fixes. Updating is the fix. See [docs/updates.md](docs/updates.md).

| Version | Security fixes |
|---|---|
| 0.1.x (the latest release, [see Releases](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/releases/latest)) | Yes |
| Anything older | No, please update |

## Reporting a problem

Please **don't** open a public issue, discussion or pull request for a security problem.

1. Go to the **Security** tab of this repository and click **[Report a vulnerability](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/security/advisories/new)**. Only the maintainer sees it.
2. Tell me what's in the next section.
3. Never send real passwords, keys, tokens or private data. Use test data.

There's no email contact. Use private reporting.

## What to include

- The version (`version` in `pyproject.toml`, or the `/version` address of your server) and how you run it (computer test or Docker on a server).
- Your AI app and how you reach the Confirm page, if it matters.
- What you found, and which part of the code it's in, if you know.
- The steps to reproduce it.
- What an attacker could do with it, and what they need first.

## What happens next

| When | What |
|---|---|
| Within 3 days | You get a first answer saying the report arrived |
| Within 10 days | I confirm the problem (or explain why it isn't one) and agree on a plan |
| Usually within 30 days | A fixed release is published |
| After the release | The advisory is published, with a CVE when it's useful |

This is a project run in spare time, so a date can slip. If it does, you'll hear why. Please keep the problem private until the fixed release is out, or until 90 days have passed, whichever comes first.

## Credit

If you'd like, you're named in the published advisory and in [CHANGELOG.md](CHANGELOG.md). Tell me the name or GitHub account to use, or say you'd rather stay anonymous. There's no paid bug bounty.

## Testing in good faith

If you follow this policy, I won't take any action against you for your research. Please:

- test only on your own data and your own computer or server, or ones you have permission to test
- never open, read or change other people's data
- stop and report as soon as you see someone else's data
- don't run denial-of-service tests against someone else's server

## In scope

- Anything that could reveal a token, key, passphrase or environment value to someone who shouldn't have them (tool answers, pages, error messages, logs, files on disk).
- Any way for an AI app to make a change without a tap on the Confirm page, or to change something the ticket did not say.
- Any way to use the Confirm page without the Zero Trust login and the allowed email, to log in to the MCP door without the passphrase, or to connect a new AI app while pairing is closed.
- Any way to reach a Coolify or Cloudflare setting this tool says it cannot change (for example deleting an app, or changing Cloudflare outside DNS records and one tunnel's routes).

## Out of scope

- An AI model following instructions hidden in a file (prompt injection). That's a known limit of today's AI models. The defences are in [docs/safety.md](docs/safety.md), and improvements are welcome as normal issues.
- A user asking the AI to do something harmful to their own data, after the approvals.
- Weak passwords or passphrases chosen by a user.
- What's listed under "What it can't protect" in [docs/threat-model.md](docs/threat-model.md).
- Problems in Coolify, Cloudflare, your hosting company or your AI app. Please report those to them.
- Problems in a dependency that this project doesn't use in a harmful way.
- Missing security headers or reports from automated scanners without a real attack that works.

## Keeping your own setup safe

- Update when a new release comes out.
- Use a passphrase nobody can guess, at least 12 characters.
- Start with a read-only Coolify token and a read-only Cloudflare token. Add the change tokens only when you need them, as narrow as possible.
- Read every ticket before you tap Confirm.
- Keep backups.
- More in [docs/safety.md](docs/safety.md) and [docs/privacy.md](docs/privacy.md).
