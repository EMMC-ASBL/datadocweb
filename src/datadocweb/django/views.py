
""" Defines the RaufossDB Django App views """

from pathlib import Path
from tempfile import TemporaryDirectory
from datadocweb.django.appview import AppView
from datadocweb.datadoc import DataDoc


class Home(AppView):

    app = 'DataDocWeb'
    name = 'home'
    path = ''
    template = 'datadocweb-home'
    login_required = True
    roles_required = {
        'get': 'datadocweb-find | datadocweb-register'
    }

    def get(self, request):
        """ Render the home page (with search function) """
        return self.render(request)


class RegisterData(AppView):

    app = 'DataDocWeb'
    name = 'register'
    path = 'register'
    template = 'datadocweb-register'
    login_required = True
    roles_required = {
        'get': 'datadocweb-register',
        'post': 'datadocweb-register',
        'delete': 'datadocweb-register'
    }

    def get(self, request):
        """ Render the form to register data """
        return self.render(request)

    def post(self, request):
        """ Post the form data and add the data in the triple store """
        with TemporaryDirectory(prefix='datadocweb') as workdir:
            wd = Path(workdir)
            files = {}
            for key in request.FILES:
                files[key] = []
                for item in request.FILES.getlist(key):
                    filename = wd / item.name
                    with filename.open('wb+') as dst:
                        for chunk in item.chunks():
                            dst.write(chunk)
                    files[key].append(filename)
            data = DataDoc()
            # data.parse(database)
            # data.add()
        return self.render(request)


REGISTERED_VIEWS = [Home, RegisterData]
