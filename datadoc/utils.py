from django.http import JsonResponse
import os
import tempfile
import json
from tripper.datadoc import save_datadoc
from tripper.datadoc import store
from tripper.datadoc import told
from tripper.datadoc import TableDoc

SUPPORTED_EXTENSIONS = {
    "spreadsheet": (".xls", ".xlsx", ".csv"),
    "json": (".json", ".jsonld"),
    "yaml": (".yaml", ".yml"),
}


def handle_spreadsheet(uploaded_file, ts):
    def process(path):
        td = TableDoc.parse_csv(path)
        td.save(ts)
        return f"{uploaded_file.name} has populated the Graph"

    result = process_with_temp_file(uploaded_file, "wb", process)
    return JsonResponse(result, status=200 if result["status"] == "Success" else 500)


def handle_json(uploaded_file, ts):
    try:
        dataset = told(json.load(uploaded_file))
        store(ts, dataset)
        return JsonResponse(
            {
                "status": "Success",
                "message": f"{uploaded_file.name} has populated the Graph",
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({"status": "Error", "message": str(e)}, status=500)


def handle_yaml(uploaded_file, ts):
    def process(path):
        save_datadoc(ts, path)
        return f"{uploaded_file.name} has populated the Graph"

    result = process_with_temp_file(uploaded_file, "wb", process)
    return JsonResponse(result, status=200 if result["status"] == "Success" else 500)


def save_uploaded_file_to_temp(uploaded_file, mode="wb"):
    file_extension = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=file_extension, mode=mode
    ) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        return temp_file.name


def process_with_temp_file(uploaded_file, mode, processing_func):
    temp_file_path = None
    try:
        temp_file_path = save_uploaded_file_to_temp(uploaded_file, mode)
        message = processing_func(temp_file_path)
        return {"status": "Success", "message": message}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
