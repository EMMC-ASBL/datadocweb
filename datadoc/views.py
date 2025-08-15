from django.shortcuts import render
from django.http import FileResponse, Http404
import os
import mimetypes
from django.conf import settings


def index(request):
    return render(request, "datadoc/index.html")


def home(request):
    return render(request, "datadoc/views/home.html")


def editForm(request):
    return render(request, "datadoc/views/editForm.html")


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
