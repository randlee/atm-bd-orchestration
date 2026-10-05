"""Transport/contract failures must not become a successful sanity check."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("jev_client", Path(__file__).parents[1] / "jev_client.py")
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


def reply():
    return {"model": client.MODEL, "answers": {"startup": {
        "type": "choice", "choice": "ready", "confidence": 0.99,
        "probabilities": {"ready": 1.0, "other": 0.0},
    }}, "usage": {"input_tokens": 1, "output_tokens": 1}}


class JevClientTests(unittest.TestCase):
    def test_missing_key_no_network(self):
        with patch.dict(client.os.environ, {}, clear=True), patch.object(client.http.client, "HTTPSConnection") as http:
            with self.assertRaises(client.JevError):
                client.evaluate(client.startup_request())
            http.assert_not_called()

    def startup(self, argv, team, daemon, environ=None):
        """Run the startup probe without a key; `atm escalation list` answers with `team` / `daemon` recipients."""
        def run(cmd, **kwargs):
            listed = {"--team": team} if "--team" in cmd else {"": daemon}
            recipients = next(iter(listed.values()))
            return MagicMock(returncode=0 if recipients is not None else 1, stdout=json.dumps({"recipients": recipients or []}))
        with patch.dict(client.os.environ, environ if environ is not None else {"ATM_TEAM": "t"}, clear=True), \
             patch.object(client.subprocess, "run", side_effect=run) as send:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = client.main(argv)
        sends = [(c.args[0][2], c.kwargs["input"]) for c in send.call_args_list if c.args[0][:2] == ["atm", "send"]]
        return rc, json.loads(output.getvalue()), sends

    def test_startup_announces_to_escalation_recipients_else_lead(self):
        rc, result, sends = self.startup(["--startup", "--announce", "--lead", "appointed-lead"], ["oversight@team"], ["daemon@host"])
        self.assertEqual(rc, 2)
        self.assertTrue(result["error"]["recoverable"])
        self.assertEqual(set(result["error"]), {"code", "message", "recoverable", "suggested_action"})
        self.assertEqual([to for to, _ in sends], ["oversight@team"])
        self.assertIn(result["error"]["message"], sends[0][1])
        _, _, sends = self.startup(["--startup", "--announce", "--lead", "appointed-lead"], [], ["daemon@host"])
        self.assertEqual([to for to, _ in sends], ["daemon@host"])
        _, _, sends = self.startup(["--startup", "--announce", "--lead", "appointed-lead"], [], None)
        self.assertEqual([to for to, _ in sends], ["appointed-lead"])
        self.assertTrue(sends[0][1].endswith("No escalation recipient is set."))
        _, _, sends = self.startup(["--startup", "--announce", "--lead", "appointed-lead"], None, ["daemon@host"], environ={})
        self.assertEqual([to for to, _ in sends], ["daemon@host"])

    def test_startup_without_announce_sends_nothing(self):
        rc, _, sends = self.startup(["--startup"], ["oversight@team"], ["daemon@host"])
        self.assertEqual((rc, sends), (2, []))
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            client.main(["--startup", "--announce"])

    def test_successful_transport(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read.return_value = json.dumps(reply()).encode()
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), patch.object(client.http.client, "HTTPSConnection", return_value=conn):
            self.assertEqual(client.evaluate(client.startup_request()), reply())
        self.assertEqual(conn.request.call_args.args[:2], ("POST", "/v1/systemone"))
        conn.close.assert_called_once()

    def test_auth_error_does_not_echo_body_or_key(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 401
        conn.getresponse.return_value.read.return_value = b"test-only-key server details"
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), patch.object(client.http.client, "HTTPSConnection", return_value=conn):
            with self.assertRaises(client.JevError) as raised:
                client.evaluate(client.startup_request())
        self.assertNotIn("test-only-key", str(raised.exception))
        self.assertFalse(raised.exception.recoverable)
        self.assertEqual(conn.request.call_count, 1)

    def test_retry_is_bounded(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 429
        conn.getresponse.return_value.read.return_value = b"{}"
        conn.getresponse.return_value.getheader.return_value = "0"
        with patch.dict(client.os.environ, {"TYPESAFE_API_KEY": "test-only-key"}), patch.object(client.http.client, "HTTPSConnection", return_value=conn), patch.object(client.time, "sleep"):
            with self.assertRaises(client.JevError):
                client.evaluate(client.startup_request())
        self.assertEqual(conn.request.call_count, 2)

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

    def test_oversize_request_abstains(self):
        request = client.startup_request()
        request["state"] = "x" * client.MAX_REQUEST_BYTES
        with self.assertRaises(client.JevError) as raised:
            client.validate_request(request)
        self.assertEqual(raised.exception.code, "SANITY.JEV_INCONCLUSIVE")

    def test_finite_request_values_only(self):
        request = client.startup_request()
        request["state"] = {"bad": float("inf")}
        with self.assertRaises(client.JevError):
            client.validate_request(request)


if __name__ == "__main__":
    unittest.main()
