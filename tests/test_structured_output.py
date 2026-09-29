import unittest

from orchestrator.structured_output import ModelRateLimitError, extract_json_object, raise_if_rate_limited


class StructuredOutputFallbackTests(unittest.TestCase):
    def test_extracts_plain_json(self):
        self.assertEqual({"status": "ok"}, extract_json_object('{"status":"ok"}'))

    def test_extracts_fenced_json(self):
        content = 'Result:\n```json\n{"status":"ok"}\n```'
        self.assertEqual({"status": "ok"}, extract_json_object(content))

    def test_rejects_empty_provider_response(self):
        with self.assertRaisesRegex(ValueError, "no JSON object"):
            extract_json_object("")

    def test_rate_limit_error_is_short_and_actionable(self):
        provider_error = RuntimeError(
            "Error code: 429 - X-RateLimit-Reset: 1790726400000 free-models-per-day"
        )
        with self.assertRaises(ModelRateLimitError) as raised:
            raise_if_rate_limited(provider_error)
        message = str(raised.exception)
        self.assertIn("quota is exhausted", message)
        self.assertIn("2026-09-30 00:00 UTC", message)
        self.assertNotIn("X-RateLimit", message)


if __name__ == "__main__":
    unittest.main()
