"""Transport/contract failures must not become a successful sanity check."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from subprocess_helpers import (
    isolated_git_env,
    run_fixture_git,
    set_fixture_hooks_path,
)

spec = importlib.util.spec_from_file_location("jev_client", Path(__file__).parents[1] / "jev_client.py")
assert spec is not None and spec.loader is not None
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "atm-beads/tests"))
from phase_fixtures import write_phase


def reply():
    return {"model": client.MODEL, "answers": {"startup": {
        "type": "choice", "choice": "ready", "confidence": 0.99,
        "probabilities": {"ready": 1.0, "other": 0.0},
    }}, "usage": {"input_tokens": 1, "output_tokens": 1}}


def no_sleep(delay):
    raise AssertionError(f"Unexpected retry delay: {delay}")


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.waits = []

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.advance(seconds)


class JevClientTests(unittest.TestCase):
    def fixture_repo(self, root):
        root = Path(root)
        repo = root / "repo"
        repo.mkdir()
        env, _ = isolated_git_env(root)
        self.git(repo, env, "init", "-q")
        set_fixture_hooks_path(repo, env=env)
        return repo, env

    def git(self, repo, env, *args):
        return run_fixture_git(
            ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            env=env,
        ).stdout.strip()

    def test_missing_key_no_network(self):
        with patch.dict(client.os.environ, {}, clear=True), patch.object(client.http.client, "HTTPSConnection") as http:
            with self.assertRaises(client.JevError):
                client.evaluate(client.startup_request(), sleep=no_sleep)
            http.assert_not_called()

    def startup(self, argv, team, daemon, environ=None, phase_lead="appointed-lead", tool_identity="atm-bd@tool"):
        """Run the startup probe with an explicit repository and phase configuration."""
        def run(cmd, **kwargs):
            if "--team" in cmd:
                requested_team = cmd[cmd.index("--team") + 1]
                recipients = team if requested_team == "phase-team" else []
            else:
                recipients = daemon
            return MagicMock(returncode=0 if recipients is not None else 1, stdout=json.dumps({"recipients": recipients or []}))
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            write_phase(repo, "x", lead=phase_lead)
            phase_path = repo / ".atm-bd" / "phase-x.toml"
            phase_text = phase_path.read_text()
            phase_path.write_text(phase_text.replace("\n[templates]", '\nteam = "phase-team"\n\n[templates]'))
            config = repo / ".claude/project/atm-bd-orchestration.yaml"
            config.parent.mkdir(parents=True)
            config.write_text(f"tool_identity: {tool_identity}\n")
            return self.run_startup(argv, environ, repo, run)

    def run_startup(self, argv, environ, repo, run):
        with patch.dict(client.os.environ, environ if environ is not None else {"ATM_TEAM": "t"}, clear=True), \
             patch.object(client.repo_config, "repo_root", return_value=repo), \
             patch.object(client.subprocess, "run", side_effect=run) as send:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = client.main(argv, sleep=no_sleep)
        sends = [(c.args[0][2], c.kwargs["input"], c.args[0]) for c in send.call_args_list if c.args[0][:2] == ["atm", "send"]]
        return rc, json.loads(output.getvalue()), sends

    def test_startup_announcement_uses_configured_phase_recipients_despite_conflicting_environment(self):
        rc, result, sends = self.startup(["--startup", "--announce", "--phase", "x"],
                                         ["oversight-one@phase-team", "oversight-two@phase-team"], ["daemon@host"],
                                         environ={"ATM_TEAM": "conflicting-team"})
        self.assertEqual(rc, 2)
        self.assertTrue(result["error"]["recoverable"])
        self.assertEqual(set(result["error"]), {"code", "message", "recoverable", "suggested_action"})
        self.assertEqual([to for to, _, _ in sends], ["oversight-one@phase-team", "oversight-two@phase-team"])
        for _, text, argv in sends:
            self.assertIn(result["error"]["message"], text)
            self.assertEqual(argv[argv.index("--as") + 1], "atm-bd@tool")
        self.assertEqual(len(sends), 2)

    def test_announcement_falls_back_to_daemon_recipients(self):
        _, _, sends = self.startup(["--startup", "--announce", "--phase", "x"], [], ["daemon-one@host", "daemon-two@host"])
        self.assertEqual([to for to, _, _ in sends], ["daemon-one@host", "daemon-two@host"])

    def test_announcement_uses_repository_tool_identity_override(self):
        _, _, sends = self.startup(["--startup", "--announce", "--phase", "x"], [], None,
                                   tool_identity="custom-bot@tools")
        self.assertEqual(sends[0][2][sends[0][2].index("--as") + 1], "custom-bot@tools")

    def test_startup_without_announce_sends_nothing(self):
        rc, _, sends = self.startup(["--startup"], ["oversight@team"], ["daemon@host"])
        self.assertEqual((rc, sends), (2, []))
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            client.main(["--startup", "--announce"], sleep=no_sleep)

    def test_an_oversized_request_error_is_announced_without_an_llm_fallback(self):
        error = "SANITY.JEV_REQUEST_TOO_LARGE: Jev request oversized (123456 bytes > 96000); no further split fits the remaining attempt budget"
        with patch.object(client.http.client, "HTTPSConnection") as http:
            rc, result, sends = self.startup(["--announce", "--error", error, "--phase", "x"], ["oversight@team"], ["daemon@host"],
                                             environ={"ATM_TEAM": "t", "TYPESAFE_API_KEY": "test-only-key"})
            http.assert_not_called()
        self.assertEqual((rc, result), (0, {"success": True, "data": {"announced": error}, "error": None}))
        text = sends[0][1]
        self.assertIn(error, text)
        self.assertIn("123456 bytes > 96000", text)
        self.assertIn("no LLM or haiku check replaces Jev", text)
        self.assertNotIn("Selection takes the LLM reply", text)

    def test_error_announces_a_child_failure_verbatim_without_probing(self):
        error = "SANITY.JEV_UNAVAILABLE: Jev HTTP 503; response body withheld"
        with patch.object(client.http.client, "HTTPSConnection") as http:
            rc, result, sends = self.startup(["--announce", "--error", error, "--phase", "x"], ["oversight@team"], ["daemon@host"],
                                             environ={"ATM_TEAM": "t", "TYPESAFE_API_KEY": "test-only-key"})
            http.assert_not_called()
        self.assertEqual((rc, result), (0, {"success": True, "data": {"announced": error}, "error": None}))
        self.assertEqual([to for to, _, _ in sends], ["oversight@team"])
        self.assertIn(error, sends[0][1])
        for argv in (["--error", error], ["--announce", "--error", "", "--phase", "x"],
                     ["--announce", "--error", error], ["--startup", "--error", error, "--announce", "--phase", "x"],
                     ["--request", "r.json", "--announce", "--phase", "x"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                client.main(argv, sleep=no_sleep)

    def test_announcement_falls_back_to_phase_lead_with_no_recipient_note(self):
        for lead in ("phase-owner-one", "phase-owner-two"):
            with self.subTest(lead=lead):
                _, _, sends = self.startup(["--startup", "--announce", "--phase", "x"], [], None,
                                           environ={"ATM_IDENTITY": "wrong-environment-lead"}, phase_lead=lead)
                self.assertEqual([recipient for recipient, _, _ in sends], [f"{lead}@phase-team"])
                self.assertIn("no escalation recipient is set", sends[0][1].lower())

    def test_missing_phase_settings_stop_before_probe_or_send(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            path = write_phase(repo, "x")
            for invalid in ("lead = ''\n", "not valid TOML"):
                with self.subTest(invalid=invalid):
                    path.write_text(invalid)
                    with patch.object(client.repo_config, "repo_root", return_value=repo), \
                         patch.object(client, "evaluate") as evaluate, \
                         patch.object(client.subprocess, "run") as send, \
                         contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit):
                        client.main(["--startup", "--announce", "--phase", "x"], sleep=no_sleep)
                    self.assertIn("phase-x.toml", stderr.getvalue())
                    evaluate.assert_not_called()
                    send.assert_not_called()

    def test_legacy_lead_override_is_rejected(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()) as stderr:
            client.main(["--startup", "--announce", "--lead", "wrong-lead"], sleep=no_sleep)
        self.assertIn("unrecognized arguments: --lead", stderr.getvalue())

    def test_successful_transport(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read.return_value = json.dumps(reply()).encode()
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), patch.object(client.http.client, "HTTPSConnection", return_value=conn):
            self.assertEqual(client.evaluate(client.startup_request(), sleep=no_sleep), reply())
        self.assertEqual(conn.request.call_args.args[:2], ("POST", "/v1/systemone"))
        conn.close.assert_called_once()

    def test_auth_error_does_not_echo_body_or_key(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 401
        conn.getresponse.return_value.read.return_value = b"test-only-key server details"
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), patch.object(client.http.client, "HTTPSConnection", return_value=conn):
            with self.assertRaises(client.JevError) as raised:
                client.evaluate(client.startup_request(), sleep=no_sleep)
        self.assertNotIn("test-only-key", str(raised.exception))
        self.assertFalse(raised.exception.recoverable)
        self.assertEqual(conn.request.call_count, 1)

    def test_retry_is_bounded(self):
        self.assertEqual(client.MAX_JEV_ATTEMPTS, 4)
        for transient in (429, 502, 529, OSError("down"), client.socket.timeout("late"),
                          client.http.client.HTTPException("broken")):
            with self.subTest(transient=transient):
                conn = MagicMock()
                if isinstance(transient, Exception):
                    conn.request.side_effect = transient
                else:
                    conn.getresponse.return_value.status = transient
                conn.getresponse.return_value.read.return_value = b"{}"
                conn.getresponse.return_value.getheader.return_value = "0"
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(client.startup_request(), sleep=no_sleep, max_attempts=99)
                self.assertEqual(conn.request.call_count, 4)
                self.assertEqual(conn.close.call_count, 4)
                self.assertTrue(raised.exception.recoverable)

    def test_transient_statuses_and_transport_retry_to_success(self):
        for transient in (429, 502, 529, "transport"):
            with self.subTest(transient=transient):
                conn = MagicMock()
                good = MagicMock(status=200)
                good.read.return_value = json.dumps(reply()).encode()
                bad = MagicMock(status=transient, getheader=MagicMock(return_value="0"))
                bad.read.return_value = b"{}"
                if transient == "transport":
                    conn.request.side_effect = [OSError("unavailable"), None]
                    conn.getresponse.return_value = good
                else:
                    conn.getresponse.side_effect = [bad, good]
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn):
                    self.assertEqual(client.evaluate(client.startup_request(), sleep=no_sleep), reply())
                self.assertEqual(conn.request.call_count, 2)

    def test_other_http_errors_are_terminal(self):
        for status in sorted(set(range(400, 600)) - {413, 429, 502, 529}):
            with self.subTest(status=status):
                conn = MagicMock()
                conn.getresponse.return_value.status = status
                conn.getresponse.return_value.read.return_value = b"private server response"
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(client.startup_request(), sleep=no_sleep)
                self.assertEqual(conn.request.call_count, 1)
                self.assertFalse(raised.exception.recoverable)
                self.assertEqual(raised.exception.message, f"Jev HTTP {status}; response body withheld")

    def test_invalid_responses_are_terminal(self):
        for raw in (b"x" * (client.MAX_RESPONSE_BYTES + 1), b"not-json", b"\xff",
                    json.dumps({**reply(), "model": "wrong"}).encode(),
                    json.dumps({**reply(), "answers": {}}).encode()):
            with self.subTest(raw_size=len(raw)):
                conn = MagicMock()
                conn.getresponse.return_value.status = 200
                conn.getresponse.return_value.read.return_value = raw
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(client.startup_request(), sleep=no_sleep)
                self.assertEqual(conn.request.call_count, 1)
                self.assertEqual(raised.exception.code, "SANITY.JEV_RESPONSE_INVALID")
                self.assertFalse(raised.exception.recoverable)

    def test_retry_after_is_honoured_and_capped_without_sleeping(self):
        conn = MagicMock()
        good = MagicMock(status=200)
        good.read.return_value = json.dumps(reply()).encode()
        busy = MagicMock(status=529, getheader=MagicMock(return_value="99"))
        busy.read.return_value = b"{}"
        conn.getresponse.side_effect = [busy, good]
        waits = []
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
             patch.object(client.http.client, "HTTPSConnection", return_value=conn):
            self.assertEqual(client.evaluate(client.startup_request(), sleep=waits.append), reply())
        self.assertEqual(waits, [30.0])
        self.assertEqual(conn.request.call_count, 2)








    def test_server_oversize_refuses_once_without_parts(self):
        request = client.written_request("delivery", "evidence")
        for status, body in ((413, b"{}"), (400, b'{"detail":{"error_type":"max_tokens_exceeded"}}')):
            with self.subTest(status=status):
                conn = MagicMock()
                conn.getresponse.return_value.status = status
                conn.getresponse.return_value.read.return_value = body
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(request, sleep=no_sleep)
                self.assertEqual(conn.request.call_count, 1)
                self.assertEqual(raised.exception.code, "SANITY.JEV_REQUEST_TOO_LARGE")
                self.assertIn("subtask beads", raised.exception.message)
                self.assertIn("reference beads", raised.exception.message)
                self.assertTrue(client.is_client_message(raised.exception.message))

    def test_4xx_names_the_parsed_error_type_and_nothing_else_from_the_body(self):
        cases = [(400, b'{"detail":{"error_type":"invalid_request","msg":"private"}}',
                  "Jev HTTP 400 error_type=invalid_request; response body withheld"),
                 (401, b'{"detail":{"error_type":"invalid_api_key"}}',
                  "Jev HTTP 401 error_type=invalid_api_key; response body withheld"),
                 (400, b'{"detail":{"error_type":"Private Body Text"}}', "Jev HTTP 400; response body withheld"),
                 (400, b'{"detail":"private"}', "Jev HTTP 400; response body withheld"),
                 (503, b'{"detail":{"error_type":"overloaded"}}', "Jev HTTP 503; response body withheld")]
        for status, body, message in cases:
            with self.subTest(status=status, body=body):
                conn = MagicMock()
                conn.getresponse.return_value.status = status
                conn.getresponse.return_value.read.return_value = body
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(client.startup_request(), sleep=no_sleep)
                self.assertEqual(conn.request.call_count, 1)
                self.assertEqual(raised.exception.code, "SANITY.JEV_UNAVAILABLE")
                self.assertEqual(raised.exception.message, message)
                self.assertIsNotNone(client.CLIENT_MESSAGES.fullmatch(raised.exception.message))

    def test_elapsed_includes_retries_and_is_present_on_failure(self):
        for outcomes, elapsed, status in [([529, 200], 4.5, 0), ([OSError("down")] * 4, 5.0, 2),
                                           ([502] * 4, 11.0, 2), ([529] * 4, 11.0, 2), ([429] * 4, 11.0, 2),
                                           ([503], 1.25, 2), (["invalid"], 1.25, 2)]:
            with self.subTest(outcomes=outcomes):
                clock = FakeClock()
                conn = MagicMock()
                pending = iter(outcomes)

                def send(*args, **kwargs):
                    clock.advance(1.25)
                    outcome = next(pending)
                    if isinstance(outcome, Exception):
                        raise outcome
                    response = MagicMock(status=200 if outcome == "invalid" else outcome)
                    response.read.return_value = b"not-json" if outcome == "invalid" else json.dumps(reply()).encode()
                    response.getheader.return_value = "2"
                    conn.getresponse.return_value = response

                conn.request.side_effect = send
                output = io.StringIO()
                original_clock = client.time.monotonic
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), \
                     contextlib.redirect_stdout(output):
                    self.assertEqual(client.main(["--startup"], clock=clock, sleep=clock.sleep), status)
                result = json.loads(output.getvalue())
                self.assertEqual(result["elapsed_s"], elapsed)
                self.assertEqual(conn.request.call_count, len(outcomes))
                self.assertEqual(clock.waits, [2.0] * (len(outcomes) - 1) if isinstance(outcomes[0], int)
                                 and outcomes[0] in (429, 502, 529) else [])
                self.assertIs(client.time.monotonic, original_clock)
                if status:
                    self.assertIsNone(result["data"])
                    self.assertTrue(client.is_client_message(result["error"]["message"]))

    def test_bad_answer_shapes(self):
        for change in [lambda r: r.update(model="wrong"),
                       lambda r: r.update(answers={}),
                       lambda r: r["answers"]["startup"].update(choice={}),
                       lambda r: r["answers"]["startup"].update(confidence=float("nan")),
                       lambda r: r["answers"]["startup"].update(probabilities={"ready": 0.1, "other": 0.1})]:
            value = reply()
            change(value)
            with self.assertRaises(client.JevError):
                client.validate_response(value, client.startup_request())


    def test_unsplittable_local_request_reports_too_large_without_sending(self):
        request = client.written_request("d" * client.MAX_REQUEST_BYTES, "evidence")
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "request.json"
            file.write_text(json.dumps(request))
            output = io.StringIO()
            with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                 patch.object(client.http.client, "HTTPSConnection") as http, \
                 contextlib.redirect_stdout(output):
                self.assertEqual(client.main(["--request", str(file)], clock=FakeClock(), sleep=no_sleep), 2)
        http.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(result["elapsed_s"], 0.0)
        self.assertEqual(result["error"]["code"], "SANITY.JEV_REQUEST_TOO_LARGE")
        self.assertIn("oversized", result["error"]["message"])
        self.assertRegex(result["error"]["message"], rf"\b\d+ bytes > {client.MAX_REQUEST_BYTES}\b")

    def test_non_text_oversize_state_is_terminal_without_network(self):
        for state in ("x" * client.MAX_REQUEST_BYTES,
                      {"deliverable": "d", "evidence": {"blob": "x" * client.MAX_REQUEST_BYTES}},
                      {"deliverable": "d", "context": ["x" * client.MAX_REQUEST_BYTES]},
                      {"deliverable": "d", "external_evidence": {"blob": "x" * client.MAX_REQUEST_BYTES}}):
            with self.subTest(state_type=type(state).__name__):
                request = {**client.startup_request(), "state": state}
                with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection") as http, \
                     self.assertRaises(client.JevError) as raised:
                    client.evaluate(request, sleep=no_sleep)
                http.assert_not_called()
                self.assertEqual(raised.exception.code, "SANITY.JEV_REQUEST_TOO_LARGE")

    def test_finite_request_values_only(self):
        request = client.startup_request()
        request["state"] = {"bad": float("inf")}
        with self.assertRaises(client.JevError):
            client.validate_request(request)

    def test_request_prints_a_receipt_only_the_call_can_write(self):
        request = {"model": client.MODEL, "state": {"deliverable": "d", "evidence": "e"}, "questions": {"written": {
            "type": "choice", "instructions": "Delivered?", "criteria": {"yes": "delivered", "no": "not delivered"}}}}
        response = {"model": client.MODEL, "id": "resp-1", "answers": {"written": {
            "type": "choice", "choice": "no", "confidence": 0.9, "probabilities": {"yes": 0.1, "no": 0.9}}}}
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read.return_value = json.dumps(response).encode()
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json") as file:
            json.dump(request, file)
            file.flush()
            output = io.StringIO()
            with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), \
                 patch.object(client.http.client, "HTTPSConnection", return_value=conn), contextlib.redirect_stdout(output):
                self.assertEqual(client.main(["--request", file.name], sleep=no_sleep), 0)
        receipt = json.loads(output.getvalue())["data"]["receipt"]
        self.assertEqual({k: receipt[k] for k in ("model", "question", "choice", "probabilities", "response_id")},
                         {"model": client.MODEL, "question": "written", "choice": "no",
                          "probabilities": {"yes": 0.1, "no": 0.9}, "response_id": "resp-1"})
        self.assertEqual(receipt["request_sha256"], client.hashlib.sha256(client.canonical(request)).hexdigest())
        self.assertTrue(client.verify_receipt(receipt, "test-only-key"))
        self.assertFalse(client.verify_receipt(receipt, "another-key"))
        self.assertFalse(client.verify_receipt(dict(receipt, choice="yes"), "test-only-key"))
        self.assertFalse(client.verify_receipt({k: v for k, v in receipt.items() if k != "mac"}, "test-only-key"))

    def test_assignment_request_carries_the_deliverable_verbatim_and_the_committed_diff(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            Path(tmp, "server.py").write_text("bind()\ndrop()\nrebind()\n")
            Path(tmp, "notes.md").write_text("context note\n")
            self.git(tmp, env, "add", "-A"); self.git(tmp, env, "commit", "-qm", "base")
            base = self.git(tmp, env, "rev-parse", "HEAD")
            Path(tmp, "server.py").write_text("bind()\nhand_off_fd()\n")
            self.git(tmp, env, "commit", "-qam", "fix")
            commit = self.git(tmp, env, "rev-parse", "HEAD")
            assignment = {"deliverable": {"number": 1, "text": "Keep the listener open and hand its fd to the child."},
                          "worktree_path": str(tmp), "commit": commit, "base_sha": base,
                          "changed_files": ["server.py"], "context": ["notes.md"]}
            with patch.dict(client.os.environ, env):
                (request,) = client.assignment_requests(assignment)
            self.assertEqual(request["state"]["deliverable"], assignment["deliverable"]["text"])
            self.assertIn("+hand_off_fd()", request["state"]["evidence"])
            self.assertIn("-rebind()", request["state"]["evidence"])
            self.assertEqual(request["state"]["context"], {"notes.md": "context note\n"})
            client.validate_request(request)

            response = {"model": client.MODEL, "answers": {"written": {
                "type": "choice", "choice": "yes", "confidence": 0.9, "probabilities": {"yes": 0.95, "no": 0.05}}}}
            conn = MagicMock()
            conn.getresponse.return_value.status = 200
            conn.getresponse.return_value.read.return_value = json.dumps(response).encode()
            file = Path(tmp, "..", Path(tmp).name + "-assignment.json").resolve()
            file.write_text(json.dumps(assignment))
            try:
                output = io.StringIO()
                with patch.dict(client.os.environ, {**env, "TYPESAFE_API_KEY": "test-only-key"}), \
                     patch.object(client.http.client, "HTTPSConnection", return_value=conn), contextlib.redirect_stdout(output):
                    self.assertEqual(client.main(["--assignment", str(file)], sleep=no_sleep), 0)
                sent = json.loads(conn.request.call_args.kwargs["body"])
                self.assertEqual(sent, request)
                receipt = json.loads(output.getvalue())["data"]["receipt"]
                self.assertEqual(receipt["request_sha256"], client.hashlib.sha256(client.canonical(request)).hexdigest())
                self.assertTrue(client.verify_receipt(receipt, "test-only-key"))

                for broken, message in (({**assignment, "commit": "0" * 40}, "Committed evidence unreadable at the pinned commits"),
                                        ({k: v for k, v in assignment.items() if k != "base_sha"},
                                         "Assignment lacks deliverable text, worktree, commits or file lists")):
                    file.write_text(json.dumps(broken))
                    output = io.StringIO()
                    with patch.dict(client.os.environ, {**env, "TYPESAFE_API_KEY": "test-only-key"}), contextlib.redirect_stdout(output):
                        self.assertEqual(client.main(["--assignment", str(file)], sleep=no_sleep), 2)
                    error = json.loads(output.getvalue())["error"]
                    self.assertEqual((error["code"], error["message"]), ("VALIDATION.INPUT", message))
            finally:
                file.unlink()

    def test_oversize_context_is_refused_and_a_smaller_context_fits(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            Path(tmp, "server.py").write_text("bind()\n")
            big = "".join(f"line {i} " + "x" * 90 + "\n" for i in range(1, 1201))  # ~120 KB, over the cap
            Path(tmp, "big.md").write_text(big)
            self.git(tmp, env, "add", "-A"); self.git(tmp, env, "commit", "-qm", "base")
            base = self.git(tmp, env, "rev-parse", "HEAD")
            Path(tmp, "server.py").write_text("bind()\nhand_off_fd()\n")
            self.git(tmp, env, "commit", "-qam", "fix")
            assignment = {"deliverable": {"number": 1, "text": "Hand the fd to the child."}, "worktree_path": str(tmp),
                          "commit": self.git(tmp, env, "rev-parse", "HEAD"), "base_sha": base,
                          "changed_files": ["server.py"], "context": ["big.md"]}
            file = Path(tmp, "..", Path(tmp).name + "-assignment.json").resolve()
            file.write_text(json.dumps(assignment))
            try:
                with patch.dict(client.os.environ, env), self.assertRaises(client.JevError) as raised:
                    client.assignment_requests(assignment)
                self.assertEqual(raised.exception.code, "SANITY.JEV_REQUEST_TOO_LARGE")
                with patch.dict(client.os.environ, env):
                    (rebuilt,) = client.assignment_requests({**assignment, "context": ["big.md:600-602"]})  # the rebuild fits
                client.validate_request(rebuilt)
                self.assertEqual(rebuilt["state"]["context"], {"big.md:600-602": "".join(big.splitlines(keepends=True)[599:602])})
                with patch.dict(client.os.environ, env):
                    (retry,) = client.assignment_requests({**assignment, "context": []})
                client.validate_request(retry)
            finally:
                file.unlink()

    def test_a_line_range_context_entry_sends_only_those_lines_and_a_bad_range_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            base, commit = self.split_repo(tmp, env, {"a.py": "start\nchanged\n"})
            Path(tmp, "notes.md").write_text("one\ntwo\nthree\nfour\n")
            self.git(tmp, env, "add", "notes.md")
            self.git(tmp, env, "commit", "-qm", "notes")
            commit = self.git(tmp, env, "rev-parse", "HEAD")
            assignment = {"deliverable": {"number": 1, "text": "d"}, "worktree_path": str(tmp), "commit": commit,
                          "base_sha": base, "changed_files": ["a.py"], "context": ["notes.md:2-3", "notes.md"]}
            with patch.dict(client.os.environ, env):
                (request,) = client.assignment_requests(assignment)
            self.assertEqual(request["state"]["context"], {"notes.md:2-3": "two\nthree\n", "notes.md": "one\ntwo\nthree\nfour\n"})
            for entry in ("notes.md:0-2", "notes.md:3-2", "notes.md:4-5"):
                with self.subTest(entry=entry), patch.dict(client.os.environ, env), \
                     self.assertRaises(client.JevError) as raised:
                    client.assignment_requests({**assignment, "context": [entry]})
                self.assertEqual((raised.exception.code, raised.exception.message),
                                 ("VALIDATION.INPUT", f"Context entry {entry} names lines outside its file at the pinned commit"))
                self.assertIn("Fix that `context` entry", client.failure(raised.exception)["error"]["suggested_action"])
            with patch.dict(client.os.environ, env), self.assertRaises(client.JevError) as raised:
                client.assignment_requests({**assignment, "context": ["missing.md:1-2"]})
            self.assertEqual(raised.exception.message, "Committed evidence unreadable at the pinned commits")

    def split_repo(self, tmp, env, files):
        """A repository whose one commit changes `files` (name -> new text) from a one-line base."""
        for name in files:
            Path(tmp, name).write_text("start\n" + "\n".join(f"keep {i}" for i in range(0, 4000, 40)) + "\n")
        self.git(tmp, env, "add", "-A"); self.git(tmp, env, "commit", "-qm", "base")
        base = self.git(tmp, env, "rev-parse", "HEAD")
        for name, text in files.items():
            Path(tmp, name).write_text(text)
        self.git(tmp, env, "commit", "-qam", "change")
        return base, self.git(tmp, env, "rev-parse", "HEAD")


    def test_diff_over_cap_is_refused_without_jev_call(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            base, commit = self.split_repo(tmp, env, {"big.py": "start\n" + "x" * (client.MAX_REQUEST_BYTES + 1)})
            assignment = {"deliverable": {"number": 1, "text": "Add content."}, "worktree_path": str(tmp),
                          "commit": commit, "base_sha": base, "changed_files": ["big.py"], "context": []}
            with patch.dict(client.os.environ, env), patch.object(client.http.client, "HTTPSConnection") as http, \
                 self.assertRaises(client.JevError) as raised:
                client.assignment_requests(assignment)
            http.assert_not_called()
            self.assertEqual(raised.exception.code, "SANITY.JEV_REQUEST_TOO_LARGE")
            self.assertIn("subtask beads", raised.exception.message)
            self.assertIn("reference beads", raised.exception.message)

    def test_deliverable_text_alone_over_the_cap_names_the_plan_fix(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            base, commit = self.split_repo(tmp, env, {"a.py": "start\nchanged\n"})
            with patch.dict(client.os.environ, env), self.assertRaises(client.JevError) as raised:
                client.assignment_requests({"deliverable": {"number": 1, "text": "d" * client.MAX_REQUEST_BYTES},
                                            "worktree_path": str(tmp), "commit": commit, "base_sha": base,
                                            "changed_files": ["a.py"], "context": []})
            action = client.failure(raised.exception)["error"]["suggested_action"]
            self.assertIn("subtask beads", action)
            self.assertIn("reference beads", action)
            self.assertNotIn("unchanged", action)

    REFS = [{"kind": "bead_notes", "bead": "lint-k7", "text": "Ran `just test`: 412 passed at abc123."},
            {"kind": "pr_body", "repo": "o/r", "pr": 460},
            {"kind": "pr_comment", "repo": "o/r", "comment_id": 77}]

    def fetched(self, failing=(), answering=None):
        """`subprocess.run` answering bd/gh for REFS (git passes through); a command naming a `failing` id exits 1;
        `answering` maps an id to the response replacing its default."""
        real = client.subprocess.run
        answers = {"lint-k7": [{"id": "lint-k7", "notes": "Ran `just test`: 412 passed at abc123.", "updated_at": "2026-10-13T01:00:00Z"}],
                   "repos/o/r/pulls/460": {"body": "Evidence: smoke log attached.", "html_url": "https://github.com/o/r/pull/460",
                                           "updated_at": "2026-10-13T02:00:00Z", "user": {"login": "dev"}},
                   "repos/o/r/issues/comments/77": {"body": "Re-ran on Windows: green.", "html_url": "https://github.com/o/r/pull/460#c77",
                                                    "updated_at": "2026-10-13T03:00:00Z", "user": {"login": "qa"}}}
        answers.update(answering or {})

        def run(argv, **kwargs):
            if argv[0] == "git":
                return real(argv, **kwargs)
            key = argv[2]
            if key in failing:
                return MagicMock(returncode=1, stdout="", stderr="not found")
            return MagicMock(returncode=0, stdout=json.dumps(answers[key]), stderr="")
        return patch.object(client.subprocess, "run", side_effect=run)

    def test_evidence_only_deliverable_sends_bead_notes_and_pr_text_with_their_source(self):
        assignment = {"deliverable": {"number": 1, "text": "Record the Windows re-run result."}, "worktree_path": "/nonexistent",
                      "commit": "c" * 40, "base_sha": "b" * 40, "changed_files": [], "context": [], "external_evidence": self.REFS}
        with self.fetched() as run:
            (request,) = client.assignment_requests(assignment)
        self.assertEqual([c.args[0][:2] for c in run.call_args_list], [["gh", "api"], ["gh", "api"]])
        self.assertTrue(all(c.kwargs["cwd"] == "/nonexistent" for c in run.call_args_list))
        client.validate_request(request)
        self.assertEqual(request["state"]["evidence"], "")
        self.assertEqual(request["state"]["external_evidence"], [
            {"kind": "bead_notes", "ref": "lint-k7", "url": None, "updated_at": None, "author": None,
             "text": "Ran `just test`: 412 passed at abc123."},
            {"kind": "pr_body", "ref": "o/r#460", "url": "https://github.com/o/r/pull/460", "updated_at": "2026-10-13T02:00:00Z",
             "author": "dev", "text": "Evidence: smoke log attached."},
            {"kind": "pr_comment", "ref": "o/r#77", "url": "https://github.com/o/r/pull/460#c77", "updated_at": "2026-10-13T03:00:00Z",
             "author": "qa", "text": "Re-ran on Windows: green."}])
        with self.fetched():
            (without,) = client.assignment_requests({k: v for k, v in assignment.items() if k != "external_evidence"})
        self.assertNotIn("external_evidence", without["state"])

    def test_external_evidence_that_cannot_be_read_or_is_malformed_fails_before_any_jev_call(self):
        assignment = {"deliverable": {"number": 1, "text": "d"}, "worktree_path": "/nonexistent", "commit": "c" * 40,
                      "base_sha": "b" * 40, "changed_files": [], "context": [], "external_evidence": self.REFS}
        with self.fetched(failing=("repos/o/r/pulls/460",)), patch.object(client.http.client, "HTTPSConnection") as https:
            with self.assertRaises(client.JevError) as raised:
                client.assignment_requests(assignment)
            https.assert_not_called()
        error = client.failure(raised.exception)["error"]
        self.assertEqual((error["code"], error["message"]), ("VALIDATION.INPUT", "External evidence unreadable: pr_body o/r#460"))
        self.assertTrue(client.is_client_message(error["message"]))
        self.assertIn("gh auth status", error["suggested_action"])
        for bad in ([{"kind": "pr_body", "repo": "o/r"}], [{"kind": "pr_body", "repo": "{owner}/{repo}", "pr": 460}], [{"kind": "pr_body", "repo": "o/r", "pr": "460"}],
                    [{"kind": "issue", "repo": "o/r", "pr": 1}], [{"kind": "bead_notes", "bead": "--all"}],
                    [{"kind": "bead_notes", "bead": "x", "text": 3}], {"kind": "bead_notes", "bead": "x"}):
            with self.subTest(bad=bad), self.fetched() as run, self.assertRaises(client.JevError) as raised:
                client.assignment_requests({**assignment, "external_evidence": bad})
            run.assert_not_called()
            self.assertEqual(raised.exception.message,
                             "Assignment external_evidence entry is not a bead_notes, pr_body or pr_comment reference")
            self.assertIn("pr_comment", client.failure(raised.exception)["error"]["suggested_action"])

    def test_null_pr_body_is_empty_evidence_but_any_other_non_string_body_still_fails(self):
        ref, key = {"kind": "pr_body", "repo": "o/r", "pr": 460}, "repos/o/r/pulls/460"
        with self.fetched(answering={key: {"body": None}}):
            (evidence,) = [client.external_evidence(ref, "/nonexistent")]
        self.assertEqual((evidence["kind"], evidence["ref"], evidence["text"]), ("pr_body", "o/r#460", ""))
        for bad in ({"body": 5}, {"html_url": "https://github.com/o/r/pull/460"}, ["body"]):
            with self.subTest(bad=bad), self.fetched(answering={key: bad}), self.assertRaises(client.JevError) as raised:
                client.external_evidence(ref, "/nonexistent")
            self.assertEqual(raised.exception.message, "External evidence unreadable: pr_body o/r#460")

    def test_layered_source_reads_lower_layer_context_at_the_pinned_top(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp, env = self.fixture_repo(directory)
            Path(tmp, "lib.py").write_text("def old(): pass\n")
            Path(tmp, "server.py").write_text("old()\n")
            self.git(tmp, env, "add", "-A"); self.git(tmp, env, "commit", "-qm", "trunk")
            trunk = self.git(tmp, env, "rev-parse", "HEAD")
            Path(tmp, "lib.py").write_text("def hand_off(fd): pass\n")  # lower layer
            self.git(tmp, env, "commit", "-qam", "layer 1")
            lower = self.git(tmp, env, "rev-parse", "HEAD")
            Path(tmp, "server.py").write_text("hand_off(3)\n")  # top layer, the one checked
            self.git(tmp, env, "commit", "-qam", "layer 2")
            top = self.git(tmp, env, "rev-parse", "HEAD")
            assignment = {"deliverable": {"number": 1, "text": "Call hand_off with the listener fd."}, "worktree_path": str(tmp),
                          "commit": top, "base_sha": lower, "changed_files": ["server.py"], "context": ["lib.py"]}
            with patch.dict(client.os.environ, env):
                (request,) = client.assignment_requests(assignment)
            self.assertEqual(request["state"]["context"], {"lib.py": "def hand_off(fd): pass\n"})
            self.assertIn("+hand_off(3)", request["state"]["evidence"])
            self.assertNotIn("lib.py", request["state"]["evidence"])
            with patch.dict(client.os.environ, env):
                (layered,) = client.assignment_requests({**assignment, "base_sha": trunk, "changed_files": ["lib.py", "server.py"]})
            self.assertIn("+def hand_off(fd): pass", layered["state"]["evidence"])
            self.assertIn("+hand_off(3)", layered["state"]["evidence"])

    def test_external_evidence_over_cap_is_refused(self):
        assignment = {"deliverable": {"number": 1, "text": "d"}, "worktree_path": "/nonexistent", "commit": "c" * 40,
                      "base_sha": "b" * 40, "changed_files": [], "context": [],
                      "external_evidence": [{"kind": "bead_notes", "bead": "lint-k7", "text": "n" * client.MAX_REQUEST_BYTES}]}
        with self.assertRaises(client.JevError) as raised:
            client.assignment_requests(assignment)
        self.assertEqual(raised.exception.code, "SANITY.JEV_REQUEST_TOO_LARGE")

    def test_each_known_error_returns_its_fix(self):
        cases = {
            ("SANITY.JEV_UNAVAILABLE", "Jev connection failed or timed out", True): "retry budget is exhausted",
            ("SANITY.JEV_UNAVAILABLE", "Jev HTTP 503; response body withheld", True): "retry budget is exhausted",
            ("SANITY.JEV_UNAVAILABLE", "Jev HTTP 401; response body withheld", False): "Report this error unchanged",
            ("VALIDATION.INPUT", "Committed evidence unreadable at the pinned commits", False): "git -C <worktree_path> fetch origin",
            ("VALIDATION.INPUT", "Request file unavailable or invalid JSON", False): "Write the file as the JSON object",
            ("SANITY.JEV_RESPONSE_INVALID", "Invalid Choice answer", False): "Report this error unchanged",
        }
        for (code, message, recoverable), fix in cases.items():
            with self.subTest(message=message):
                self.assertIn(fix, client.failure(client.JevError(code, message, recoverable))["error"]["suggested_action"])

    def test_every_failure_message_the_client_writes_is_recognised(self):
        source = (Path(__file__).parents[1] / "jev_client.py").read_text()
        import re
        literals = re.findall(r'JevError\("[A-Z_.]+", f?"([^"]+)"', source)
        self.assertGreaterEqual(len(literals), 15)
        # Placeholders computed before the literal take each value the client can give them.
        variants = {"{bound}": [f"> {client.MAX_REQUEST_BYTES}", "over Jev's token limit"],
                    "{named}": ["", " error_type=max_tokens_exceeded"]}
        for literal in literals:
            filled = [literal.replace("{status}", "503").replace("{request_size}", "123456").replace(
                "{MAX_REQUEST_BYTES}", str(client.MAX_REQUEST_BYTES))]
            for placeholder, values in variants.items():
                filled = [text.replace(placeholder, value) for text in filled for value in values] \
                    if placeholder in literal else filled
            for message in filled:
                with self.subTest(message=message):
                    self.assertTrue(client.is_client_message(message))
        self.assertFalse(client.is_client_message("Selected model is at capacity"))


if __name__ == "__main__":
    unittest.main()
