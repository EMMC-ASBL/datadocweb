import os
import tempfile


def save_uploaded_file_to_temp(uploaded_file, mode="wb"):
    file_extension = os.path.splitext(uploaded_file.name)[1]
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=file_extension, mode=mode
    )
    for chunk in uploaded_file.chunks():
        temp_file.write(chunk)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    temp_file_path = temp_file.name
    temp_file.close()
    return temp_file_path


def process_with_temp_file(uploaded_file, mode, processing_func):
    temp_file_path = None
    try:
        temp_file_path = save_uploaded_file_to_temp(uploaded_file, mode)
        return {"status": "Success", "message": processing_func(temp_file_path)}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
