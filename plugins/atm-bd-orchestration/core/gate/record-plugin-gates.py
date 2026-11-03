#!/usr/bin/env python3
"""Record one Jev sample for each changed plug-in hook/spec/question-set input."""
from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path
from types import ModuleType


def load_gate() -> ModuleType:
    path = Path(__file__).with_name("atm-bd-lite-gate.py")
    spec = importlib.util.spec_from_file_location("atm_bd_lite_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load gate module at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record_hook(gate: ModuleType, hook: Path, spec: Path, records_dir: Path) -> bool:
    source = hook.read_text(encoding="utf-8")
    spec_text = spec.read_text(encoding="utf-8")
    question_set = gate.QUESTIONS.read_text(encoding="utf-8")
    rows = gate.table(spec_text, "Transitions")
    facts = gate.facts(source)
    failures = gate.deterministic(source, facts, rows)
    digest = gate.input_sha256(source, spec_text, question_set)
    target = gate.record_path(digest, records_dir)
    if failures:
        print(f"RECORD.DETERMINISTIC_FAILURE: {hook.name} sha256={digest}: {failures}", file=sys.stderr)
        return False
    if target.exists():
        print(f"RECORD.EXISTS: {hook.name} sha256={digest}")
        return True
    questions = gate.questions(facts, rows)
    state = {"hook": source, "spec": spec_text}
    try:
        reply = gate.check(state, questions)
        gate.write_record(target, digest, reply.answers, reply.input_tokens)
    except (gate.JevError, OSError) as exc:
        print(f"RECORD.JEV_FAILED: {hook.name} sha256={digest}: {exc}", file=sys.stderr)
        return False
    print(f"RECORD.WRITTEN: {hook.name} sha256={digest} path={target}")
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    gate = load_gate()
    results = []
    for profile in sorted((root / "skills").glob("*/profile.toml")):
        data = tomllib.loads(profile.read_text(encoding="utf-8"))
        for name, script in sorted(data.get("hooks", {}).items()):
            hook = profile.parent / script
            spec = profile.parent / "hooks" / (name.replace(".", "-") + ".md")
            if not spec.is_file():
                print(f"RECORD.SPEC_MISSING: {spec}", file=sys.stderr)
                results.append(False)
                continue
            results.append(record_hook(gate, hook, spec, gate.RECORDS_DIR))
    if not results:
        print("RECORD.NO_HOOKS: no declared plug-in hooks found", file=sys.stderr)
        return 2
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
