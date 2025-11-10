"""Implement the views functions"""

from pathlib import Path
import mimetypes

from django.apps import apps
from django.shortcuts import render
from django.http import FileResponse, Http404, JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from tripper.datadoc.dataset import get_prefixes
from .utils import (
    json_response,
    get_triplestore,
    handle_file,
    handle_file_url,
    process_csv_form,
    get_setting,
    triplestore_search,
    triplestore_filters,
    triplestore_filter_choices
)


def default_context(request: HttpRequest):
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


def index(request: HttpRequest):
    ctx = default_context(request)
    ctx['hide_header'] = True
    return render(request, "datadoc/index.html", ctx)


def home(request: HttpRequest):
    ctx = default_context(request)
    return render(request, "datadoc/views/home.html", ctx)


def edit_form(request: HttpRequest):
    prefix = get_setting('prefix', {})
    prefix_list = []
    for key, val in prefix.items():
        prefix_list.append({'prefix': key, 'iri': val})
    ctx = default_context(request)
    ctx.update(prefix_list=prefix_list)
    return render(request, "datadoc/views/edit_form.html", context=ctx)


def get_prefixes_view(request: HttpRequest):
    """
    Django view to return the list of prefixes from Tripper as JSON.
    """
    prefixes_dict = get_prefixes()
    prefixes = [{'prefix': k, 'iri': v} for k, v in prefixes_dict.items()]
    return JsonResponse({'prefixes': prefixes})


def upload_file(request: HttpRequest):
    ctx = default_context(request)
    return render(request, "datadoc/views/upload_file.html", ctx)


def upload_url(request: HttpRequest):
    ctx = default_context(request)
    return render(request, "datadoc/views/upload_url.html", ctx)


def explore(request: HttpRequest):
    """ Search in triple store """
    ctx = default_context(request)

    if request.method == 'GET':
        # get the query
        ctx['query'] = request.GET.dict()

        # fetch the filters and update the context
        triplestore_filters(ctx, request.user)

        ctx['error'] = ''
        rdf_type = ctx['search']['rdf_type']
        criterias = ctx['search']['criterias']
        if rdf_type or criterias:
            try:
                ctx['table'] = triplestore_search(rdf_type, criterias)
            except Exception as ex:
                doc = ex.__class__.__doc__
                if not doc:
                    doc = ex.__class__.__name__
                err = str(ex).strip("'")
                ctx['error'] = f'{doc.rstrip(".")}: "{err}".'

        return render(request, "datadoc/views/explore.html", ctx)

    elif request.method == 'POST':
        print(request.POST)
        name = request.POST.get('name', '')
        criteria = request.POST.get('criteria', '')
        choices = triplestore_filter_choices(criteria)
        data = {'name': name, 'choices': choices}
        return JsonResponse(data)

    elif request.method == 'DELETE':
        print(request.GET)
        criteria = request.GET.get('criteria', '')
        # choices = triplestore_filter_choices(criteria)
        data = {'status': 'deleted'}
        return JsonResponse(data)


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


def upload_files(request):
    """Upload files to the triple store"""

    if request.method != "POST" or "files" not in request.FILES:
        return json_response("Error", "No file uploaded")

    ts = get_triplestore()
    return handle_file(request.FILES["files"], ts)


def upload_file_url(request):
    """Upload documentation to the triple store from file URL's"""
    if request.method == "POST":
        url = request.POST.get("url")
        ts = get_triplestore()
        return handle_file_url(url, ts)


@csrf_exempt
def process_csv(request):
    if request.method == "POST":

        ts = get_triplestore()

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
