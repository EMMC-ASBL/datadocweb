
""" The web app views """

from datadocweb.django.appview import AppView
from datadocweb.django.views import Home, UploadData

Home.login_required = False
UploadData.login_required = False


class Home(AppView):

    name = 'index'
    path = ''
    template = 'index'
    login_required = False

    def get(self, request):
        return self.render(request)


class About(AppView):

    name = 'about'
    path = 'about'
    template = 'about'
    login_required = False

    def get(self, request):
        return self.render(request)


REGISTERED_VIEWS = [Home, About]
