from django.test import TestCase
from django.urls import reverse


class EditFormViewTests(TestCase):
    def test_documentation_form_renders_correctly(self):
        url = reverse("edit_form")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "➕ Add Column")
        self.assertContains(response, "➕ Add Row")
        self.assertContains(response, "Submit Documentation")

        self.assertContains(response, 'id="successModal"')
        self.assertContains(response, "<script>", count=1)

        self.assertContains(response, "function addColumn()")
        self.assertContains(response, "function generateCSV()")
        self.assertContains(response, "function addRow()")
