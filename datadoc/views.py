from django.shortcuts import render
from django.http import FileResponse, Http404
import os
import mimetypes
from django.conf import settings
from tripper.datadoc import TableDoc
from tripper import Triplestore
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from tripper.datadoc import save_datadoc
from tripper.datadoc import store
from tripper.datadoc import told
import json
from .utils import process_with_temp_file

# Move this to env file
select_iri = "http://localhost:7200/repositories/matchmaker"
update_iri = "http://localhost:7200/repositories/matchmaker/statements"


def index(request):
    return render(request, "datadoc/index.html")


def home(request):
    return render(request, "datadoc/views/home.html")


def edit_form(request):
    return render(request, "datadoc/views/edit_form.html")


def upload_file(request):
    return render(request, "datadoc/views/upload_file.html")


def upload_url(request):
    return render(request, "datadoc/views/upload_url.html")


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
def upload_files(request):
    if request.method != "POST" or not request.FILES.get("files"):
        return JsonResponse({"status": "Not Success", "message": "No file uploaded"})

    uploaded_file = request.FILES["files"]
    filename = uploaded_file.name.lower()
    ts = Triplestore("sparqlwrapper", base_iri=select_iri, update_iri=update_iri)

    try:
        if filename.endswith((".xls", ".xlsx", ".csv")):

            def process_csv(path):
                td = TableDoc.parse_csv(path)
                td.save(ts)
                return f"{uploaded_file.name} has populated the Graph"

            result = process_with_temp_file(uploaded_file, "wb", process_csv)

        elif filename.endswith((".json", ".jsonld")):
            try:
                dataset = told(json.load(uploaded_file))
                store(ts, dataset)
                result = {
                    "status": "Success",
                    "message": f"{uploaded_file.name} has populated the Graph",
                }
            except Exception as e:
                result = {"status": "Error", "message": str(e)}

        elif filename.endswith((".yaml", ".yml")):

            def process_yaml(path):
                save_datadoc(ts, path)
                return f"{uploaded_file.name} has populated the Graph"

            result = process_with_temp_file(uploaded_file, "wb", process_yaml)
        else:
            result = {"status": "Not Success", "message": "Invalid file type"}

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"status": "Error", "message": str(e)})
