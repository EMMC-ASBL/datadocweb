from django.test import TestCase
from django.urls import reverse


class UploadPageTemplateTests(TestCase):
    def test_upload_page_renders_correctly(self):
        response = self.client.get(reverse("upload_file"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('<meta name="csrf-token"', content)
        self.assertIn('id="drop-zone"', content)
        self.assertIn('id="modal"', content)
        self.assertIn('hx-post="', content)
        self.assertIn('hx-target="#upload-result"', content)
