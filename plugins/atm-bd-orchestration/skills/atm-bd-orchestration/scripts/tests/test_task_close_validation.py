"""The extracted validators remain the hook's public objects."""
import ast
import io
from pathlib import Path
import tokenize

import pytest

from task_close_world import hook
import task_close_validation as validation


def test_production_scripts_obey_rule_003():
    scripts = Path(__file__).resolve().parents[1]
    ignored = {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL,
               tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT}
    counts = {}
    for path in sorted(scripts.rglob("*")):
        if not path.is_file() or path.suffix not in ("", ".py") or "tests" in path.relative_to(scripts).parts or "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        first_line = source.splitlines()[0] if source else ""
        if path.suffix != ".py" and not (first_line.startswith("#!") and ("python" in first_line or "uv run --script" in first_line)):
            continue
        docstrings = set()
        for node in ast.walk(ast.parse(source, filename=str(path))):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    assert first.end_lineno is not None
                    docstrings.update(range(first.lineno, first.end_lineno + 1))
        counts[str(path.relative_to(scripts))] = len({token.start[0] for token in tokenize.generate_tokens(io.StringIO(source).readline)
                                                      if token.type not in ignored and token.start[0] not in docstrings})
    assert counts
    assert {name: count for name, count in counts.items() if count > 1000} == {}


def test_hook_reexports_the_shared_validators_and_error():
    for name in ("CloseError", "assignment_details", "assignment_id_for_round", "sanity_round",
                 "sanity_round_key", "validate_command_json", "header", "reviewer_list", "validate",
                 "sanity_close_mode", "bd_value", "read_vars", "merge_result", "validate_outcome",
                 "read_toml_setting", "read_config"):
        assert getattr(hook, name) is getattr(validation, name)
    with pytest.raises(hook.CloseError) as error:
        validation.validate_command_json(["atm", "task", "events", "task", "--json"], {"events": "bad"})
    assert error.value.code == "COMMAND.INVALID"
    assert "atm task events task" in error.value.fix
