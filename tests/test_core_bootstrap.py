# pyright: strict
"""Production users of shared core must keep the same bootstrap."""
import ast
from pathlib import Path


def test_profile_core_bootstraps_are_identical() -> None:
    skills = Path(__file__).resolve().parents[1] / "plugins/atm-bd-orchestration/skills"
    snippets: dict[str, str] = {}
    for path in skills.rglob("*"):
        if not path.is_file() or "tests" in path.parts or "scripts" not in path.parts:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        marker = "import json as _core_json\n"
        if marker not in text:
            continue
        start = text.index(marker)
        end = text.index("    raise SystemExit(3)\n", text.index("_core_resolved =", start)) + len("    raise SystemExit(3)\n")
        snippets[str(path)] = text[start:end]
    assert snippets
    assert len(set(snippets.values())) == 1, f"core bootstrap drift: {list(snippets)}"


def test_every_profile_core_import_has_bootstrap() -> None:
    root = Path(__file__).resolve().parents[1] / "plugins/atm-bd-orchestration"
    modules = {path.stem for path in (root / "core/scripts").glob("*.py")}
    for path in (root / "skills").rglob("*"):
        if not path.is_file() or "tests" in path.parts or "scripts" not in path.parts:
            continue
        try:
            source = path.read_text()
            tree = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError):
            continue
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
        }
        if modules & imports:
            assert "import json as _core_json\n" in source, str(path)
