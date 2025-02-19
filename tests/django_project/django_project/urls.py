"""
URL configuration for django_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
try:
    from ms_identity_web.django.msal_views_and_urls import MsalViews
except Exception:
    MsalViews = None


app = 'datadocweb'
ns = f'{app}.django'
urlpatterns = [
    path(f'{app}/', include((ns + '.urls', ns), namespace=app)),
    path('', include('dashboard.urls')),
    path('admin/', admin.site.urls)
]
if (MsalViews is not None) & (settings.MS_IDENTITY_WEB is not None):
    msal_urls = MsalViews(settings.MS_IDENTITY_WEB).url_patterns()
    aad_django = settings.AAD_CONFIG.django
    urlpatterns += [
        path(f'{aad_django.auth_endpoints.prefix}/', include(msal_urls)),
    ]
