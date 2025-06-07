from django.test import TestCase, Client
from unittest.mock import patch
import os


class ProcessVideoTests(TestCase):
    @patch("summary.views.pipeline_proxy.summarize_with_gemini")
    @patch("summary.views.pipeline_proxy.download_and_transcribe")
    def test_process_video_passes_lang(self, mock_transcribe, mock_summarize):
        mock_transcribe.return_value = "text"
        mock_summarize.return_value = "script"
        with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}):
            response = Client().get("/process/abc123/?lang=en")
        self.assertEqual(response.status_code, 200)
        mock_summarize.assert_called_with("key", "text", lang="en")

