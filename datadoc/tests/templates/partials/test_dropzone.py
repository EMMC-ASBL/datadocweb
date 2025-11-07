from django.test import TestCase
from django.urls import reverse


class UploadPageTemplateTests(TestCase):
    def test_upload_page_renders_correctly(self):
        response = self.client.get(reverse("datadoc:upload_file"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="files-dropzone"', content)
        self.assertIn('alert', content)
