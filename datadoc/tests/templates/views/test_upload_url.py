from django.test import TestCase
from django.urls import reverse


class UploadFileURLPageTests(TestCase):
    def test_upload_file_url_page_renders_correctly(self):
        response = self.client.get(reverse("upload_url"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('class="info-banner"', content)
        self.assertIn("Please provide a valid download URL", content)
        self.assertIn('id="url-form"', content)
        self.assertIn('method="post"', content)
        self.assertIn('hx-post="', content)
        self.assertIn('hx-target="#processing"', content)
        self.assertIn('type="url"', content)
        self.assertIn('id="url"', content)
        self.assertIn('id="submit-button"', content)
        self.assertIn("disabled", content)
        self.assertIn('id="processing"', content)
        self.assertIn("Processing request for documentation", content)
        self.assertIn('id="modal"', content)
        self.assertIn('id="modalContent"', content)
        self.assertIn("csrfmiddlewaretoken", content)
