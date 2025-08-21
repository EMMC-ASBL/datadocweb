
""" Util module for datadoc and Django """

from typing import Callable
import os
from pathlib import Path
import tempfile
import json

from django.http import JsonResponse
from django.core.files.base import File

from tripper import Triplestore
from tripper.datadoc import save_datadoc, store, told, TableDoc


SUPPORTED_EXTENSIONS = {
    "spreadsheet": (".xls", ".xlsx", ".csv"),
    "json": (".json", ".jsonld"),
    "yaml": (".yaml", ".yml"),
}
STATUS_CODE = {'Success': 200, 'Error': 400, 'Exception': 500}


def get_triplestore(config: dict):
    """ Returns instance of Triplestore from the config """
    return Triplestore(**config)


def get_filetype(filemame: str) -> str:
    """ Return the file type from its extension """
    types = {}
    for typ, extensions in SUPPORTED_EXTENSIONS.items():
        for ext in extensions:
            types[ext] = typ
    return types.get(Path(filemame).suffix.lower(), '')


def json_response(status: str, message: str = '', status_code: int = None):
    """ Return a django.http.JsonResponse """
    content = status
    if isinstance(status, str):
        content = dict(status=status, message=message)
    if not isinstance(status_code, int):
        status_code = STATUS_CODE.get(content['status'], 501)
    return JsonResponse(content, status=status_code)


def handle_spreadsheet(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """ Upload a spreadsheet file """

    def process(path):
        td = TableDoc.parse_csv(path)
        td.save(ts)
        return f"{uploaded_file.name} has populated the Graph"

    result = process_with_temp_file(uploaded_file, "wb", process)
    return json_response(result)


def handle_json(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """ Upload a JSON file """
    status = ''
    try:
        dataset = told(json.load(uploaded_file))
        store(ts, dataset)
        status = 'Success'
        message = f"{uploaded_file.name} has populated the Graph"
    except Exception as ex:
        status = 'Exception'
        message = str(ex)
    return json_response(status, message)


def handle_yaml(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """ Upload a YAML file """

    def process(path):
        save_datadoc(ts, path)
        return f"{uploaded_file.name} has populated the Graph"

    result = process_with_temp_file(uploaded_file, "wb", process)
    return json_response(result)


def handle_file(uploaded_file: File, ts: Triplestore) -> JsonResponse:
    """ Update a file to the triplestore """
    filetype = get_filetype(uploaded_file.name)
    try:
        if filetype == 'spreadsheet':
            return handle_spreadsheet(uploaded_file, ts)
        elif filetype == 'json':
            return handle_json(uploaded_file, ts)
        elif filetype == 'yaml':
            return handle_yaml(uploaded_file, ts)
        else:
            ext = Path(uploaded_file.name).suffix
            return json_response('Error', f'Unsupported file type "{ext}"')
    except Exception as ex:
        return json_response('Exception', str(ex))


def save_uploaded_file_to_temp(uploaded_file: File, mode: str = "wb"):
    """ Save file content to temp file """
    file_extension = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=file_extension, mode=mode
    ) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        return temp_file.name


def process_with_temp_file(uploaded_file: File, mode: str,
                           processing_func: Callable):
    """ Upload a temporary file """
    temp_file_path = None
    try:
        temp_file_path = save_uploaded_file_to_temp(uploaded_file, mode)
        message = processing_func(temp_file_path)
        return {"status": "Success", "message": message}
    except Exception as e:
        return {"status": "Exception", "message": str(e)}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
