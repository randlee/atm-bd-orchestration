#!/usr/bin/env python3
"""Generate stubs/atm_bd_types.pyi and stubs/atm_bd_core.pyi from the Rust bindings, through the built wheel.

    uv run --frozen --no-editable python gen_stubs.py          # rewrite both stubs
    uv run --frozen --no-editable python gen_stubs.py --check  # exit 1 if a checked-in stub is stale

The text comes from `atm_bd_types._native._stub(module)`: enum and record stubs are rendered from the Rust
declarations, method signatures from the text each binding carries. Before anything is written, every name a stub
declares is checked against the runtime module (classes, enum members, methods, properties, record fields) and every
name the module exports against the stub, so a stub can never describe a binding that does not exist.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
STUBS = HERE / "stubs"
# stub name -> the runtime module whose names it declares
MODULES = {"atm_bd_types": "atm_bd_types", "atm_bd_core": "atm_bd_types._core"}


def stub_text(name: str) -> str:
    native = importlib.import_module("atm_bd_types._native")
    return native._stub(name)


def _class_mismatches(node: ast.ClassDef, cls: type) -> list[str]:
    out: list[str] = []
    declared: list[str] = []
    is_enum = any(isinstance(b, ast.Attribute) and b.attr == "Enum" for b in node.bases)
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name not in ("__new__", "__init__"):
            declared.append(stmt.name)
        elif isinstance(stmt, ast.Assign):
            declared += [t.id for t in stmt.targets if isinstance(t, ast.Name)]
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            declared.append(stmt.target.id)
    out += [f"{node.name}.{name}: in the stub, not on the binding" for name in declared if not hasattr(cls, name)]
    if is_enum:
        runtime = {k for k, v in vars(cls).items() if isinstance(v, cls)}
        out += [f"{node.name}.{name}: a binding member the stub lacks" for name in sorted(runtime - set(declared))]
    return out


def surface_mismatches(text: str, module: ModuleType) -> list[str]:
    """Every difference between the names `text` declares and the names `module` provides."""
    out: list[str] = []
    declared: set[str] = set()
    for node in ast.parse(text).body:
        if isinstance(node, ast.ClassDef):
            declared.add(node.name)
            cls = getattr(module, node.name, None)
            if not isinstance(cls, type):
                out.append(f"{node.name}: in the stub, not in {module.__name__}")
                continue
            out += _class_mismatches(node, cls)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            declared.add(node.name)
            if not callable(getattr(module, node.name, None)):
                out.append(f"{node.name}: in the stub, not callable in {module.__name__}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            declared.add(node.target.id)
            if not hasattr(module, node.target.id):
                out.append(f"{node.target.id}: in the stub, not in {module.__name__}")
    public = {n for n in declared if not n.startswith("_")}
    exported = set(getattr(module, "__all__", []))
    out += [f"{name}: exported by {module.__name__}, not in the stub" for name in sorted(exported - public)]
    out += [f"{name}: in the stub, not in {module.__name__}.__all__" for name in sorted(public - exported)]
    return out


def generate() -> dict[str, str]:
    """Stub name -> text; raises SystemExit naming every stub/binding mismatch."""
    stubs = {name: stub_text(name) for name in MODULES}
    problems = [f"{name}.pyi: {p}" for name, mod in MODULES.items()
                for p in surface_mismatches(stubs[name], importlib.import_module(mod))]
    if problems:
        raise SystemExit("stub and bindings disagree:\n  " + "\n  ".join(problems))
    return stubs


def main(argv: list[str]) -> int:
    stubs = generate()
    if "--check" in argv:
        stale = [n for n, text in stubs.items() if (STUBS / f"{n}.pyi").read_text(encoding="utf-8") != text]
        if stale:
            print("stale stubs: " + ", ".join(stale) + "; run: uv run --frozen --no-editable python gen_stubs.py")
            return 1
        return 0
    STUBS.mkdir(exist_ok=True)
    for name, text in stubs.items():
        (STUBS / f"{name}.pyi").write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
