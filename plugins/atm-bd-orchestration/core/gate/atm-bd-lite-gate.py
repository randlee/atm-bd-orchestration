#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2"]
# ///
"""atm-bd-lite gate: hold one hook file to its hooks/*.md spec (fenix-brief.md §B).

usage: atm-bd-lite-gate.py <hook.py> <hooks/spec.md> --out run.json

Deterministic checks run first and fail before Jev: rows == Transition arms (ANC-052), at most one
beads write and no create/claim/release (ANC-064), stack_bead only read (ANC-065), no subprocess/bd/gh
(ANC-066), <= 100 lines (ANC-070). Then one Jev request with two question sets: every Transitions row
is implemented by exactly one arm with no additional check or write (ANC-053); every arm and reply site
is listed as a row or an Errors entry (ANC-054). Jev's answers and errors are advisory; only deterministic
failures block. Writes the run JSON; exits 1 on a deterministic failure and 3 for invalid usage.
"""
import ast, dataclasses, hashlib, json, sys
from pathlib import Path
from typing import Any, TypedDict

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN_ROOT / "skills/atm-bd-orchestration/scripts"))
from jev_client import MODEL, JevError, JsonObject, evaluate, is_json_object

QUESTIONS = Path(__file__).with_name("gate-questions.json")
# Write detection recognizes only receivers named beads, cache, or store; aliases are not tracked.
WRITES, FORBIDDEN_WRITES = {"update", "create", "claim", "release"}, {"create", "claim", "release"}
READS = {("beads", "show"), ("cache", "get")}
CLI_ADAPTERS, OS_SPAWN, CLI_TOOLS = {"BdCli", "GitCli", "AtmCli"}, ("system", "popen", "exec", "spawn"), {"gh", "bd", "git"}
REPLIES = {"pass_through", "not_applicable", "handled"}  # plus refused(Refusal(ErrorId.X, ...)) (§B.1)
MAX_LINES = 100
QUESTION_SET_SCHEMA = "plan-anchoring/questions/1"


class Question(TypedDict):
    type: str
    instructions: str
    criteria: dict[str, str]


@dataclasses.dataclass(frozen=True)
class QuestionSet:
    templates: dict[str, Question]

    def expand(self, template: str, subjects: dict[str, str]) -> dict[str, Question]:
        if template not in self.templates:
            raise JevError("VALIDATION.INPUT", f"question set has no template {template}")
        question = self.templates[template]
        return {f"{template}:{key}": {"type": "choice",
                "instructions": question["instructions"].replace("{subject}", subject),
                "criteria": dict(question["criteria"])} for key, subject in subjects.items()}


@dataclasses.dataclass(frozen=True)
class JevReply:
    answers: dict[str, JsonObject]
    input_tokens: int | None


@dataclasses.dataclass(frozen=True)
class InputRecord:
    prompt_sha256: str
    input_tokens: int | None
    prompt_tokens: int | None
    leak: int | None
    commands: int
    equal: bool


def load_question_set(path: Path) -> QuestionSet:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JevError("VALIDATION.INPUT", f"cannot read question set {path}: {exc}") from None
    questions = raw.get("questions") if isinstance(raw, dict) and raw.get("schema") == QUESTION_SET_SCHEMA else None
    if not isinstance(questions, dict):
        raise JevError("VALIDATION.INPUT", f"{path} is not a {QUESTION_SET_SCHEMA} question set")
    templates: dict[str, Question] = {}
    for key, value in questions.items():
        criteria = value.get("criteria") if isinstance(value, dict) else None
        instructions = value.get("instructions") if isinstance(value, dict) else None
        if (not isinstance(value, dict) or value.get("type") != "choice" or not isinstance(instructions, str)
                or not isinstance(criteria, dict) or len(criteria) < 2):
            raise JevError("VALIDATION.INPUT", f"{path}: question {key} is not a choice question")
        templates[key] = {"type": "choice", "instructions": instructions,
                          "criteria": {name: str(text) for name, text in criteria.items()}}
    return QuestionSet(templates)


def check(state: JsonObject, questions: dict[str, Question]) -> JevReply:
    question_values: JsonObject = {}
    for key, question in questions.items():
        question_values[key] = {"type": question["type"], "instructions": question["instructions"],
                                "criteria": dict(question["criteria"])}
    response = evaluate({"model": MODEL, "state": state, "questions": question_values})
    answers = response.get("answers")
    if not is_json_object(answers):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Missing or unexpected answer IDs")
    parsed_answers: dict[str, JsonObject] = {}
    for key, answer in answers.items():
        if not is_json_object(answer):
            raise JevError("SANITY.JEV_RESPONSE_INVALID", "Answer must be an object")
        parsed_answers[key] = answer
    usage = response.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    return JevReply(parsed_answers, tokens if isinstance(tokens, int) and not isinstance(tokens, bool) else None)


def input_record(state: Any, questions: dict[str, Question], input_tokens: int | None,
                 prompt_tokens: int | None, commands: int) -> InputRecord:
    if prompt_tokens is not None or commands != 0:
        raise ValueError("input_record accepts only Jev usage; prompt_tokens must be None and commands must be zero")
    payload = json.dumps({"questions": questions, "state": state}, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode()
    return InputRecord(hashlib.sha256(payload).hexdigest(), input_tokens, None, None, 0, True)


def table(spec: str, heading: str) -> list[list[str]]:
    section = spec.split(f"## {heading}", 1)[1].split("\n## ", 1)[0] if f"## {heading}" in spec else ""
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in section.splitlines() if line.startswith("|")]
    return rows[2:]  # drop header and separator


def call_name(node: ast.Call) -> tuple[str, str] | None:
    f = node.func
    return (f.value.id, f.attr) if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else None


def facts(src: str) -> dict:
    tree = ast.parse(src)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    arms = [(ast.unparse(c.pattern), c.pattern.lineno) for m in ast.walk(tree) if isinstance(m, ast.Match)
            for c in m.cases]
    transition_arms = [(p, line) for p, line in arms if "Transition." in p]
    calls = [(n, call_name(n)) for n in ast.walk(tree) if isinstance(n, ast.Call)]
    beads_calls = [(name[1], n.lineno) for n, name in calls
                   if name and name[0] in {"beads", "cache", "store"}]
    def inside_loop(node: ast.AST) -> bool:
        cursor = parents.get(node)
        while cursor is not None:
            if isinstance(cursor, (ast.For, ast.AsyncFor, ast.While, ast.comprehension)):
                return True
            cursor = parents.get(cursor)
        return False

    loop_writes = [n.lineno for n, name in calls if name and name[0] in {"beads", "cache", "store"}
                   and name[1] in WRITES and inside_loop(n)]
    replies = [(ast.unparse(n), n.lineno) for n, name in calls if name and name[0] == "HookReply"
               and (name[1] in REPLIES or name[1] == "refused")]

    def only_read(node: ast.AST) -> bool:
        cursor = parents.get(node)
        while cursor is not None:
            if isinstance(cursor, ast.Call) and call_name(cursor) in READS:
                return True
            cursor = parents.get(cursor)
        return False

    def runs_cli(n: ast.Call) -> bool:
        first = n.args[0] if n.args else None
        if isinstance(first, (ast.List, ast.Tuple)) and first.elts:
            first = first.elts[0]
        return (isinstance(first, ast.Constant) and isinstance(first.value, str)
                and Path(first.value.split(" ")[0]).name in CLI_TOOLS)

    subprocess_sites = sorted(
        [(f"import {a.name}", n.lineno) for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
         if a.name.split(".")[0] == "subprocess"]
        + [(f"from {n.module} import", n.lineno) for n in ast.walk(tree)
           if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "subprocess"]
        + [(n.id if isinstance(n, ast.Name) else n.attr, n.lineno) for n in ast.walk(tree)
           if isinstance(n, (ast.Name, ast.Attribute))
           and (getattr(n, "id", None) in CLI_ADAPTERS or getattr(n, "attr", None) in CLI_ADAPTERS)]
        + [(f"import {a.name}", n.lineno) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
           for a in n.names if a.name in CLI_ADAPTERS]
        + [(ast.unparse(n)[:60], n.lineno) for n, name in calls
           if (name and name[0] == "os" and name[1].startswith(OS_SPAWN)) or runs_cli(n)], key=lambda x: x[1])
    stack_uses = [n.lineno for n in ast.walk(tree) if isinstance(n, (ast.Name, ast.Attribute))
                  and (getattr(n, "id", None) == "stack_bead" or getattr(n, "attr", None) == "stack_bead")
                  and not only_read(n)]
    return {"arms": arms, "transition_arms": transition_arms, "beads_calls": beads_calls, "replies": replies,
            "stack_bead_writes": stack_uses, "loop_writes": loop_writes,
            "subprocess_sites": subprocess_sites}


def deterministic(src: str, f: dict, rows: list[list[str]]) -> list[str]:
    names = sorted(r[1] for r in rows if len(r) >= 2)
    armed = sorted(p.removeprefix("Transition.") for p, _ in f["transition_arms"])
    writes = [c for c in f["beads_calls"] if c[0] in WRITES]
    fails = []
    if (not rows or any(len(r) < 2 for r in rows) or names != armed
            or len({r[0] for r in rows}) != len(rows) or len(set(names)) != len(names)):
        fails.append(f"ANC-052 rows != arms: spec rows {names}, Transition arms {armed}")
    if len(writes) > 1 or f["loop_writes"] or any(c[0] in FORBIDDEN_WRITES for c in writes):
        fails.append(f"ANC-064 writes: {writes}, loop writes: {f['loop_writes']} (at most one update; no create/claim/release)")
    if f["stack_bead_writes"]:
        fails.append(f"ANC-065 stack_bead used outside beads.show(/cache.get( at lines {f['stack_bead_writes']}")
    if f["subprocess_sites"]:
        fails.append(f"ANC-066 subprocess/CLI adapter/bd/gh/git: {f['subprocess_sites']}")
    if (n := len(src.splitlines())) > MAX_LINES:
        fails.append(f"ANC-070 {n} lines > {MAX_LINES}")
    return fails


def sites(f: dict) -> dict[str, str]:
    """Keep distinct arms and replies even when they share a source line."""
    return {f"L{line}:{index}": text for index, (text, line) in enumerate(f["arms"] + f["replies"])}


def questions(f: dict, rows: list[list[str]]) -> dict[str, Question]:
    qs = load_question_set(QUESTIONS)
    return (qs.expand("implemented", {r[0]: f"Spec Transitions row {r[0]} ({r[1]})." for r in rows})
            | qs.expand("listed", {key: f"state.hook {key}: `{text}`." for key, text in sites(f).items()}))


def findings(answers: dict, f: dict) -> list[str]:
    """Map each non-yes answer to the missing row or unlisted site."""
    site_map = sites(f)
    out = []
    for key, answer in answers.items():
        kind, subject = key.split(":", 1)
        if answer["choice"] != "yes":
            out.append(f"implement {subject}" if kind == "implemented"
                       else f"add a row for {subject} `{site_map.get(subject, '')}`, or remove the branch")
    return out


def main(argv: list[str]) -> int:
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(argv) != 4 or argv[2] != "--out" or not argv[3]:
        print(__doc__, file=sys.stderr)
        return 3
    hook, spec = Path(argv[0]), Path(argv[1])
    out = Path(argv[3])
    src, spec_md = hook.read_text(), spec.read_text()
    rows = table(spec_md, "Transitions")
    f = facts(src)
    run = {"hook": str(hook), "spec": str(spec), "lines": len(src.splitlines()), "rows": [r[:2] for r in rows],
           "facts": f, "deterministic_failures": deterministic(src, f, rows), "jev": None}
    if not run["deterministic_failures"]:
        state: JsonObject = {"hook": src, "spec": spec_md}
        qs = questions(f, rows)
        try:
            reply = check(state, qs)
        except JevError as exc:
            run["jev_error"] = {"code": exc.code, "message": str(exc)}
        else:
            answers = reply.answers
            run["jev"] = {"answers": answers, "findings": findings(answers, f),
                          "input": dataclasses.asdict(input_record(state, qs, reply.input_tokens, None, 0)),
                          "no": sorted(k for k, a in answers.items() if a.get("choice") != "yes")}
    run["pass"] = not run["deterministic_failures"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(run, indent=2) + "\n")
    print(json.dumps({"pass": run["pass"], "out": str(out), "deterministic_failures": run["deterministic_failures"],
                      "jev_no": run["jev"] and run["jev"]["no"], "jev_error": run.get("jev_error")}, indent=2))
    return 0 if run["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
