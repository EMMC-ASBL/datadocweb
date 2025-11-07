from django.test import TestCase
from django.urls import reverse

class TemplateDownloadTests(TestCase):
    def test_excel_template_download_url(self):
        url = reverse('datadoc:download_template', args=['template.csv'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="template.csv"')

    def test_jsonld_template_download_url(self):
        url = reverse('datadoc:download_template', args=['template.json'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="template.json"')

    def test_yaml_template_download_url(self):
        url = reverse('datadoc:download_template', args=['template.yaml'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="template.yaml"')
