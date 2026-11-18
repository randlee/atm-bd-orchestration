#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.8.0,<2"]
# ///
# pyright: strict
"""Bounded Jev transport and startup probe for the proposed sanity agent."""
import argparse
from collections.abc import Callable
from email.utils import parsedate_to_datetime
import hashlib
import hmac
import http.client
import json
import re
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Literal, NotRequired, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "atm-beads/scripts"))
import repo_config
import phase_settings as phase_settings_module
from operation_models import matches_typeddict
from sprint_index_common import JsonObject, JsonValue, is_json_object, is_json_value, string_list

MODEL = "jev-1.13.0"
HOST = "api.typesafe.ai"
MAX_REQUEST_BYTES = 96000  # Jev documents 32k state tokens of a 64k request budget; ~3 bytes per token of code.
MAX_RESPONSE_BYTES = 1048576
# A request gets at most four transient-error attempts.
MAX_JEV_ATTEMPTS = 4


class JevError(Exception):
    def __init__(self, code: str, message: str, recoverable: bool = False) -> None:
        super().__init__(message)
        self.code, self.message, self.recoverable = code, message, recoverable
        self.size: int | None = None
        self.fix: str | None = None


REPORT = "Report this error unchanged; the coordinator records the slot unavailable."
RETRY = "The client retry budget is exhausted. " + REPORT
REBUILD = "Split the sprint into subtask beads or move samples into reference beads, then retry; report the refusal to the coordinator."
CONTEXT_RANGE = re.compile(r"(?P<path>.+):(?P<start>[0-9]+)-(?P<end>[0-9]+)")  # a `context` entry naming lines
FENCED = re.compile(r"\s*```(?:json)?[ \t]*\n(.*?)\n```\s*", re.S)  # an assignment as received: fenced JSON
FIXES = (  # message prefix -> what the calling agent does next
    ("TYPESAFE_API_KEY is missing", "No Jev call is possible without TYPESAFE_API_KEY. " + REPORT),
    ("TYPESAFE_API_KEY has invalid formatting", "TYPESAFE_API_KEY holds whitespace, quotes or control characters. " + REPORT),
    ("Assignment lacks", "Write the assignment you received unchanged: it needs `deliverable.text`, `worktree_path`, "
     "`commit`, `base_sha`, `changed_files` and `context`. If the received assignment lacks one, " + REPORT[0].lower() + REPORT[1:]),
    ("Committed evidence unreadable", "Run `git -C <worktree_path> fetch origin` so `commit` and `base_sha` exist, then run "
     "the same command again. If it still fails, a `changed_files` or `context` path is missing at `commit`: " + REPORT[0].lower() + REPORT[1:]),
    ("Assignment external_evidence", "Each `external_evidence` entry is one of {\"kind\": \"bead_notes\", \"bead\": <id>, \"text\": <notes>}, "
     "{\"kind\": \"pr_body\", \"repo\": \"owner/name\", \"pr\": <n>} or {\"kind\": \"pr_comment\", \"repo\": "
     "\"owner/name\", \"comment_id\": <n>}. If the received assignment holds another shape, " + REPORT[0].lower() + REPORT[1:]),
    ("External evidence reference is invalid", "Use inline `bead_notes` with `kind`, `bead` and string `text`, or a valid `pr_body`/`pr_comment` reference. "
     + REPORT),
    ("External evidence unreadable", "Run `gh api` for the PR or comment, fix what it reports (`gh auth status`), "
     "then run the same command again. If it still fails, "
     + REPORT[0].lower() + REPORT[1:]),
    ("Context entry", "Fix that `context` entry: `path:start-end` names lines 1 <= start <= end <= the file's line "
     "count at `commit`; a plain `path` sends the whole file. Then run the same command again."),
    ("Request file unavailable", "Write the file as the JSON object you were given, outside the worktree, and run the command again."),
    ("Jev connection failed", RETRY),
    ("Jev retry budget exhausted", RETRY),
)


def suggested_action(exc: JevError) -> str:
    if exc.message.startswith("Jev request oversized"):
        return getattr(exc, "fix", None) or REPORT
    if exc.message.startswith("Jev HTTP"):
        return RETRY if exc.recoverable else "Jev rejected the request or the key. " + REPORT
    return next((fix for prefix, fix in FIXES if exc.message.startswith(prefix)), REPORT)


def failure(exc: JevError) -> JsonObject:
    return {"success": False, "data": None, "error": {
        "code": exc.code, "message": exc.message, "recoverable": exc.recoverable,
        "suggested_action": suggested_action(exc),
    }}


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise JevError("SANITY.JEV_UNAVAILABLE", "TYPESAFE_API_KEY is missing; no Jev evaluation ran", True)
    if not key.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in key):
        raise JevError("SANITY.JEV_UNAVAILABLE", "TYPESAFE_API_KEY has invalid formatting")
    return key


def probability(value: JsonValue) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1)


class ChoiceAnswer(TypedDict):
    type: str
    choice: str
    confidence: int | float
    probabilities: dict[str, int | float]


class ValidatedResponse(TypedDict):
    answers: dict[str, ChoiceAnswer]
    raw: JsonObject


def parse_choice_answer(answer: JsonValue, options: set[str]) -> ChoiceAnswer:
    if not isinstance(answer, dict):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Answer must be an object")
    if (not matches_typeddict(answer, ChoiceAnswer) or answer["type"] != "choice"
            or answer["choice"] not in options or not probability(answer["confidence"])):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Invalid Choice answer")
    probs = answer["probabilities"]
    if (set(probs) != options
            or not all(probability(p) for p in probs.values())
            or abs(sum(probs.values()) - 1) > 0.001):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Invalid Choice answer")
    return answer


def parse_response(value: JsonValue, request: JsonObject) -> ValidatedResponse:
    if not isinstance(value, dict) or value.get("model") != MODEL:
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Unexpected Jev response model or shape")
    answers = value.get("answers")
    questions = request.get("questions")
    if not isinstance(questions, dict) or not isinstance(answers, dict) or set(answers) != set(questions):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Missing or unexpected answer IDs")
    parsed_answers: dict[str, ChoiceAnswer] = {}
    for name, question in questions.items():
        if not isinstance(question, dict) or not isinstance(question.get("criteria"), dict):
            raise JevError("SANITY.JEV_RESPONSE_INVALID", "Invalid Choice answer")
        criteria = question["criteria"]
        assert isinstance(criteria, dict)
        parsed_answers[name] = parse_choice_answer(answers[name], set(criteria))
    return {"answers": parsed_answers, "raw": value}


def validate_response(value: JsonValue, request: JsonObject) -> JsonObject:
    return parse_response(value, request)["raw"]


class ChoiceQuestion(TypedDict):
    type: str
    instructions: str | dict[str, JsonValue] | list[JsonValue]
    criteria: JsonObject


class ValidatedRequest(TypedDict):
    state: JsonValue
    questions: dict[str, ChoiceQuestion]
    raw: JsonObject


def parse_request(request: JsonValue) -> ValidatedRequest:
    if (not isinstance(request, dict) or request.get("model") != MODEL
            or not isinstance(request.get("state"), (str, dict, list))
            or not isinstance(request.get("questions"), dict) or not request["questions"]):
        raise JevError("VALIDATION.INPUT", "Expected pinned model, state and nonempty questions")
    questions = request["questions"]
    assert isinstance(questions, dict)
    if not is_json_object(questions):
        raise JevError("VALIDATION.INPUT", "Pilot supports well-formed Choice questions only")
    parsed_questions: dict[str, ChoiceQuestion] = {}
    for name, q in questions.items():
        if (not name or not matches_typeddict(q, ChoiceQuestion) or q["type"] != "choice"
                or not 2 <= len(q["criteria"]) <= 255 or not all(q["criteria"])
                or not all(v is None or isinstance(v, (str, dict, list)) for v in q["criteria"].values())):
            raise JevError("VALIDATION.INPUT", "Pilot supports well-formed Choice questions only")
        parsed_questions[name] = q
    return {"state": request["state"], "questions": parsed_questions, "raw": request}


def validate_request(request: JsonValue) -> bytes:
    return encode_request(parse_request(request))


def encode_request(parsed: ValidatedRequest) -> bytes:
    try:
        body = json.dumps(parsed["raw"], allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        raise JevError("VALIDATION.INPUT", "Request must contain finite JSON values") from None
    if len(body) > MAX_REQUEST_BYTES:
        raise oversize(parsed["raw"])
    return body


def parse_response_for_request(value: JsonValue, request: ValidatedRequest) -> ValidatedResponse:
    if not isinstance(value, dict) or value.get("model") != MODEL:
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Unexpected Jev response model or shape")
    answers = value.get("answers")
    questions = request["questions"]
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Missing or unexpected answer IDs")
    parsed = {name: parse_choice_answer(answers[name], set(question["criteria"]))
              for name, question in questions.items()}
    return {"answers": parsed, "raw": value}


def retry_delay(retry_after: str | None) -> float:
    if retry_after is None:
        return 1.0
    try:
        delay = float(retry_after)
    except (TypeError, ValueError):
        try:
            delay = parsedate_to_datetime(retry_after).timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            return 30.0
    return min(30.0, max(0.0, delay)) if math.isfinite(delay) else 30.0


def evaluate(request: JsonObject, *, sleep: Callable[[float], None] | None = None,
             max_attempts: int = MAX_JEV_ATTEMPTS) -> JsonObject:
    parsed_request = parse_request(request)
    body = encode_request(parsed_request)
    key = api_key()
    sleeper = sleep or time.sleep
    remaining = min(max_attempts, MAX_JEV_ATTEMPTS)
    while remaining > 0:
        remaining -= 1
        conn = None
        try:
            conn = http.client.HTTPSConnection(HOST, timeout=20)
            conn.request("POST", "/v1/systemone", body=body, headers={
                "Authorization": "Bearer " + key, "Content-Type": "application/json",
            })
            response = conn.getresponse()
            status = response.status
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            retry_after = response.getheader("Retry-After")
        except (OSError, socket.timeout, http.client.HTTPException):
            if remaining > 0:
                continue
            raise JevError("SANITY.JEV_UNAVAILABLE", "Jev connection failed or timed out", True) from None
        finally:
            if conn is not None:
                conn.close()
        error_type = jev_error_type(raw) if 400 <= status < 500 else None
        if status == 413:
            raise oversize(request)
        if error_type == "max_tokens_exceeded":
            raise oversize(request, limit="over Jev's token limit")
        if status in (429, 502, 529) and remaining > 0:
            delay = retry_delay(retry_after)
            if delay:
                sleeper(delay)
            continue
        if status != 200:
            named = f" error_type={error_type}" if error_type else ""
            raise JevError("SANITY.JEV_UNAVAILABLE", f"Jev HTTP {status}{named}; response body withheld",
                           status in (429, 502, 529))
        if len(raw) > MAX_RESPONSE_BYTES:
            raise JevError("SANITY.JEV_RESPONSE_INVALID", "Jev response exceeded size limit")
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError):
            raise JevError("SANITY.JEV_RESPONSE_INVALID", "Jev response was not JSON") from None
        if not is_json_value(value):
            raise JevError("SANITY.JEV_RESPONSE_INVALID", "Unexpected Jev response model or shape")
        return parse_response_for_request(value, parsed_request)["raw"]
    raise JevError("SANITY.JEV_UNAVAILABLE", "Jev retry budget exhausted", True)


# Every failure message this client writes. A Jev failure envelope must carry one verbatim (sanity-merge checks it).
CLIENT_MESSAGES = re.compile("|".join([
    r"TYPESAFE_API_KEY is missing; no Jev evaluation ran", r"TYPESAFE_API_KEY has invalid formatting",
    r"Unexpected Jev response model or shape", r"Missing or unexpected answer IDs", r"Answer must be an object",
    r"Invalid Choice answer", r"Expected pinned model, state and nonempty questions",
    r"Pilot supports well-formed Choice questions only", r"Request must contain finite JSON values",
    r"Jev request oversized \(\d+ bytes (> \d+|over Jev's token limit)\); split into subtask beads or move samples to reference beads",
    r"Jev connection failed or timed out", r"Jev HTTP \d{3}( error_type=[a-z0-9_.-]+)?; response body withheld",
    r"Jev response exceeded size limit", r"Jev response was not JSON", r"Jev retry budget exhausted",
    r"Startup probe returned the wrong literal choice", r"Request file unavailable or invalid JSON",
    r"Assignment lacks deliverable text, worktree, commits or file lists",
    r"Committed evidence unreadable at the pinned commits",
    r"Assignment external_evidence entry is not a bead_notes, pr_body or pr_comment reference",
    r"External evidence reference is invalid",
    r"External evidence unreadable: \S+ \S+",
    r"Context entry .+ names lines outside its file at the pinned commit",
]))


def is_client_message(message: JsonValue) -> bool:
    return isinstance(message, str) and CLIENT_MESSAGES.fullmatch(message) is not None


def canonical(value: JsonValue) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def receipt_mac(body: JsonObject, key: str) -> str:
    return hmac.new(key.encode("utf-8"), canonical({k: body[k] for k in RECEIPT_KEYS if k != "mac"}), hashlib.sha256).hexdigest()


class ReceiptInput(TypedDict):
    model: JsonValue
    question: str
    choice: JsonValue
    probabilities: JsonValue
    response_id: str | None


class ReceiptAnswer(TypedDict):
    choice: JsonValue
    probabilities: JsonValue


class ReceiptResponse(TypedDict):
    model: JsonValue
    id: NotRequired[JsonValue]


def parse_receipt_input(request: JsonObject, response: JsonObject) -> ReceiptInput:
    questions, answers = request.get("questions"), response.get("answers")
    if not isinstance(questions, dict) or len(questions) != 1 or not isinstance(answers, dict):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Missing or unexpected answer IDs")
    (name,) = questions
    answer = answers.get(name)
    if not matches_typeddict(answer, ReceiptAnswer) or not matches_typeddict(response, ReceiptResponse):
        raise JevError("SANITY.JEV_RESPONSE_INVALID", "Invalid Choice answer")
    response_id = response.get("id")
    return {"model": response["model"], "question": name, "choice": answer["choice"],
            "probabilities": answer["probabilities"],
            "response_id": response_id if isinstance(response_id, str) else None}


def receipt(request: JsonObject, response: JsonObject, key: str) -> JsonObject:
    """What a caller copies to show this call happened: the one question's answer, bound to the request and keyed with
    the API key, so it cannot be written without the call."""
    parsed = parse_receipt_input(request, response)
    body: JsonObject = {"model": parsed["model"], "question": parsed["question"], "choice": parsed["choice"],
            "probabilities": parsed["probabilities"], "response_id": parsed["response_id"],
            "request_sha256": hashlib.sha256(canonical(request)).hexdigest()}
    return {**body, "mac": receipt_mac({**body, "mac": None}, key)}


class ReceiptToVerify(TypedDict):
    model: JsonValue
    question: JsonValue
    choice: JsonValue
    probabilities: JsonValue
    response_id: JsonValue
    request_sha256: JsonValue
    mac: str


RECEIPT_KEYS = tuple(ReceiptToVerify.__annotations__)


def parse_receipt(value: JsonValue) -> ReceiptToVerify | None:
    """Extract the MAC; retain signed fields exactly as received for verification."""
    if not matches_typeddict(value, ReceiptToVerify) or set(value) != set(ReceiptToVerify.__required_keys__):
        return None
    return value


def verify_receipt(value: JsonValue, key: str) -> bool:
    if not isinstance(value, dict) or not key:
        return False
    parsed = parse_receipt(value)
    if parsed is None:
        return False
    return hmac.compare_digest(parsed["mac"], receipt_mac(value, key))


def startup_request() -> JsonObject:
    # Synthetic state only: no repository source is sent during startup.
    return {"model": MODEL, "state": {"marker": "ready"}, "questions": {
        "startup": {"type": "choice", "instructions": "Which literal value is in state.marker?",
                    "criteria": {"ready": "marker equals ready", "other": "marker differs"}},
    }}


def written_request(text: str, evidence: str, context: dict[str, str] | None = None,
                    external: list[JsonObject] | None = None) -> JsonObject:
    state: JsonObject = {"deliverable": text, "evidence": evidence}
    if context:
        state["context"] = {key: value for key, value in context.items()}
    if external:
        state["external_evidence"] = [*external]
    instructions = "Does the committed evidence deliver the deliverable?"
    return {"model": MODEL, "state": state, "questions": {"written": {
        "type": "choice", "instructions": instructions, "criteria": {"yes": "delivered", "no": "not delivered"}}}}


def jev_error_type(raw: bytes) -> str | None:
    """`detail.error_type` from a Jev 4xx body (e.g. max_tokens_exceeded); only that short identifier leaves the
    client, never the rest of the body."""
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return None
    detail = value.get("detail") if is_json_object(value) else None
    error_type = detail.get("error_type") if is_json_object(detail) else None
    return error_type if isinstance(error_type, str) and re.fullmatch(r"[a-z0-9_.-]{1,64}", error_type) else None


def size(request: JsonValue) -> int:
    return len(json.dumps(request, allow_nan=False).encode("utf-8"))


def oversize(request: JsonValue, fix: str | None = None, limit: str | None = None) -> JevError:
    request_size = size(request)
    bound = limit or f"> {MAX_REQUEST_BYTES}"
    exc = JevError("SANITY.JEV_REQUEST_TOO_LARGE", f"Jev request oversized ({request_size} bytes {bound}); split into subtask beads or move samples to reference beads", True)
    exc.size = request_size
    exc.fix = fix.format(size=exc.size) if fix else REBUILD
    return exc


class BeadNotesReference(TypedDict):
    kind: Literal["bead_notes"]
    bead: str
    text: str


class PullRequestReference(TypedDict):
    kind: Literal["pr_body"]
    repo: str
    pr: int


class CommentReference(TypedDict):
    kind: Literal["pr_comment"]
    repo: str
    comment_id: int


EvidenceReference = BeadNotesReference | PullRequestReference | CommentReference


class GitHubEvidence(TypedDict):
    text: str
    url: JsonValue
    updated_at: JsonValue
    author: JsonValue


def parse_github_evidence(value: JsonValue, kind: str, label: str) -> GitHubEvidence:
    if isinstance(value, dict) and "body" in value and value["body"] is None:
        value = {**value, "body": ""}  # GitHub uses null for an empty description.
    if not isinstance(value, dict) or not isinstance(value.get("body"), str):
        raise JevError("VALIDATION.INPUT", f"External evidence unreadable: {kind} {label}")
    body = value["body"]
    assert isinstance(body, str)
    user = value.get("user")
    return {"text": body, "url": value.get("html_url"), "updated_at": value.get("updated_at"),
            "author": user.get("login") if isinstance(user, dict) else None}


def evidence_ref(ref: JsonValue) -> bool:
    """True for one well-formed `external_evidence` reference."""
    return parse_evidence_ref(ref) is not None


def parse_evidence_ref(ref: JsonValue) -> EvidenceReference | None:
    if (matches_typeddict(ref, BeadNotesReference) and set(ref) == set(BeadNotesReference.__required_keys__)
            and ref["bead"] and not ref["bead"].startswith("-")):
        return ref
    if (matches_typeddict(ref, PullRequestReference) and set(ref) == set(PullRequestReference.__required_keys__)
            and ref["repo"] and not ref["repo"].startswith("-") and "{" not in ref["repo"] and ref["pr"] > 0):
        return ref
    if (matches_typeddict(ref, CommentReference) and set(ref) == set(CommentReference.__required_keys__)
            and ref["repo"] and not ref["repo"].startswith("-") and "{" not in ref["repo"] and ref["comment_id"] > 0):
        return ref
    return None


def external_evidence(ref: JsonObject, worktree: str) -> JsonObject:
    """Inline bead notes or a PR body/comment fetched here, labelled with where it came from."""
    ref["kind"]  # Preserve the missing-kind error for callers of this function.
    parsed = parse_evidence_ref(ref)
    if parsed is None:
        raise JevError("VALIDATION.INPUT", "External evidence reference is invalid")
    return external_evidence_from_ref(parsed, worktree)


def external_evidence_from_ref(parsed: EvidenceReference, worktree: str) -> JsonObject:
    kind = parsed["kind"]
    if parsed["kind"] == "bead_notes":
        return {"kind": kind, "ref": parsed["bead"], "url": None, "updated_at": None,
                "author": None, "text": parsed["text"]}
    repo = parsed["repo"]
    number = parsed["pr"] if parsed["kind"] == "pr_body" else parsed["comment_id"]
    label = f"{repo}#{number}"
    argv = (["gh", "api", f"repos/{repo}/pulls/{number}"] if kind == "pr_body" else
            ["gh", "api", f"repos/{repo}/issues/comments/{number}"])
    try:
        proc = subprocess.run(argv, cwd=worktree, capture_output=True, text=True, timeout=60)
        value: JsonValue = json.loads(proc.stdout) if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        value = None
    evidence = parse_github_evidence(value, kind, label)
    return {"kind": kind, "ref": label, "url": evidence["url"], "updated_at": evidence["updated_at"],
            "author": evidence["author"], "text": evidence["text"]}


class EvidenceAssignment(TypedDict):
    text: str
    worktree: str
    commit: str
    base: str
    changed: list[str]
    context: list[str]
    refs: list[EvidenceReference]


def parse_evidence_assignment(assignment: JsonValue) -> EvidenceAssignment:
    if not isinstance(assignment, dict):
        raise JevError("VALIDATION.INPUT", "Assignment lacks deliverable text, worktree, commits or file lists") from None
    deliverable = assignment.get("deliverable")
    text = deliverable.get("text") if isinstance(deliverable, dict) else None
    worktree, commit, base = assignment.get("worktree_path"), assignment.get("commit"), assignment.get("base_sha")
    changed, context = assignment.get("changed_files"), assignment.get("context")
    if (not isinstance(text, str) or not text or not isinstance(worktree, str) or not worktree
            or not isinstance(commit, str) or not commit or not isinstance(base, str) or not base
            or not string_list(changed) or not all(changed) or not string_list(context) or not all(context)):
        raise JevError("VALIDATION.INPUT", "Assignment lacks deliverable text, worktree, commits or file lists") from None
    refs = assignment.get("external_evidence", [])
    if not isinstance(refs, list):
        raise JevError("VALIDATION.INPUT", "Assignment external_evidence entry is not a bead_notes, pr_body or pr_comment reference")
    parsed_refs: list[EvidenceReference] = []
    for ref in refs:
        parsed = parse_evidence_ref(ref)
        if parsed is None:
            raise JevError("VALIDATION.INPUT", "Assignment external_evidence entry is not a bead_notes, pr_body or pr_comment reference")
        parsed_refs.append(parsed)
    return {"text": text, "worktree": worktree, "commit": commit, "base": base,
            "changed": changed, "context": context, "refs": parsed_refs}


def assignment_requests(assignment: JsonValue) -> list[JsonObject]:
    """The sanity requests, built from the assignment so no agent writes them: the deliverable text verbatim, the
    committed diff of the changed files and the context entries at the pinned commit (a `path:start-end` entry only
    those lines, labelled with the entry). An oversized full request is refused without splitting."""
    parsed = parse_evidence_assignment(assignment)
    text, worktree, commit, base = parsed["text"], parsed["worktree"], parsed["commit"], parsed["base"]
    changed, context, refs = parsed["changed"], parsed["context"], parsed["refs"]

    def git(*args: str) -> str:
        proc = subprocess.run(["git", "-C", worktree, *args], capture_output=True, text=True)
        if proc.returncode:
            raise JevError("VALIDATION.INPUT", "Committed evidence unreadable at the pinned commits")
        return proc.stdout

    def diff(*paths: str) -> str:
        return git("diff", "--no-color", f"{base}...{commit}", "--", *paths) if paths else ""

    def excerpt(entry: str) -> str:
        """A plain path's whole file at `commit`, or only lines start..end (1-based, inclusive) of `path:start-end`."""
        lines = CONTEXT_RANGE.fullmatch(entry)
        if not lines:
            return git("show", f"{commit}:{entry}")
        text, start, end = git("show", f"{commit}:{lines['path']}"), int(lines["start"]), int(lines["end"])
        kept = text.splitlines(keepends=True)
        if not 1 <= start <= end <= len(kept):
            raise JevError("VALIDATION.INPUT", f"Context entry {entry} names lines outside its file at the pinned commit")
        return "".join(kept[start - 1:end])

    external = [external_evidence_from_ref(ref, worktree) for ref in refs]
    request = written_request(text, diff(*changed), {entry: excerpt(entry) for entry in context}, external=external)
    if size(request) > MAX_REQUEST_BYTES:
        raise oversize(request)
    return [request]


class EscalationList(TypedDict):
    recipients: list[str]


def parse_escalation_list(value: JsonValue) -> EscalationList:
    recipients = value.get("recipients") if isinstance(value, dict) else None
    return {"recipients": [item for item in recipients if isinstance(item, str) and item]
            if isinstance(recipients, list) else []}


def escalation_recipients(team: str | None = None) -> list[str]:
    """Read a team's escalation list, or the daemon default when no team is supplied."""
    argv = ["atm", "escalation", "list"]
    if team:
        argv.extend(("--team", team))
    argv.append("--json")
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=15)
        value: JsonValue = json.loads(result.stdout) if result.returncode == 0 else {}
    except (OSError, subprocess.TimeoutExpired, ValueError):
        value = {}
    return parse_escalation_list(value)["recipients"]


def oversight_recipients(settings: phase_settings_module.PhaseSettings) -> tuple[list[str], bool]:
    """Use phase oversight, then daemon oversight, then the lead with an explicit fallback note."""
    recipients = escalation_recipients(settings.team)
    if recipients:
        return recipients, False
    recipients = escalation_recipients()
    if recipients:
        return recipients, False
    return [f"{settings.lead}@{settings.team}"], True


def announce(message: str, recipients: list[str], tool_identity: str, *, no_recipient_fallback: bool = False) -> None:
    """Send `message` to oversight as the repository-configured atm-bd tool identity."""
    if no_recipient_fallback:
        message = f"No escalation recipient is set; sending to the phase lead. {message}"
    for recipient in recipients:
        try:
            sent = subprocess.run(["atm", "send", recipient, "--as", tool_identity, "--stdin"], input=message,
                                  text=True, capture_output=True, timeout=15)
            if sent.returncode:
                print(f"Announcement to {recipient} failed; coordinator must report the error via ATM.", file=sys.stderr)
        except (OSError, subprocess.TimeoutExpired):
            print(f"Announcement to {recipient} unavailable; coordinator must report the error via ATM.", file=sys.stderr)


class JevArguments(argparse.Namespace):
    startup: bool
    request: Path | None
    assignment: Path | None
    error: str | None
    announce: bool
    phase: str | None


class StartupProbe(TypedDict):
    ready: bool


def parse_startup_probe(value: JsonObject) -> StartupProbe:
    answers = value.get("answers")
    startup = answers.get("startup") if isinstance(answers, dict) else None
    return {"ready": isinstance(startup, dict) and startup.get("choice") == "ready"}


def evaluation_result(args: JevArguments, *, clock: Callable[[], float] = time.monotonic,
                      sleep: Callable[[float], None] | None = None) -> JsonObject:
    elapsed_s: float | None = None
    assignment: JsonValue = None
    try:
        if args.startup:
            request = startup_request()
        elif args.assignment:
            text = args.assignment.read_text()
            fenced = FENCED.fullmatch(text)
            assignment = json.loads(fenced.group(1) if fenced else text)
            if not is_json_value(assignment):
                raise JevError("VALIDATION.INPUT", "Assignment lacks deliverable text, worktree, commits or file lists")
            request = assignment_requests(assignment)[0]
        else:
            assert args.request is not None
            raw_request: JsonValue = json.loads(args.request.read_text())
            if not isinstance(raw_request, dict):
                validate_request(raw_request)
                raise JevError("VALIDATION.INPUT", "Expected pinned model, state and nonempty questions")
            request = raw_request
        started = clock()
        try:
            data: JsonObject
            data = evaluate(request, sleep=sleep)
        finally:
            elapsed_s = max(0.0, clock() - started)
        questions = parse_request(request)["questions"]
        if not args.startup and len(questions) == 1 and "receipt" not in data:
            data = {**data, "receipt": receipt(request, data, api_key())}
        if args.startup:
            probe = parse_startup_probe(data)
            if not probe["ready"]:
                raise JevError("SANITY.JEV_RESPONSE_INVALID", "Startup probe returned the wrong literal choice")
            data = {"model": MODEL, "status": "ready", "scope": "authenticated synthetic probe only; sanity accuracy unverified"}
        result: JsonObject = {"success": True, "data": data, "error": None}
    except JevError as exc:
        result = failure(exc)
    except (OSError, ValueError, UnicodeError):
        result = failure(JevError("VALIDATION.INPUT", "Request file unavailable or invalid JSON"))
    result["elapsed_s"] = elapsed_s if elapsed_s is not None else 0.0
    return result


def main(argv: list[str] | None = None, *, clock: Callable[[], float] = time.monotonic,
         sleep: Callable[[float], None] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--startup", action="store_true")
    mode.add_argument("--request", type=Path)
    mode.add_argument("--assignment", type=Path, help="a sanity assignment (fenced JSON body); the client builds the request")
    mode.add_argument("--error", help="with --announce: announce this JEV child error verbatim; no probe runs")
    parser.add_argument("--announce", action="store_true",
                        help="with --startup or --error: send a failure to ATM's escalation recipients (else the phase lead)")
    parser.add_argument("--phase", help="phase whose tracked settings name the lead; required with --announce")
    args = parser.parse_args(argv, namespace=JevArguments())
    if args.announce and (args.request or args.assignment or not args.phase):
        parser.error("--announce requires --startup or --error and an explicit --phase")
    if args.error is not None and (not args.announce or not args.error.strip()):
        parser.error("--error requires --announce and a nonempty error")
    recipients: list[str] = []
    no_recipient_fallback = False
    tool_identity = None
    if args.phase:
        try:
            settings = phase_settings_module.phase_settings(repo_config.repo_root(), args.phase)
            if args.announce:
                recipients, no_recipient_fallback = oversight_recipients(settings)
            tool_identity = settings.tool_identity
        except (repo_config.ConfigError, RuntimeError, OSError, ValueError) as exc:
            parser.error(str(exc))
    if args.error is not None:
        assert recipients and tool_identity is not None
        if args.error.startswith("SANITY.JEV_REQUEST_TOO_LARGE"):
            # An oversized request is the caller's to rebuild; it never hands the slot to an LLM or haiku check (#365).
            announce(f"dev-sanity Jev request oversized: {args.error}. The deliverable's Jev slot "
                     "keeps this error; no LLM or haiku check replaces Jev for it.", recipients, tool_identity,
                     no_recipient_fallback=no_recipient_fallback)
        else:
            announce(f"dev-sanity Jev child failed: {args.error}. Selection takes the LLM reply for JEV slots until a Jev child succeeds.",
                     recipients, tool_identity, no_recipient_fallback=no_recipient_fallback)
        print(json.dumps({"success": True, "data": {"announced": args.error}, "error": None}))
        return 0
    result = evaluation_result(args, clock=clock, sleep=sleep)
    if args.announce and not result["success"]:
        assert recipients and tool_identity is not None
        error = result["error"]
        assert isinstance(error, dict)
        announce(f"dev-sanity Jev startup failed: {error['code']}: {error['message']}. No sc-sanity-jev checks run; dev-sanity records every JEV slot as unavailable until a startup probe passes.",
                 recipients, tool_identity, no_recipient_fallback=no_recipient_fallback)
    print(json.dumps(result, allow_nan=False))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    sys.exit(main())
