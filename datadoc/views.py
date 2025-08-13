from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, "datadoc/index.html")


def hello(request):
    return HttpResponse("<p>Hello from HTMX!</p>")


def home(request):
    return HttpResponse("<p>Welcome to the app!</p>")
