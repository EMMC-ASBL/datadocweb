from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.explore, name="home"),
    path("explore/", views.explore, name="explore"),
    path("upload-url/", views.upload_url, name="upload_url"),
    path("upload-file/", views.upload_file, name="upload_file"),
    # path("edit-form/", views.edit_form, name="edit_form"),
    # non template paths
    path("download/<str:filename>/", views.download_template, name="download_template"),
    path("upload/file/", views.upload_files, name="upload_files"),
    path("upload/url/", views.upload_file_url, name="upload_file_url"),
    path("edit-form/", views.table_view, name="table_view"),
    path("add-row/", views.add_row, name="add_row"),
    path("add-column/", views.add_column, name="add_column"),
    path("delete-row/<int:row_id>/", views.delete_row, name="delete_row"),
    path("delete-column/<int:col_id>/", views.delete_column, name="delete_column"),
    path('update-cell/<int:row_id>/<int:col_id>/', views.update_cell, name='update_cell'),
    path('update-column/<str:col_id>/', views.update_column, name='update_column'),
]
