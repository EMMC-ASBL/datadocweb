
""" Define the URLs of the DataDocWeb Django App """

from django.urls import path

from . import views

urlpatterns = []
for cls in views.REGISTERED_VIEWS:
    urlpatterns.append(path(cls.path, cls.as_view(), name=cls.name))
