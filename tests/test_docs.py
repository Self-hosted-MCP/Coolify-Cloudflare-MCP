"""The docs stay true: every link and anchor works, every setting and tool is documented, no em dashes."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
DOCS = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")])
LINK = re.compile(r"\]\(([^)\s]+)\)|href=\"([^\"]+)\"|src=\"([^\"]+)\"")
EM = chr(0x2014)  # the em dash character


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    text = re.sub(r"[`*_]|<[^>]+>", "", heading.strip().lower())
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    out = set()
    in_code = False
    for line in path.read_text("utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if in_code or not line.startswith("#"):
            continue
        s = slug(line.lstrip("#"))
        n = seen.get(s, 0)
        seen[s] = n + 1
        out.add(s if n == 0 else f"{s}-{n}")
    return out


def test_links_and_anchors_work():
    broken = []
    for doc in DOCS:
        text = re.sub(r"```.*?```", "", doc.read_text("utf-8"), flags=re.S)
        for m in LINK.finditer(text):
            target = next(g for g in m.groups() if g)
            if re.match(r"[a-z]+:", target) or target.startswith("//"):
                continue
            path, _, anchor = target.partition("#")
            dest = (doc.parent / path).resolve() if path else doc
            if not dest.exists():
                broken.append(f"{doc.name}: {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                broken.append(f"{doc.name}: {target} (no such heading)")
    assert not broken, "\n".join(broken)


def _setting_names() -> set[str]:
    """Every environment variable the code reads, found in the source."""
    names = set()
    for src in (ROOT / "src" / "opsmcp").glob("*.py"):
        text = src.read_text("utf-8")
        names |= set(re.findall(r'(?:env|env_int|env_list|flag|safe_flag)\("([A-Z][A-Z0-9_]+)"', text))
        names |= set(re.findall(r'config\.env\("([A-Z][A-Z0-9_]+)"', text))
    return names


def test_every_setting_is_documented():
    settings = (ROOT / "docs" / "settings.md").read_text("utf-8")
    missing = sorted(n for n in _setting_names() if f"`{n}`" not in settings)
    assert not missing, f"not in docs/settings.md: {missing}"


def test_env_example_matches_the_docs():
    settings = (ROOT / "docs" / "settings.md").read_text("utf-8")
    names = re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", (ROOT / ".env.example").read_text("utf-8"), flags=re.M)
    assert names
    missing = sorted(n for n in names if f"`{n}`" not in settings)
    assert not missing, f"in .env.example but not in docs/settings.md: {missing}"


def test_every_tool_is_documented():
    import asyncio
    from opsmcp import server
    tools = (ROOT / "docs" / "tools.md").read_text("utf-8")
    names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    assert names
    assert f"The {len(names)} tools" in tools, f"tools.md must say 'The {len(names)} tools'"
    missing = [n for n in names if f"`{n}`" not in tools]
    assert not missing, f"not in docs/tools.md: {missing}"


def test_no_em_dashes():
    found = [f"{d.name}:{i}" for d in DOCS for i, line in enumerate(d.read_text("utf-8").splitlines(), 1)
             if EM in line or (" " + chr(0x2013) + " ") in line]
    assert not found, found
