from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.explore, name="home"),
    path("explore/", views.explore, name="explore"),
    path("upload/", views.upload, name="upload"),
    path("edit-form/", views.edit_form, name="edit_form"),
    path("download/<str:filename>/", views.download_template, name="download_template"),
]
