import json
import tempfile
import unittest
from pathlib import Path

from local_data_plane.daemon import InferenceDaemon
from local_data_plane.openai_adapter import OpenAIAdapter


class OpenAIAdapterTests(unittest.TestCase):
    def setUp(self):
        self.daemon = InferenceDaemon()
        self.handle = self.daemon.handle({"method": "load", "model_id": "tiny"})[0][1]["handle_id"]
        self.adapter = OpenAIAdapter(self.daemon)

    def test_chat_uses_existing_handle_and_streams(self):
        status_before = len(self.daemon.handles)
        code, headers, body = self.adapter.dispatch(
            "POST", "/v1/chat/completions", {"Content-Type": "application/json"},
            json.dumps({"messages": [{"role": "user", "content": "hello"}], "max_tokens": 2,
                        "stream": True}).encode())
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Type"], "text/event-stream")
        self.assertIn(b"[DONE]", body)
        self.assertEqual(len(self.daemon.handles), status_before)

    def _chat(self, **payload):
        payload.setdefault("messages", [{"role": "user", "content": "hello"}])
        code, _, body = self.adapter.dispatch("POST", "/v1/chat/completions", {},
                                             json.dumps(payload).encode())
        return code, json.loads(body)

    def test_max_completion_tokens_is_honored_and_preferred(self):
        code, body = self._chat(max_completion_tokens=5)
        self.assertEqual(code, 200)
        self.assertEqual(body["usage"]["completion_tokens"], 5)
        code, body = self._chat(max_completion_tokens=3, max_tokens=6)
        self.assertEqual(code, 200)
        self.assertEqual(body["usage"]["completion_tokens"], 3)
        code, body = self._chat(max_tokens=4)
        self.assertEqual(code, 200)
        self.assertEqual(body["usage"]["completion_tokens"], 4)

    def test_null_max_tokens_uses_the_default(self):
        code, body = self._chat(max_tokens=None, max_completion_tokens=None)
        self.assertEqual(code, 200)
        self.assertEqual(body["usage"]["completion_tokens"], 8)

    def test_malformed_max_tokens_is_a_client_error(self):
        for field in ("max_tokens", "max_completion_tokens"):
            for value in ("sixty", "12", 2.5, True, [3]):
                with self.subTest(field=field, value=value):
                    code, body = self._chat(**{field: value})
                    self.assertEqual(code, 400)
                    self.assertIn(field, body["error"]["message"])
        code, _, body = self.adapter.dispatch("POST", "/v1/completions", {},
                                              json.dumps({"prompt": "x", "max_tokens": "sixty"}).encode())
        self.assertEqual(code, 400)
        self.assertIn(b"max_tokens", body)

    def test_text_content_parts_are_flattened(self):
        parts = [{"type": "text", "text": "hel"}, {"type": "text", "text": "lo"}]
        code, body = self._chat(messages=[{"role": "user", "content": parts}], max_tokens=1)
        self.assertEqual(code, 200)
        self.assertEqual(body["choices"][0]["text"], " hello")

    def test_non_text_content_parts_are_rejected(self):
        for content in ([{"type": "image_url", "image_url": {"url": "x"}}],
                        [{"type": "text"}], [{"type": "text", "text": 1}], ["hello"], 7):
            with self.subTest(content=content):
                code, body = self._chat(messages=[{"role": "user", "content": content}])
                self.assertEqual(code, 400)
                self.assertIn("content", body["error"]["message"])

    def test_tools_are_candidates_forbidden_from_execution(self):
        code, _, body = self.adapter.dispatch("POST", "/v1/completions", {},
                                             json.dumps({"prompt": "x", "tools": []}).encode())
        self.assertEqual(code, 400)
        self.assertIn(b"forbidden", body)

    def test_non_loopback_requires_token_and_cors_is_not_added(self):
        with self.assertRaises(ValueError):
            OpenAIAdapter(self.daemon, host="0.0.0.0")
        protected = OpenAIAdapter(self.daemon, host="0.0.0.0", auth_token="secret")
        self.assertEqual(protected.dispatch("GET", "/v1/models")[0], 401)
        self.assertEqual(protected.dispatch("GET", "/v1/models", {"Authorization": "Bearer secret"})[0], 200)
        self.assertNotIn("Access-Control-Allow-Origin", protected.dispatch("GET", "/v1/models", {"Authorization": "Bearer secret"})[1])

    def test_local_benchmark_page_is_served_same_origin(self):
        with tempfile.TemporaryDirectory() as root:
            page = Path(root) / "qwen38.html"
            page.write_text("<title>Qwen benchmark</title>", encoding="utf-8")
            adapter = OpenAIAdapter(self.daemon, static_root=root)
            code, headers, body = adapter.dispatch("GET", "/")
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn(b"Qwen benchmark", body)


if __name__ == "__main__":
    unittest.main()
