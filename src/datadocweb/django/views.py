
""" Defines the RaufossDB Django App views """

import os
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from django.http import HttpRequest
from datadocweb.django.appview import AppView
from datadocweb.datadoc import DataDoc


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
        print(request.GET)
        if self.query.get_str('fmt') == 'json':
            # search in a graph
            values = self.query.validate('graph query')
            if 'error' in values:
                self.json_error(values['error'], status='error')
            else:
                graph, query = values('graph query')
                backend = 'rdflib'
                graph_file = None
                if graph.endswith('.ttl'):
                    backend = 'rdflib'
                    workdir = Path(gettempdir()) / 'datadocweb'
                    workdir.mkdir(exist_ok=True)
                    graph_file = workdir / f'{uuid4()}.ttl'
                    self.read_bytes(f'graphs/{graph}', graph_file)
                data = DataDoc(backend)
                error = ''
                if graph_file:
                    if graph_file.exists():
                        data.parse(graph_file, fmt='turtle')
                        os.remove(graph_file)
                    else:
                        error = f'graph database not found: "{graph}".'
                if error:
                    self.json_error(error, status='error')
                else:
                    table = data.find(typ=query, fmt='table')
                    result = {'table': table, 'status': 'success'}
                    self.json_data('result', result)
        else:
            # render the home page with search input
            graphs = self.list_blobs('graphs/')
            self['graphs'] = [x[7:] for x in graphs if x.endswith('.ttl')]
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
        graphs = self.list_blobs('graphs/')
        self['graphs'] = [x[7:] for x in graphs if x.endswith('.ttl')]
        return self.render(request)

    def post(self, request: HttpRequest):
        """ Post the form data and add the data in the triple store """
        answer = {'nrow': 0, 'status': ''}
        values = self.query.validate('database filedata prefixes')
        if 'error' in values:
            self.json_error(values['error'], status='error')
        else:
            workdir = Path(gettempdir()) / 'datadocweb'
            workdir.mkdir(exist_ok=True)
            graph: str = values['database']
            filedata = values.load_json('filedata')
            prefixes = values.load_json('prefixes')
            graph_file = None
            if graph.endswith('.ttl'):
                backend = 'rdflib'
                graph_file = workdir / f'{uuid4()}.ttl'
                self.read_bytes(f'graphs/{graph}', graph_file)
            data = DataDoc(backend)
            data.bind(prefixes)
            if graph_file:
                if graph_file.exists():
                    data.parse(graph_file, fmt='turtle')
            columns = [c['name'] for c in filedata['columns']]
            data.add_table(columns, filedata['rows'])
            if graph_file:
                data.dump(graph_file, fmt='turtle')
                self.write_bytes(graph_file, f'graphs/{graph}')
                os.remove(graph_file)
            answer['nrow'] = len(filedata['rows'])
            answer['status'] = 'success'
        return self.json_response(answer)


REGISTERED_VIEWS = [Home, UploadData]
