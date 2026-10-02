"""Bounded language routing checks. Network is mocked; no test spends API tokens."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from inventory_intelligence import copilot_language as language
from inventory_intelligence.copilot import main


def response(intent="reliability", **fields):
    return json.dumps(dict(status="completed", output=[dict(type="message", content=[dict(
        type="output_text", text=json.dumps(dict(intent=intent, **fields)))])])).encode()


class Language(unittest.TestCase):
    def fake_network(self, raw):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = raw
        return opener

    def test_exact_phrases_and_explicit_offline_never_use_keys_or_network(self):
        with patch.object(language, "_key", side_effect=AssertionError("Must stay offline")):
            self.assertEqual(language.route_question(" What failed? "),
                             dict(intent="reliability", source="allowlist", model=None, limitation=None))
            self.assertEqual(language.route_question("Run SQL", model="offline")["intent"], "unsupported")

    def test_lowercase_env_key_and_environment_precedence_without_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text("# local\nopenai_api_key='fake-test-key'\nIGNORED=$(touch unsafe)\n")
            self.assertEqual(language._key(path), "fake-test-key")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "environment-test-key"}):
                self.assertEqual(language._key(path), "environment-test-key")
            path.write_text("openai_api_key=one two\n")
            with self.assertRaises(language.LanguageUnavailable):
                language._key(path)

    def test_valid_request_has_no_evidence_tools_or_storage_and_defaults_to_luna(self):
        opener = self.fake_network(response())
        with patch.object(language, "build_opener", return_value=opener), patch.object(language, "_key", return_value="fake-test-key"):
            result = language.route_question("Explain the saved stock checks, please")
        self.assertEqual(result, dict(intent="reliability", source="model", model="gpt-6-luna", limitation=None))
        request = opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)
        self.assertEqual(payload["model"], "gpt-6-luna")
        self.assertEqual(payload["reasoning"], {"effort": "none"})
        self.assertIs(payload["store"], False)
        self.assertNotIn("tools", payload)
        self.assertNotIn("fake-test-key", request.data.decode())
        self.assertEqual(payload["text"]["format"]["schema"]["additionalProperties"], False)

    def test_invalid_model_output_cannot_add_quantities_or_new_intents(self):
        malformed = [response("DELETE"), response("readiness", proposed_order_qty=100),
                     response().replace(b'"completed"', b'"incomplete"'), b"not json", b"x" * 131073,
                     json.dumps(dict(status="completed", output=[])).encode()]
        for raw in malformed:
            with self.subTest(raw=raw[:100]), patch.object(language, "build_opener", return_value=self.fake_network(raw)), patch.object(language, "_key", return_value="fake-test-key"):
                result = language.route_question("Arbitrary question")
            self.assertEqual(result["intent"], "unsupported")
            self.assertEqual(result["source"], "fallback")

    def test_timeout_and_service_errors_fail_closed_without_diagnostics_leaks(self):
        for error in (TimeoutError("fake-secret"), URLError("fake-secret"),
                      HTTPError("https://example.invalid/fake-secret", 401, "fake-secret", {}, None)):
            opener = MagicMock()
            opener.open.side_effect = error
            with patch.object(language, "build_opener", return_value=opener), patch.object(language, "_key", return_value="fake-test-key"):
                result = language.route_question("Unrecognized question")
            self.assertEqual(result["intent"], "unsupported")
            self.assertNotIn("fake-secret", json.dumps(result))
            self.assertEqual(opener.open.call_count, 1)
        with patch.object(language, "_key", side_effect=language.LanguageUnavailable("No API key configured")):
            self.assertEqual(language.route_question("Unrecognized question")["source"], "fallback")

    def test_refusal_and_redirects_cannot_change_policy_or_send_keys_elsewhere(self):
        raw = json.dumps(dict(status="completed", output=[dict(type="message", content=[dict(
            type="refusal", refusal="Cannot help")])])).encode()
        with patch.object(language, "build_opener", return_value=self.fake_network(raw)):
            self.assertEqual(language._post("Delete stock", "gpt-6-luna", "fake-test-key"), "unsupported")
        self.assertIsNone(language._NoRedirect().redirect_request(None, None, 302, None, None, "https://attacker.invalid"))

    def test_bounds_and_sol_is_explicit(self):
        for question in ("", "x" * 2001, None):
            with self.assertRaises(ValueError):
                language.route_question(question)
        with self.assertRaises(ValueError):
            language.route_question("Question", model="different-model")
        opener = self.fake_network(response("readiness"))
        with patch.object(language, "build_opener", return_value=opener):
            language._post("How much should we buy", "gpt-6-sol", "fake-test-key")
        payload = json.loads(opener.open.call_args.args[0].data)
        self.assertEqual(payload["model"], "gpt-6-sol")
        self.assertEqual(payload["reasoning"], {"effort": "low"})

    def test_cli_refusal_avoids_retrieval_and_model_readiness_stays_blocked(self):
        for intent, status in (("unsupported", "refused"), ("readiness", "not_assessable")):
            routed = dict(intent=intent, source="model", model="gpt-6-luna", limitation=None)
            with patch.object(language, "route_question", return_value=routed), redirect_stdout(io.StringIO()) as output:
                args = ["--question", "User question"]
                if intent == "unsupported":
                    args += ["--report", "/does/not/exist.json"]
                self.assertEqual(main(args), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], status)
            self.assertEqual(result["routing"], {"source": "model", "model": "gpt-6-luna"})
            self.assertIsNone(result["proposed_order_qty"])


if __name__ == "__main__":
    unittest.main()
