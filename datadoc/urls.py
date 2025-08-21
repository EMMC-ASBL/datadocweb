from django.urls import path
from . import views

urlpatterns = [
    # template paths
    path("", views.index, name="index"),
    path("home/", views.explore, name="home"),
    path("explore/", views.explore, name="explore"),
    path("upload-url/", views.upload_url, name="upload_url"),
    path("upload-file/", views.upload_file, name="upload_file"),
    path("edit-form/", views.edit_form, name="edit_form"),
    # non template paths
    path("download/<str:filename>/", views.download_template, name="download_template"),
    path("upload/file/", views.upload_files, name="upload_files"),
]
