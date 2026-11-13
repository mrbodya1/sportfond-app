import base64
import datetime as dt
import json
import unittest
from unittest.mock import patch, MagicMock
from recognition import validate_result, decode_image, recognize, RecognitionError

VALID = {"workout_date": "2026-10-29", "distance_km": 5.25, "gps_route": "present", "activity": "running", "readable": True, "notes": "GPS виден."}


class RecognitionTests(unittest.TestCase):
    def validate(self, **updates):
        return validate_result({**VALID, **updates}, dt.date(2026, 11, 13))

    def test_rules_without_pace_or_pulse(self):
        self.assertEqual(self.validate()["decision"], "eligible_preview")
        self.assertEqual(self.validate(workout_date="2026-10-28")["decision"], "rejected")
        self.assertEqual(self.validate(gps_route="absent")["decision"], "rejected")
        self.assertEqual(self.validate(gps_route="unclear")["decision"], "manual_review")
        self.assertEqual(self.validate(activity="other")["decision"], "rejected")

    def test_uncertain_date_and_distance_never_invented(self):
        self.assertEqual(self.validate(workout_date=None)["decision"], "manual_review")
        self.assertEqual(self.validate(distance_km=None)["decision"], "manual_review")
        with self.assertRaises(RecognitionError):
            self.validate(workout_date="2026-02-30")
        with self.assertRaises(RecognitionError):
            self.validate(distance_km=True)
        with self.assertRaises(RecognitionError):
            self.validate(distance_km=float("nan"))

    def test_no_remote_urls_or_spoofed_mime(self):
        for value in ["https://example.com/image.png", "data:image/png;base64," + base64.b64encode(b"not a png").decode()]:
            with self.assertRaises(RecognitionError):
                decode_image(value)

    @patch("recognition.ssl.create_default_context")
    @patch("recognition.urllib.request.urlopen")
    def test_request_is_server_only_with_no_storage_or_tools(self, fetch, context):
        response = MagicMock()
        response.read.return_value = json.dumps({"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(VALID)}]}]}).encode()
        fetch.return_value.__enter__.return_value = response
        image = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode()
        result = recognize(image, {"OPENAI_API_KEY": "test-not-a-real-key"})
        payload = json.loads(fetch.call_args.args[0].data)
        self.assertIs(payload["store"], False)
        self.assertNotIn("tools", payload)
        self.assertEqual(set(payload["text"]["format"]["schema"]["properties"]), set(VALID))
        self.assertEqual(result["distance_km"], 5.25)
        self.assertNotIn("OPENAI_API_KEY", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
