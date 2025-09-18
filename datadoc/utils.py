"""Util module for datadoc and Django"""

from typing import Callable, Optional
import os
from pathlib import Path
import tempfile
import json
import requests
from django.http import JsonResponse
from django.core.files.base import File

from tripper import Triplestore
from tripper.datadoc import save_datadoc, store, told, TableDoc


SUPPORTED_EXTENSIONS = {
    "spreadsheet": (".xls", ".xlsx", ".csv"),
    "json": (".json", ".jsonld"),
    "yaml": (".yaml", ".yml"),
}
STATUS_CODE = {"Success": 200, "Error": 400, "Exception": 500}


def get_triplestore(config: dict):
    """Returns instance of Triplestore from the config"""
    return Triplestore(**config)


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
