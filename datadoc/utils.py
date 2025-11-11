"""Util module for datadoc and Django"""

from typing import Callable, Optional
import os
import re
from pathlib import Path
from urllib.parse import urlparse
import tempfile
import json
import requests

from django.conf import settings
from django.http import JsonResponse
from django.core.files.base import File
from django.contrib.auth.models import User

from tripper import Triplestore, RDF
from tripper.datadoc import (
    save_datadoc, store, told, TableDoc, search, acquire
)
from tripper.datadoc.dataset import get_prefixes


SUPPORTED_EXTENSIONS = {
    "spreadsheet": (".xls", ".xlsx", ".csv"),
    "json": (".json", ".jsonld"),
    "yaml": (".yaml", ".yml"),
}
STATUS_CODE = {"Success": 200, "Error": 400, "Exception": 500}


def get_setting(name: str, default_value: str = ''):
    """ Return a config value from the datadocweb settings """
    return settings.DATADOCWEB.get(name, default_value)


def get_triplestore():
    """ Init a triple store using the datadocweb config """
    config = get_setting('triplestore', None)
    if config:
        ts = Triplestore(**config)
        prefix = get_setting('prefix', None)
        if prefix:
            for key, val in prefix.items():
                ts.bind(key, val)
        return ts
    else:
        raise ValueError('config for the triplestore is not found.')


def get_filetype(filemame: str) -> str:
    """Return the file type from its extension"""
    types = {}
    for typ, extensions in SUPPORTED_EXTENSIONS.items():
        for ext in extensions:
            types[ext] = typ
    return types.get(Path(filemame).suffix.lower(), "")


def json_response(status: str, message: str = "", status_code: int = None):
    """Return a JsonResponse with status code selected based on status string
    and included in the response body.
    """
    if isinstance(status_code, int):
        resolved_status_code = status_code
    else:
        resolved_status_code = STATUS_CODE.get(status, 501)
    content = {
        "status": status,
        "message": message,
        "status_code": resolved_status_code,
    }
    return JsonResponse(content, status=resolved_status_code)


def write_csv(
    path: str, ts: Triplestore, headers: Optional[dict] = None
) -> JsonResponse:
    """Document data in CSV format"""
    try:
        td = TableDoc.parse_csv(path)
        td.save(ts)
        return json_response("Success", "File has populated the Graph")
    except Exception as ex:
        return json_response("Exception", str(ex))


def write_yaml(
    path: str, ts: Triplestore, headers: Optional[dict] = None
) -> JsonResponse:
    """Document data in YAML format"""
    try:
        save_datadoc(ts, path)
        return json_response("Success", "File has populated the Graph")
    except Exception as ex:
        return json_response("Exception", str(ex))


def write_json(
    path: str, ts: Triplestore, headers: Optional[dict] = None
) -> JsonResponse:
    """Document data in JSON format"""
    try:
        response = requests.get(path, headers=headers)
        if response.status_code == 200:
            dataset = told(json.loads(response.text))
            store(ts, dataset)
            return json_response("Success", "File has populated the Graph")
        else:
            msg = f"Failed to fetch file. Status code: {response.status_code}"
            return json_response("Error", msg)
    except Exception as ex:
        return json_response("Exception", str(ex))


def handle_spreadsheet(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """Upload a spreadsheet file"""

    return process_with_temp_file(uploaded_file, "wb", write_csv, ts)


def handle_json(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """Upload a JSON file"""
    status = ""
    try:
        dataset = told(json.load(uploaded_file))
        store(ts, dataset)
        status = "Success"
        message = f"{uploaded_file.name} has populated the Graph"
    except Exception as ex:
        status = "Exception"
        message = str(ex)
    return json_response(status, message)


def handle_yaml(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """Upload a YAML file"""

    return process_with_temp_file(uploaded_file, "wb", write_yaml, ts)


def handle_file(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """Update a file to the triplestore"""
    try:
        filetype = get_filetype(uploaded_file.name)
        if filetype == "spreadsheet":
            return handle_spreadsheet(uploaded_file, ts)
        elif filetype == "json":
            return handle_json(uploaded_file, ts)
        elif filetype == "yaml":
            return handle_yaml(uploaded_file, ts)
        else:
            ext = Path(uploaded_file.name).suffix
            return json_response("Error", f'Unsupported file type "{ext}"')
    except Exception as ex:
        return json_response("Exception", str(ex))


def handle_file_url(url: str, ts: Triplestore) -> JsonResponse:
    """Update a file from url to the triplestore"""
    try:
        filetype = get_filetype(url)
        if filetype == "spreadsheet":
            return write_csv(url, ts)
        elif filetype == "json":
            return write_json(url, ts)
        elif filetype == "yaml":
            return write_yaml(url, ts)
        else:
            ext = Path(url).suffix
            return json_response("Error", f'Unsupported file type "{ext}"')
    except Exception as ex:
        return json_response("Exception", str(ex))


def save_uploaded_file_to_temp(uploaded_file: File, mode: str = "wb"):
    """Save file content to temp file"""
    file_extension = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=file_extension, mode=mode
    ) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        return temp_file.name


def process_with_temp_file(
    uploaded_file: File, mode: str, processing_func: Callable, ts: Triplestore
):
    """Upload a temporary file"""
    temp_file_path = None
    try:
        temp_file_path = save_uploaded_file_to_temp(uploaded_file, mode)
        return processing_func(temp_file_path, ts)
    except Exception as e:
        return json_response("Exception", str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def process_csv_form(csv_data: str, ts: Triplestore):
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", newline=""
        ) as temp_file:
            temp_file.write(csv_data)
            temp_file_path = temp_file.name
            temp_file.close()
        return write_csv(temp_file_path, ts)

    except Exception as e:
        return json_response("Exception", str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def _convert(value, dtype, default=None):
    try:
        v = dtype(value)
    except Exception:
        v = default
    return v


def normalize_name(name: str) -> str:
    """ Converts camelCase or snake_case to space-separated words """
    if name.startswith('EMMO_'):
        return name
    else:
        # Handle upper case
        name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)
        # Handle camel case
        name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
        # Handle underscores
        name = re.sub(r'_+', ' ', name)
        # Capitalize first letters
        return ' '.join(f'{w[0].upper()}{w[1:]}' for w in name.split())


def _split_iri(iri: str, sep: str):
    p = iri.rfind(sep)
    path = iri[0:p+1]
    name = iri[p+1:]
    return path, name


def split_iri(iri: str, iri_prefix: dict = None):
    """ Split IRI to (path, name, prefix) and "iri_prefix" is a dict
        with key=iri, value=prefix.
    """
    path = ''
    name = ''
    prefix = ''
    if '#' in iri:
        path, name = _split_iri(iri, '#')
    elif '/' in iri:
        path, name = _split_iri(iri, '/')
    elif ':' in iri:
        prefix, name = iri.split(':', 1)

    if prefix and name:
        return ('', name, prefix)
    elif path and name:
        if iri_prefix:
            if path not in iri_prefix:
                iri_prefix[path] = f'prefix{len(iri_prefix)+1}'
        return (path, name, iri_prefix[path] if iri_prefix else '')
    else:
        return (path, name, prefix)


def substring_index(text: str, substring: str):
    try:
        i = text.index(substring)
    except Exception:
        i = -1
    return i


def value_to_cell(value: str, header: str) -> dict:
    """ Return cell attributes for HTML tag TD """
    attrs = {}
    cell = {'value': value, 'text': '', 'href': '', 'attrs_dict': attrs}
    if isinstance(value, str):
        cell['text'] = value
        # value starts with: http, https, ftp, file, ...
        if substring_index(value, '://') in [3, 4, 5]:
            if 'download' in header:
                url = urlparse(value)
                cell['href'] = value
                cell['text'] = Path(url.path).name
            elif header == '@type':
                path, name, prefix = split_iri(value)
                if name:
                    attrs['title'] = value
                    cell['text'] = normalize_name(name)

    elif isinstance(value, float):
        cell['text'] = f'{value:g}'

    else:
        cell['text'] = '' if value is None else f'{value}'

    cell['attrs'] = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])

    return cell


def get_email_and_config(context: dict, user: User):
    cfg = get_setting('config_base_iri')
    usr = getattr(user, 'email', '')
    if not usr:
        if 'user' in context:
            usr = context['user']['email']
    return usr, cfg


def fetch_user_filters(ts: Triplestore, email: str, config: str) -> list:
    """ Fetch user filters """
    filters = []

    # s = f'mailto:{email}'
    # p = f'{config}explore#hasFilter'

    # query = f'SELECT DISTINCT ?o WHERE {{ <{s}> <{p}> ?o . }}'
    # for item in ts.query(query):
    #     if item:
    #         selected_filters.add(item[0])

    # remove = []
    # for item in filters:
    #     if item['value'] == p:
    #         remove.append(item)
    # for item in remove:
    #     filters.remove(item)

    return filters


def post_user_filter(ts: Triplestore, email: str, config: str, filter: str):
    pass


def delete_user_filter(ts: Triplestore, email: str, config: str, filter: str):
    pass


def triplestore_filters(context: dict, user: User = None) -> dict:
    """ Search distinct predicates in the triplestore """
    # init the triplestore
    ts = get_triplestore()

    # get all prefixes and reverse the map
    prefix_iri = get_prefixes()
    iri_prefix = {}
    for prefix, iri in prefix_iri.items():
        iri_prefix[iri] = prefix
    for prefix, iri in get_setting('prefix', {}).items():
        iri_prefix[iri] = prefix
        prefix_iri[prefix] = iri

    # expand prefix for the query items
    rdf_type = ''
    criterias = {}
    for key, value in context['query'].items():
        if key == 'rdf_type':
            rdf_type = value
        elif '_' in key:
            prefix, name = key.split('_', 1)
            if prefix in prefix_iri:
                criterias[f'{prefix_iri[prefix]}{name}'] = value
            else:
                criterias[f'{prefix}:{name}'] = value
    context.update(search={'rdf_type': rdf_type, 'criterias': criterias})

    # search all filters
    filters = {}
    for item in ts.query('SELECT DISTINCT ?p WHERE { ?s ?p ?o . }'):
        if item:
            iri = item[0]
            _, name, prefix = split_iri(iri, iri_prefix)
            if name and prefix:
                filters[iri] = dict(
                    value=iri,
                    text=normalize_name(name),
                    name=f'{prefix}_{name}'
                )

    # a list of pre-selected filters
    selected = []

    # init filter on "type"
    if RDF.type in filters:
        choices = triplestore_filter_choices(RDF.type, rdf_type, ts, True)
        filters[RDF.type]['choices'] = choices
        selected.append(filters[RDF.type])

    # add the selected filters from the query
    for iri, value in criterias.items():
        if iri in filters:
            choices = triplestore_filter_choices(iri, value, ts, False)
            filters[iri]['choices'] = choices
            selected.append(filters[iri])

    # fetch the filters that have been previoulsy selected by the user
    email, config = get_email_and_config(context, user)
    if email and config:
        for item in fetch_user_filters(ts, email, config):
            if item in filters:
                selected.append(filters[item])

    # update the context for rendering the page
    items = list(filters.values())
    context.update(filters={'items': items, 'selected': selected})


def triplestore_filter_choices(
        predicate: str,
        selection: str = '',
        ts: Triplestore = None,
        norm: bool = False) -> list:
    """ Search distinct values for the given filter """
    if ts is None:
        ts = get_triplestore()

    choices = []
    query = f'SELECT DISTINCT ?o WHERE {{ ?s <{predicate}> ?o . }}'
    for item in ts.query(query):
        if item:
            value = item[0]
            opt = {'value': value, 'text': value, 'selected': ''}
            if norm:
                _, name, _ = split_iri(value)
                opt['text'] = normalize_name(name)
            if selection:
                if selection == value:
                    opt['selected'] = 'selected'
            choices.append(opt)

    if choices:
        choices.insert(0, {'value': '--- none ---', 'text': 'Select...'})
    return choices


def get_pagination(nrow, page, size=10, nmax=10):
    """ Compute the pagination """
    size = _convert(size, int, 10)
    npage = (nrow // size)
    if nrow % size > 0:
        npage += 1
    page = min(npage, max(1, _convert(page, int, 1)))

    i = nmax // 2
    m = npage // 2
    a = max(1, page - i)
    b = min(page + i, npage)
    if b - a < nmax:
        if page < m:
            b = min(nmax, npage)
        else:
            a = max(1, npage - nmax + 1)
    else:
        a += 1
    p = list(range(a, b + 1))
    pages = {
        'nrow': nrow,
        'active': page,
        'npage': npage,
        'prev': 'disabled' if p[0] == 1 else '',
        'next': 'disabled' if p[-1] == npage else '',
        'numbers': p,
        'start': (page - 1) * size,
        'stop': min(page * size, nrow),
        'page_size': size
    }
    return pages


def triplestore_search(dtype: str, criterias: dict,
                       page: int = 1, size: int = 10) -> dict:
    """ Search in the triplestore """
    ts = get_triplestore()
    iris = search(ts, dtype, criteria=criterias)
    pages = get_pagination(len(iris), page, size)

    start = pages['start']
    stop = pages['stop']

    dicts = [acquire(ts, iris[i]) for i in range(start, stop)]
    td = TableDoc.fromdicts(dicts)

    rows = []
    for row in td.data:
        newrow = [value_to_cell(v, h) for v, h in zip(row, td.header)]
        rows.append(newrow)

    columns = []
    for header in td.header:
        key = header.strip('@')
        path, name, prefix = split_iri(key)
        columns.append(normalize_name(name if name else key))

    result = {
        'table': {'cols': columns, 'rows': rows},
        'prefix': {k: f'{v}' for k, v in ts.namespaces.items()},
        'pages': pages
    }

    return result
