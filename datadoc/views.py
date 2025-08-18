from django.shortcuts import render
from django.http import FileResponse, Http404
import os
import mimetypes
from django.conf import settings
import pandas as pd
from tripper.datadoc import TableDoc
from tripper import Triplestore
import tempfile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

select_iri = "http://localhost:7200/repositories/matchmaker"
update_iri = "http://localhost:7200/repositories/matchmaker/statements"


def index(request):
    return render(request, "datadoc/index.html")


def home(request):
    return render(request, "datadoc/views/home.html")


def edit_form(request):
    return render(request, "datadoc/views/edit_form.html")


def upload(request):
    return render(request, "datadoc/views/upload.html")


def explore(request):
    return render(request, "datadoc/views/explore.html")


def download_template(request, filename):
    template_path = os.path.join(
        settings.BASE_DIR, "core/static/core/templates", filename
    )
    if os.path.exists(template_path):
        mime_type, _ = mimetypes.guess_type(template_path)
        response = FileResponse(open(template_path, "rb"), content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        raise Http404("Template not found")


@csrf_exempt  # Remove this if CSRF is configured properly and handled in your template
def upload_file(request):
    if request.method == "POST" and request.FILES.get("files"):
        uploaded_file = request.FILES["files"]

        ts = Triplestore("sparqlwrapper", base_iri=select_iri, update_iri=update_iri)

        if uploaded_file.name.endswith((".xls", ".xlsx", ".csv")):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            try:
                td = TableDoc.parse_csv(temp_file_path)
                td.save(ts)
                result_message = f"{uploaded_file.name} has populated the Graph"
            except Exception as e:
                result_message = f"Error: {str(e)}"
            finally:
                os.remove(temp_file_path)
        return JsonResponse({"status": "success", "message": result_message})
