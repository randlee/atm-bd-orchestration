#!/usr/bin/env python3
"""Generate stubs/atm_bd_types.pyi and stubs/atm_bd_core.pyi from the Rust bindings, through the built wheel.

    uv run --frozen --no-editable python gen_stubs.py          # rewrite both stubs
    uv run --frozen --no-editable python gen_stubs.py --check  # exit 1 if a checked-in stub is stale

The text comes from `atm_bd_types._native._stub(module)`: enum and record stubs are rendered from the Rust
declarations, method signatures from the text each binding carries. Before anything is written, every name a stub
declares for the types package is checked against its runtime module. The core package tests its own
runtime surface against the core stub without introducing a core dependency into the types package.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
STUBS = HERE / "stubs"
# Both stubs come from Rust; only the types runtime is installed in this package.
SURFACES = ("atm_bd_types", "atm_bd_core")
MODULES = {"atm_bd_types": "atm_bd_types"}


def stub_text(name: str) -> str:
    native = importlib.import_module("atm_bd_types._native")
    return native._stub(name)


def _stub_parameters(args: ast.arguments, *, drop_first: bool = False) -> list[tuple[str, str, bool]]:
    positional = [*args.posonlyargs, *args.args]
    defaults = [False] * (len(positional) - len(args.defaults)) + [True] * len(args.defaults)
    result = [(item.arg, "posonly" if index < len(args.posonlyargs) else "poskw", defaults[index])
              for index, item in enumerate(positional)]
    if drop_first and result:
        result.pop(0)
    if args.vararg:
        result.append((args.vararg.arg, "varpos", False))
    result.extend((item.arg, "kwonly", default is not None)
                  for item, default in zip(args.kwonlyargs, args.kw_defaults, strict=True))
    if args.kwarg:
        result.append((args.kwarg.arg, "varkw", False))
    return result


def _signature_mismatch(label: str, expected: list[tuple[str, str, bool]], target: object) -> list[str]:
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError) as error:
        return [f"{label}: runtime signature unavailable: {error}"]
    kinds = {inspect.Parameter.POSITIONAL_ONLY: "posonly", inspect.Parameter.POSITIONAL_OR_KEYWORD: "poskw",
             inspect.Parameter.VAR_POSITIONAL: "varpos", inspect.Parameter.KEYWORD_ONLY: "kwonly",
             inspect.Parameter.VAR_KEYWORD: "varkw"}
    actual = [(p.name, kinds[p.kind], p.default is not inspect.Parameter.empty)
              for p in signature.parameters.values()]
    if expected and actual and expected[0][0] in ("self", "cls") and actual[0][0] == expected[0][0]:
        actual[0] = (actual[0][0], expected[0][1], actual[0][2])
    if expected != actual:
        return [f"{label}: signature mismatch: stub {expected}, runtime {actual}"]
    return []


def _class_mismatches(node: ast.ClassDef, cls: type, module: ModuleType,
                      classes: dict[str, ast.ClassDef]) -> list[str]:
    out: list[str] = []
    declared: list[str] = []
    enum_members: list[str] = []
    methods: dict[str, ast.FunctionDef] = {}
    record = any(isinstance(d, ast.Name) and d.id == "_record" for d in node.decorator_list)
    protocol = any(ast.unparse(base) == "typing.Protocol" for base in node.bases)
    enum_stub = any(ast.unparse(base) == "enum.Enum" for base in node.bases)
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef):
            methods[stmt.name] = stmt
            if stmt.name not in ("__new__", "__init__"):
                declared.append(stmt.name)
        elif isinstance(stmt, ast.Assign):
            names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
            declared += names
            if enum_stub:
                enum_members += names
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            declared.append(stmt.target.id)
            if isinstance(stmt.annotation, ast.Subscript) and ast.unparse(stmt.annotation.value) == "typing.ClassVar":
                enum_members.append(stmt.target.id)
    out += [f"{node.name}.{name}: in the stub, not on the binding" for name in declared if not hasattr(cls, name)]
    for name, method in methods.items():
        if name in ("__new__", "__init__") or not hasattr(cls, name):
            continue
        if any(isinstance(d, ast.Name) and d.id == "property" for d in method.decorator_list):
            continue
        out += _signature_mismatch(f"{node.name}.{name}", _stub_parameters(method.args), getattr(cls, name))
    if not protocol:
        constructor = methods.get("__init__") or methods.get("__new__")
        if constructor:
            expected = _stub_parameters(constructor.args, drop_first=True)
        elif record:
            expected = [(stmt.target.id, "poskw", stmt.value is not None) for stmt in node.body
                        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)]
        else:
            expected = []
        out += _signature_mismatch(f"{node.name} constructor", expected, cls)
    if not node.bases and cls.__bases__ != (object,):
        out.append(f"{node.name}: runtime bases differ from stub")
    for base in node.bases:
        name = ast.unparse(base)
        if name == "enum.Enum":
            continue  # PyO3 enum values are checked as named singletons below.
        if name == "typing.Protocol":
            if not getattr(cls, "_is_protocol", False):
                out.append(f"{node.name}: stub declares Protocol but runtime is concrete")
            continue
        base_cls = getattr(module, name, None)
        base_stub = classes.get(name)
        if not isinstance(base_cls, type):
            out.append(f"{node.name}: runtime base {name} unavailable")
        elif getattr(base_cls, "_is_protocol", False) and base_stub:
            for method in (x for x in base_stub.body if isinstance(x, ast.FunctionDef)):
                if not hasattr(cls, method.name):
                    out.append(f"{node.name}: missing protocol member {name}.{method.name}")
                else:
                    out += _signature_mismatch(f"{node.name}.{method.name} (protocol {name})",
                                               _stub_parameters(method.args), getattr(cls, method.name))
        elif base_cls not in cls.__bases__:
            out.append(f"{node.name}: runtime does not inherit {name}")
    allowed_bases = {getattr(module, ast.unparse(base), None) for base in node.bases}
    if any(ast.unparse(base) == "typing.Protocol" for base in node.bases):
        import typing
        allowed_bases.add(typing.Protocol)
    for base in cls.__bases__:
        if base is not object and base not in allowed_bases:
            out.append(f"{node.name}: unexpected runtime base {base.__name__}")
    if enum_members:
        runtime = {k for k, v in vars(cls).items() if isinstance(v, cls)}
        out += [f"{node.name}.{name}: a binding member the stub lacks" for name in sorted(runtime - set(enum_members))]
        for name in enum_members:
            if not hasattr(cls, name):
                continue
            value = getattr(cls, name, None)
            if not isinstance(value, cls) or getattr(value, "name", None) != name or value is not getattr(cls, name):
                out.append(f"{node.name}.{name}: expected named singleton")
    return out


def surface_mismatches(text: str, module: ModuleType) -> list[str]:
    """Compare exported names, callable parameter shapes, class bases and enum members."""
    out: list[str] = []
    declared: set[str] = set()
    nodes = ast.parse(text).body
    classes = {node.name: node for node in nodes if isinstance(node, ast.ClassDef)}
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            declared.add(node.name)
            cls = getattr(module, node.name, None)
            if not isinstance(cls, type):
                out.append(f"{node.name}: in the stub, not in {module.__name__}")
                continue
            out += _class_mismatches(node, cls, module, classes)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            declared.add(node.name)
            target = getattr(module, node.name, None)
            if not callable(target):
                out.append(f"{node.name}: in the stub, not callable in {module.__name__}")
            else:
                out += _signature_mismatch(node.name, _stub_parameters(node.args), target)
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
    stubs = {name: stub_text(name) for name in SURFACES}
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
