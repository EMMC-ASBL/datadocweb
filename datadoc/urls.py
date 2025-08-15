from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.explore, name="home"),
    path("explore/", views.explore, name="explore"),
    path("upload/", views.upload, name="upload"),
    path("editForm/", views.editForm, name="editForm"),
    path("download/<str:filename>/", views.download_template, name="download_template"),
]
