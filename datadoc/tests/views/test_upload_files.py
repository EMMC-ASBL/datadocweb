import os
from django.conf import settings
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


class FileUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("datadoc:upload_files") 
        self.test_files_dir = os.path.join(
            settings.BASE_DIR, "core/static/core/templates"
        )

    def test_upload_csv_file(self):
        file_path = os.path.join(self.test_files_dir, "template.csv")
        with open(file_path, "rb") as f:
            uploaded_file = SimpleUploadedFile(
                "template.csv", f.read(), content_type="text/csv"
            )
        response = self.client.post(self.upload_url, {"files": uploaded_file})
        print("CSV Upload Response:", response.json())

    def test_upload_json_file(self):
        file_path = os.path.join(self.test_files_dir, "template.json")
        with open(file_path, "rb") as f:
            uploaded_file = SimpleUploadedFile(
                "template.json", f.read(), content_type="application/json"
            )
        response = self.client.post(self.upload_url, {"files": uploaded_file})
        print("JSON Upload Response:", response.json())

    def test_upload_yaml_file(self):
        file_path = os.path.join(self.test_files_dir, "template.yaml")
        with open(file_path, "rb") as f:
            uploaded_file = SimpleUploadedFile(
                "template.yaml", f.read(), content_type="application/x-yaml"
            )
        response = self.client.post(self.upload_url, {"files": uploaded_file})
        print("YAML Upload Response:", response.json())
