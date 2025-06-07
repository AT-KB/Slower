from django.test import TestCase, Client


class BasicViewTests(TestCase):
    def test_index(self):
        response = Client().get("/")
        self.assertEqual(response.status_code, 200)
