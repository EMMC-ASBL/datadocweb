from django.shortcuts import render
from django.http import FileResponse, Http404
import os
import mimetypes
from django.conf import settings
from tripper import Triplestore
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .utils import SUPPORTED_EXTENSIONS, handle_spreadsheet, handle_json, handle_yaml

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
    if request.method != "POST" or "files" not in request.FILES:
        return JsonResponse(
            {"status": "Error", "message": "No file uploaded"}, status=400
        )

    uploaded_file = request.FILES["files"]
    filename = uploaded_file.name.lower()
    ts = Triplestore("sparqlwrapper", base_iri=select_iri, update_iri=update_iri)

    try:
        if filename.endswith(SUPPORTED_EXTENSIONS["spreadsheet"]):
            return handle_spreadsheet(uploaded_file, ts)

        elif filename.endswith(SUPPORTED_EXTENSIONS["json"]):
            return handle_json(uploaded_file, ts)

        elif filename.endswith(SUPPORTED_EXTENSIONS["yaml"]):
            return handle_yaml(uploaded_file, ts)

        else:
            return JsonResponse(
                {"status": "Error", "message": "Unsupported file type"}, status=400
            )

    except Exception as e:
        return JsonResponse(
            {"status": "Error", "message": f"Unexpected error: {str(e)}"}, status=500
        )
