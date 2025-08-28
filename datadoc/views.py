"""Implement the views functions"""

from pathlib import Path
import mimetypes
import uuid

from django.conf import settings
from django.shortcuts import render
from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .utils import json_response, get_triplestore, handle_file, handle_file_url


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


from django.shortcuts import render
from django.http import HttpResponse

# from .utils import read_table_from_csv, write_table_to_csv
import csv
import tempfile

# Create temp files once (you can store these paths in memory or settings)
TEMP_HEADINGS_PATH = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
TEMP_CELLS_PATH = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name


def write_table_to_csv(headings, cells):
    with open(TEMP_HEADINGS_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Column", "Title"])
        writer.writerows(headings)

    with open(TEMP_CELLS_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Row", "Column", "Content"])
        writer.writerows(cells)


def read_table_from_csv():
    with open(TEMP_HEADINGS_PATH, newline="") as f:
        headings = list(csv.reader(f))[1:]
    with open(TEMP_CELLS_PATH, newline="") as f:
        cells = list(csv.reader(f))[1:]
    return headings, cells


def table_view(request):

    headings, cells = read_table_from_csv()

    column_ids = [h[0] for h in headings]
    rows = {}

    for row_id, col_id, content in cells:
        rows.setdefault(row_id, {})[col_id] = content

    return render(
        request,
        "datadoc/views/table.html",
        {"headings": headings, "column_ids": column_ids, "rows": rows},
    )


def add_row(request):
    headings, cells = read_table_from_csv()
    max_row = max([int(r[0]) for r in cells], default=-1)
    new_row = max_row + 1

    for h in headings:
        cells.append((new_row, h[0], ""))

    write_table_to_csv(headings, cells)
    return table_view(request)


def add_column(request):
    headings, cells = read_table_from_csv()

    # Generate a unique column ID
    new_col_id = str(uuid.uuid4())
    new_col_title = f"Column {len(headings) + 1}"
    headings.append((new_col_id, new_col_title))

    # Get current row IDs
    row_ids = set(row_id for row_id, _, _ in cells)

    for row_id in row_ids:
        cells.append((row_id, new_col_id, ""))

    write_table_to_csv(headings, cells)
    return table_view(request)


def delete_row(request, row_id):
    headings, cells = read_table_from_csv()
    cells = [c for c in cells if int(c[0]) != row_id]
    write_table_to_csv(headings, cells)
    return table_view(request)


def delete_column(request, col_id):
    headings, cells = read_table_from_csv()

    # Remove the column from headings
    headings = [h for h in headings if h[0] != str(col_id)]

    # Remove all cells in that column
    cells = [c for c in cells if c[1] != str(col_id)]

    write_table_to_csv(headings, cells)
    return table_view(request)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_cell(request, row_id, col_id):
    headings, cells = read_table_from_csv()
    new_content = request.POST.get("content", "").strip()

    updated = False
    for i, (r, c, _) in enumerate(cells):
        if r == str(row_id) and c == str(col_id):
            cells[i] = (r, c, new_content)
            updated = True
            break

    if not updated:
        cells.append((str(row_id), str(col_id), new_content))

    write_table_to_csv(headings, cells)
    return HttpResponse(status=204)  # No content, avoids re-rendering entire table


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def update_column(request, col_id):
    headings, cells = read_table_from_csv()
    new_title = request.POST.get("title", "").strip()

    # Update the title
    for i, (cid, title) in enumerate(headings):
        if cid == str(col_id):
            headings[i] = (cid, new_title)
            break

    write_table_to_csv(headings, cells)
    return table_view(request)
