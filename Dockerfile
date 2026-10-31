FROM python:3.14-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY src ./src
RUN uv sync --frozen --no-dev
ENV HOST=0.0.0.0 PORT=8765 ADMIN_PORT=8766 DATA_DIR=/data PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd -m -u 1000 app && mkdir -p /data && chown -R app /data
USER app
EXPOSE 8765 8766
HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health')"
CMD ["coolify-cloudflare-mcp"]
