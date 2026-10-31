# Contributing

Thanks for wanting to help. Coolify-Cloudflare-MCP is free and open source under the [Apache-2.0](LICENSE) license. Bug reports, fixes and clearer docs are all welcome. Small, focused changes are the easiest to review.

## Reporting a problem

Click **New issue** on GitHub and pick a form:

| Form | Use it when |
|---|---|
| **Something doesn't work** | You hit a bug or an error message |
| **Question or idea** | You want to know how to do something, or have an idea |
| **Idea or feature** | You want something new or different |
| **Report a security problem, privately** | Someone could misuse the project or reach private data. Only the maintainer sees it. See [SECURITY.md](SECURITY.md) |

Each form asks for what's needed to help you, such as how you run it and which AI app you use.

**Leave out passwords, keys, tokens and private data before posting.** Issues are public. For security problems, don't open an issue: follow [SECURITY.md](SECURITY.md).

## Changing the code

1. Read [AGENTS.md](AGENTS.md). It explains the code and the rules that must never break.
2. Install [uv](https://docs.astral.sh/uv/), then the project with its test tools:

   ```bash
   uv sync
   ```

3. Make your change, with a test in `tests/`. Tests use test data only. Never use real data or a real secret in a test.
4. Run the tests. Everything must pass:

   ```bash
   uv run pytest -q
   ```

   The tests also check that every tool is in `docs/tools.md`, every setting is in `docs/settings.md` and `.env.example`, every link in the docs works, and no doc has an em dash.
5. If people will notice the change, update the matching page in `docs/` and add a line to [CHANGELOG.md](CHANGELOG.md).
6. Open a pull request saying what changed and why.

## Rules

- **Never weaken the safety rules** in [AGENTS.md](AGENTS.md). A change that touches one needs a very good reason, a test, and a clear note in the pull request.
- No tool may ever take a password, a key or a passphrase, and no change may skip the Confirm page.
- Don't add new runtime dependencies without a strong reason.
- Keep third-party GitHub Actions pinned to a commit.

## Releases (maintainers)

1. Set the new version in `pyproject.toml`, `src/opsmcp/__init__.py` and `CITATION.cff`. Move the notes in [CHANGELOG.md](CHANGELOG.md) under that version, with the date.
2. Run the tests and wait for the **Tests** workflow on GitHub to pass.
3. Push to `main`, tag it `vX.Y.Z`, and publish a GitHub Release with the changelog notes.

## Writing docs

The docs are for people who have never used a terminal.

- Short sentences (8 to 20 words), everyday words, "you". Explain any technical word the first time.
- Headings in sentence case, phrased the way a reader would ask ("If something goes wrong").
- One command per code block, and show what the reader should see when it works.
- Button and page names in **bold**, exactly as on the page. Example questions for the AI in *italics*. Commands, settings and file names in `code`.
- No em dashes. Use colons, commas or brackets.
- Never write that something was tested unless it was. Say "not supported" with the reason.
- Where it matters: "Works with Coolify and Cloudflare. Not made by or affiliated with them."

## Credit and license

By contributing, you agree that your work is shared under the [Apache-2.0](LICENSE) license, the same as the rest of the project. Keep the original credit ([LICENSE](LICENSE), [NOTICE](NOTICE), `CITATION.cff`) and add yourself to the changelog entry if you like.
