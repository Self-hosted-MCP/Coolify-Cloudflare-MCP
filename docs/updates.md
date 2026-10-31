# Updates

Each release has a version tag (`vX.Y.Z`) and notes on the [releases page](https://github.com/Self-hosted-MCP/Coolify-Cloudflare-MCP/releases). What changed: [CHANGELOG.md](../CHANGELOG.md).

## Know when there's an update

On GitHub, choose **Watch, Custom, Releases** on the repository. GitHub emails you each new release. Your version is `__version__` in `src/opsmcp/__init__.py`.

## Update by hand

On your computer:

```bash
git pull
uv sync
```

On a server with Coolify: **Redeploy** the app after the new code is in the repository it builds from. Coolify rebuilds the image. If your fork follows this repository, pull the new commits into your fork first.

Before updating, read the CHANGELOG for new settings. Run `uvx pip-audit` too.

## Staying on one version

Point Coolify at a tag (`v0.1.0`) instead of `main`.

## Going back

Deploy the previous tag the same way. Coolify can also roll back to an earlier image.

## What an update never touches

Your environment variables in Coolify, and the `data` volume (login records, the action log).
