from django.test import TestCase
from django.urls import reverse


class EditFormViewTests(TestCase):
    def test_documentation_form_renders_correctly(self):
        url = reverse("datadoc:edit_form")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Add column")
        self.assertContains(response, "Add row")

        self.assertContains(response, 'id="dialog"')
        self.assertContains(response, "<script>", count=2)

        self.assertContains(response, "function addColumn()")
        self.assertContains(response, "function generateCSV()")
        self.assertContains(response, "function addRow()")
