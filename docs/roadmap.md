# Roadmap

What might come next. Nothing here is promised or has a date. If you want one of them, say so in an [issue](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/issues/new?template=question.yml), or help build it ([CONTRIBUTING.md](../CONTRIBUTING.md)).

## Wanted

- **Run against more real setups.** Cloudflare changes and the terminal are tested with pretend services. Reports from real accounts are very welcome.
- **A separate terminal user without the `docker` group.** Plus a small docker-socket-proxy or fixed sudo rules for the five number checks.
- **Split the two doors into two processes.** A bug in the public door could then not reach the approval engine.
- **A ready-made Docker image** published on a release.

## Maybe

- **Reload Compose.** Needs a clear Coolify API call to exist first.
- **Create and delete apps, services and databases.** Each kind needs its own careful design.
- **Traffic and security events from Cloudflare.** A different Cloudflare API.

## Not planned

- **Cloudflare Zero Trust, WAF and R2 changes.** A mistake there can lock you out. The Cloudflare dashboard is the right place.
- **Running arbitrary commands outside the terminal.** Too much power for too little control.
- **Telemetry of any kind.**
