
""" Defines the views for the Django App """

from django.http import HttpRequest
from datadocweb.django.appview import AppView


class Home(AppView):

    app = 'DataDocWeb'
    name = 'home'
    path = ''
    template = 'datadocweb-home'
    login_required = True
    roles_required = {
        'get': 'datadocweb-search | datadocweb-upload'
    }

    def get(self, request: HttpRequest):
        """ Render the home page (with search function) """
        storage = self.get_triplestore()
        if self.query.get_str('fmt') == 'json':
            # search in a graph
            values = self.query.validate('graph query')
            if 'error' in values:
                self.json_error(values['error'], status='error')
            else:
                graph, query = values('graph query')
                try:
                    datadoc = storage.datadoc(graph)
                    table = datadoc.find(typ=query, fmt='table')
                    result = {'table': table, 'status': 'success'}
                    self.json_data('result', result)
                except Exception as err:
                    self.json_error(str(err), status='error')
        else:
            # render the home page with search input
            self['storage'] = storage.name
            self['graphs'] = storage.databases()
        return self.render(request)


class UploadData(AppView):

    app = 'DataDocWeb'
    name = 'upload'
    path = 'upload'
    template = 'datadocweb-upload'
    login_required = True
    roles_required = {
        'get': 'datadocweb-upload',
        'post': 'datadocweb-upload',
        'delete': 'datadocweb-upload'
    }

    def get(self, request: HttpRequest):
        """ Render the form to upload data / files """
        storage = self.get_triplestore()
        self['storage'] = storage.name
        self['graphs'] = storage.databases()
        return self.render(request)

    def post(self, request: HttpRequest):
        """ Post the form data and add the data in the triple store """
        storage = self.get_triplestore()
        answer = {'nrow': 0, 'status': ''}
        values = self.query.validate('database filedata prefixes')
        if 'error' in values:
            self.json_error(values['error'], status='error')
        else:
            graph: str = values['database']
            filedata = values.load_json('filedata')
            prefixes = values.load_json('prefixes')
            if prefixes:
                p = {}
                for pr, ns in prefixes.items():
                    p[pr.strip()] = ns.strip('"\'')
                prefixes = p
            datadoc = storage.datadoc(graph, prefixes)
            columns = [c['name'] for c in filedata['columns']]
            datadoc.add_table(columns, filedata['rows'])
            storage.dump(datadoc, graph)
            answer['nrow'] = len(filedata['rows'])
            answer['status'] = 'success'
        return self.json_response(answer)


REGISTERED_VIEWS = [Home, UploadData]
