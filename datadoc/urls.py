from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.explore, name="home"),
    path("explore/", views.explore, name="explore"),
    path("upload-url/", views.upload_url, name="upload_url"),
    path("upload-file/", views.upload_file, name="upload_file"),
    path("edit-form/", views.edit_form, name="edit_form"),
    # non template paths
    path("download/<str:filename>/", views.download_template, name="download_template"),
    path("upload/file/", views.upload_files, name="upload_files"),
    path("upload/url/", views.upload_file_url, name="upload_file_url"),
    path("process-csv/", views.process_csv, name="process_csv"),
    path('get-prefixes/', views.get_prefixes_view, name='get_prefixes'),
]
