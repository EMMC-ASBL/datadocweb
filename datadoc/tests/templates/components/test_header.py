from django.test import TestCase
from django.urls import reverse

class NavbarTemplateTests(TestCase):
    def test_navbar_template_renders_correctly(self):
        response = self.client.get(reverse('explore'))  
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('src="/static/datadoc/ddw.jpg"', content)
        self.assertIn('href="/explore"', content)
        self.assertIn('href="/upload-url"', content)
        self.assertIn('href="/upload-file"', content)
        self.assertIn('href="/edit-form"', content)
        self.assertIn('navbar navbar-expand-lg navbar-light', content)
        self.assertIn('dropdown-menu', content)
