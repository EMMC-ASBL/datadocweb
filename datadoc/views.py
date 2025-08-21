
""" Implement the views functions """

from pathlib import Path
import mimetypes

from django.conf import settings
from django.shortcuts import render
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .utils import json_response, get_triplestore, handle_file


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
    """ Download a template file """
    base_dir: Path = settings.BASE_DIR
    template_path = base_dir / f"core/static/core/templates/{filename}"
    if template_path.exists():
        mime_type, _ = mimetypes.guess_type(template_path)
        return FileResponse(open(template_path, "rb"), content_type=mime_type,
                            as_attachment=True, filename=filename)
    else:
        raise Http404("Template not found")


# Remove this if CSRF is configured properly and handled in your template
@csrf_exempt
def upload_files(request):
    """ Upload files to the triple store """

    if request.method != "POST" or "files" not in request.FILES:
        return json_response('Error', 'No file uploaded')

    ts = get_triplestore(settings.DATADOCWEB['triplestore'])
    return handle_file(request.FILES["files"], ts)
