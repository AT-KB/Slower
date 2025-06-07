from django.test import TestCase, Client
from unittest.mock import patch
import os


class BasicViewTests(TestCase):
    def test_index(self):
        response = Client().get("/")
        self.assertEqual(response.status_code, 200)

    @patch("summary.views.pipeline_proxy.search_videos")
    def test_search_with_params(self, mock_search):
        mock_search.return_value = []
        params = {
            "search": "",
            "keyword": "test",
            "lang": "en",
            "after": "2024-01-01",
            "before": "2024-06-30",
            "min_views": "100",
            "max_views": "1000",
            "min_subs": "50",
            "max_subs": "500",
            "min_length": "1",
            "max_length": "2",
            "length": "short",
            "max_results": "10",
        }
        with patch.dict(os.environ, {"YT_KEY": "dummy"}):
            response = Client().get("/", params)
        self.assertEqual(response.status_code, 200)
        mock_search.assert_called_with(
            "dummy",
            "test",
            "en",
            max_results=10,
            video_duration="short",
            published_after="2024-01-01T00:00:00Z",
            published_before="2024-06-30T00:00:00Z",
            min_view_count=100,
            max_view_count=1000,
            min_subscribers=50,
            max_subscribers=500,
            min_duration=60,
            max_duration=120,
        )
