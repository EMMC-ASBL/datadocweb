import os
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse


class FileURLUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("datadoc:upload_file_url")

    @patch("datadoc.views.get_triplestore")
    @patch("datadoc.views.handle_file_url")
    def test_upload_json_url(self, mock_handle_file_url, mock_get_triplestore):
        dummy_url = "https://raw.githubusercontent.com/EMMC-ASBL/datadocweb/refs/heads/main/core/static/core/templates/template.json"

        # Mock Triplestore and response
        mock_get_triplestore.return_value = "mock_ts"
        mock_handle_file_url.return_value = JsonResponse(
            {
                "status": "Success",
                "message": "Mocked JSON file processed",
                "status_code": 200,
            },
            status=200,
        )

        response = self.client.post(self.upload_url, {"url": dummy_url})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("JSON URL Upload Response:", data)
        self.assertEqual(data["status"], "Success")

    @patch("datadoc.views.get_triplestore")
    @patch("datadoc.views.handle_file_url")
    def test_upload_csv_url(self, mock_handle_file_url, mock_get_triplestore):
        dummy_url = "https://raw.githubusercontent.com/EMMC-ASBL/datadocweb/refs/heads/main/core/static/core/templates/template.csv"

        mock_get_triplestore.return_value = "mock_ts"
        mock_handle_file_url.return_value = JsonResponse(
            {
                "status": "Success",
                "message": "Mocked CSV file processed",
                "status_code": 200,
            },
            status=200,
        )

        response = self.client.post(self.upload_url, {"url": dummy_url})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("CSV URL Upload Response:", data)
        self.assertEqual(data["status"], "Success")

    @patch("datadoc.views.get_triplestore")
    @patch("datadoc.views.handle_file_url")
    def test_upload_yaml_url(self, mock_handle_file_url, mock_get_triplestore):
        dummy_url = "https://raw.githubusercontent.com/EMMC-ASBL/datadocweb/refs/heads/main/core/static/core/templates/template.yaml"

        mock_get_triplestore.return_value = "mock_ts"
        mock_handle_file_url.return_value = JsonResponse(
            {
                "status": "Success",
                "message": "Mocked YAML file processed",
                "status_code": 200,
            },
            status=200,
        )

        response = self.client.post(self.upload_url, {"url": dummy_url})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("YAML URL Upload Response:", data)
        self.assertEqual(data["status"], "Success")
