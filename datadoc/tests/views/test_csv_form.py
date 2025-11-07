import os
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse


class ProcessCSVTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.process_csv_url = reverse("datadoc:process_csv")

    @patch("datadoc.views.get_triplestore")
    @patch("datadoc.views.process_csv_form")
    def test_process_valid_csv_data(self, mock_process_csv_form, mock_get_triplestore):
        csv_data = "@id,@type\nsemdata:77600-23-001_5kV_400x_m001,sem:SEMImage\nsemdata:77600-23-001_5kV_400x_m002,sem:SEMImage"

        mock_get_triplestore.return_value = "mock_ts"
        mock_process_csv_form.return_value = JsonResponse(
            {
                "status": "Success",
                "message": "CSV processed successfully",
                "status_code": 200,
            },
            status=200,
        )

        response = self.client.post(self.process_csv_url, {"csv_data": csv_data})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("Valid CSV Response:", data)
        self.assertEqual(data["status"], "Success")

    @patch("datadoc.views.get_triplestore")
    @patch("datadoc.views.process_csv_form")
    def test_process_invalid_csv_data(
        self, mock_process_csv_form, mock_get_triplestore
    ):
        csv_data = "name|age\nAlice|30\nBob|25"  # Invalid delimiter

        mock_get_triplestore.return_value = "mock_ts"
        mock_process_csv_form.return_value = JsonResponse(
            {
                "status": "Exception",
                "message": "Invalid CSV format",
                "status_code": 500,
            },
            status=500,
        )

        response = self.client.post(self.process_csv_url, {"csv_data": csv_data})
        self.assertEqual(response.status_code, 500)
        data = response.json()
        print("Invalid CSV Response:", data)
        self.assertEqual(data["status"], "Exception")
