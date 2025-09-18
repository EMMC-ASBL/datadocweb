"""Implement the views functions"""

from pathlib import Path
import mimetypes
from django.conf import settings
from django.shortcuts import render
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from tripper.datadoc.dataset import get_prefixes
from django.http import JsonResponse
from .utils import (
    json_response,
    get_triplestore,
    handle_file,
    handle_file_url,
    process_csv_form,
)


def index(request):
    return render(request, "datadoc/index.html")


def home(request):
    return render(request, "datadoc/views/home.html")


def edit_form(request):
    prefix = {
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'prov': 'http://www.w3.org/ns/prov#',
    }
    prefix_list = []
    for key, val in prefix.items():
        prefix_list.append({'prefix': key, 'iri': val})
    ctx = dict(prefix_list=prefix_list)
    return render(request, "datadoc/views/edit_form.html", context=ctx)

def get_prefixes_view(request):
    """
    Django view to return the list of prefixes from Tripper as JSON.
    """
    prefixes_dict = get_prefixes() 
    prefixes = [{'prefix': k, 'iri': v} for k, v in prefixes_dict.items()]
    return JsonResponse({'prefixes': prefixes})

def upload_file(request):
    return render(request, "datadoc/views/upload_file.html")


def upload_url(request):
    return render(request, "datadoc/views/upload_url.html")


def explore(request):
    return render(request, "datadoc/views/explore.html")


def download_template(request, filename):
    """Download a template file"""
    base_dir: Path = settings.BASE_DIR
    template_path = base_dir / f"core/static/core/templates/{filename}"
    if template_path.exists():
        mime_type, _ = mimetypes.guess_type(template_path)
        return FileResponse(
            open(template_path, "rb"),
            content_type=mime_type,
            as_attachment=True,
            filename=filename,
        )
    else:
        raise Http404("Template not found")


# Remove this if CSRF is configured properly and handled in your template
@csrf_exempt
def upload_files(request):
    """Upload files to the triple store"""

    if request.method != "POST" or "files" not in request.FILES:
        return json_response("Error", "No file uploaded")

    ts = get_triplestore(settings.DATADOCWEB["triplestore"])
    return handle_file(request.FILES["files"], ts)


def upload_file_url(request):
    """Upload documentation to the triple store from file URL's"""
    if request.method == "POST":
        url = request.POST.get("url")
        ts = get_triplestore(settings.DATADOCWEB["triplestore"])
        return handle_file_url(url, ts)

@csrf_exempt
def process_csv(request):
    if request.method == "POST":

        ts = get_triplestore(settings.DATADOCWEB["triplestore"])

        csv_prefix = request.POST.get("csv_prefix")
        if csv_prefix:
            for line in csv_prefix.splitlines():
                kv = line.split(':', 1)
                if len(kv) == 2:
                    pr, ns = kv
                    if pr and ns:
                        ts.bind(pr, ns)

        csv_data = request.POST.get("csv_data")
        return process_csv_form(csv_data, ts)
