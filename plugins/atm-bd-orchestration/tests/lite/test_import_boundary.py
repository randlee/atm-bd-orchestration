"""Additional import checks; the copied contract boundary test stays unchanged."""
import ast
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[2] / "skills" / "atm-bd-lite"


def forbidden_imports(source: str) -> list[str]:
    """Report imports outside the public types module and sys, including dynamic imports."""
    forbidden = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            forbidden.extend(alias.name for alias in node.names if alias.name not in {"atm_bd_types", "sys"})
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            if module not in {"atm_bd_types", "sys"}:
                forbidden.append(module)
            elif module == "atm_bd_types":
                forbidden.extend(f"{module}.{alias.name}" for alias in node.names if alias.name.startswith("_"))
        elif isinstance(node, ast.Name) and node.id in {"__import__", "importlib"}:
            forbidden.append(node.id)
    return forbidden


@pytest.mark.parametrize("path", sorted(SKILLS.rglob("*.py")), ids=lambda path: path.name)
def test_lite_imports_stay_on_public_boundary(path: Path) -> None:
    assert forbidden_imports(path.read_text(encoding="utf-8")) == [], path


@pytest.mark.parametrize("source", [
    "import atm_bd_types._native",
    "from atm_bd_types._native import Ports, stack_of",
    "from atm_bd_types import _native",
    "__import__('os')",
    "import importlib",
    "from importlib import import_module",
    "importlib.import_module('os')",
    "from . import helper",
    "import sys.path",
])
def test_rejects_boundary_bypasses(source: str) -> None:
    assert forbidden_imports(source)


def test_accepts_public_imports() -> None:
    assert forbidden_imports("import sys\nimport atm_bd_types\nfrom atm_bd_types import Refusal as R") == []
