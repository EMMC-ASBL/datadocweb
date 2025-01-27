
""" The Django App config for Raufoss DB """

from django.apps import AppConfig


class DataDocWebConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"
    name = "datadocweb.django"
    label = "datadocweb"
    verbose_name = 'Data Documentation Web Tools'
    # attribute needed for the physmet portal
    physmet = True
