from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "datadoc/index.html")


def hello(request):
    return HttpResponse("<p>Hello from HTMX!</p>")


def home(request):
    return render(request, "datadoc/views/home.html")


def editForm(request):
    return render(request, "datadoc/views/editForm.html")


def upload(request):
    return render(request, "datadoc/views/upload.html")


def explore(request):
    return render(request, "datadoc/views/explore.html")
