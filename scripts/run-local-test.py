"""Starts the MCP on your computer for a test: reads .env as plain KEY=value lines (no shell, so values with | or $ stay whole),
keeps Zero Trust off (both doors on 127.0.0.1 only) and data in ./data. The first start begins Frozen: Claude can look, not ask for changes.
Needs a way to reach Coolify's API first, for example an SSH tunnel: ssh -f -N -L 127.0.0.1:8000:localhost:8000 your-server (then COOLIFY_API_URL=http://127.0.0.1:8000).
Run from anywhere:  uv run python scripts/run-local-test.py"""
import os
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
for line in (root / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
os.environ.setdefault("ACCESS_ENFORCE", "0")
os.environ.setdefault("PORT", "8775")                 # 8765 is often taken by other local tools
os.environ.setdefault("ADMIN_PORT", "8776")
os.environ.setdefault("PUBLIC_URL", f"http://localhost:{os.environ['PORT']}")
os.environ.setdefault("CONFIRM_URL", f"http://localhost:{os.environ['ADMIN_PORT']}")
os.environ.setdefault("DATA_DIR", str(root / "data"))

data = pathlib.Path(os.environ["DATA_DIR"])
if not data.exists():
    data.mkdir(mode=0o700, parents=True)
    (data / "frozen").write_text("frozen\n")

sys.path.insert(0, str(root / "src"))
from opsmcp.server import main  # noqa: E402

main()
