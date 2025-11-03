"""Implement the views functions"""

from pathlib import Path
import mimetypes
from django.conf import settings
from django.apps import apps
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


def get_setting(name: str, default_value: str = ''):
    """ Return a config value from the datadocweb settings """
    return settings.DATADOCWEB.get(name, default_value)


def init_triplestore():
    """ Init a triple store using the datadocweb config """
    return get_triplestore(settings.DATADOCWEB['triplestore'])


def default_context(request):
    """ Create a default context from the settings and from multiple
        AppConfig.
    """
    ctx = {}
    base = get_setting('base_template', 'datadoc/base.html')
    ctx['datadoc_base_template'] = base
    app_names = get_setting('apps', [])
    for app in apps.get_app_configs():
        if app.name in app_names:
            app.update_context(request, ctx)
    return ctx


def index(request):
    ctx = default_context(request)
    ctx['hide_header'] = True
    return render(request, "datadoc/index.html", ctx)


def home(request):
    ctx = default_context(request)
    return render(request, "datadoc/views/home.html", ctx)


def edit_form(request):
    prefix = get_setting('prefix', {})
    prefix_list = []
    for key, val in prefix.items():
        prefix_list.append({'prefix': key, 'iri': val})
    ctx = default_context(request)
    ctx.update(prefix_list=prefix_list)
    return render(request, "datadoc/views/edit_form.html", context=ctx)


def get_prefixes_view(request):
    """
    Django view to return the list of prefixes from Tripper as JSON.
    """
    prefixes_dict = get_prefixes()
    prefixes = [{'prefix': k, 'iri': v} for k, v in prefixes_dict.items()]
    return JsonResponse({'prefixes': prefixes})


def upload_file(request):
    ctx = default_context(request)
    return render(request, "datadoc/views/upload_file.html", ctx)


def upload_url(request):
    ctx = default_context(request)
    return render(request, "datadoc/views/upload_url.html", ctx)


def explore(request):
    ctx = default_context(request)
    return render(request, "datadoc/views/explore.html", ctx)


def download_template(request, filename):
    """Download a template file"""
    file_templates = get_setting('file_templates', None)
    if isinstance(file_templates, Path):
        template_path = file_templates / filename
        if template_path.exists():
            mime_type, _ = mimetypes.guess_type(template_path)
            return FileResponse(
                open(template_path, "rb"),
                content_type=mime_type,
                as_attachment=True,
                filename=filename,
            )
    raise Http404("Template not found")


# Remove this if CSRF is configured properly and handled in your template
@csrf_exempt
def upload_files(request):
    """Upload files to the triple store"""

    if request.method != "POST" or "files" not in request.FILES:
        return json_response("Error", "No file uploaded")

    ts = init_triplestore()
    return handle_file(request.FILES["files"], ts)


def upload_file_url(request):
    """Upload documentation to the triple store from file URL's"""
    if request.method == "POST":
        url = request.POST.get("url")
        ts = init_triplestore()
        return handle_file_url(url, ts)


@csrf_exempt
def process_csv(request):
    if request.method == "POST":

        ts = init_triplestore()

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
