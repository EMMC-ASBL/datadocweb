
""" Defines the RaufossDB Django App views """

import os
from pathlib import Path
from tempfile import TemporaryDirectory
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
        if self.query.get_str('fmt') == 'json':
            # search in a graph
            graph, query, typ = self.query.get('g', 'q', 't')
            backend = 'rdflib'
            parse = None
            if graph.endswith('.ttl'):
                backend = 'rdflib'
                parse = self.read_bytes(graph)
            data = DataDoc(backend)
            if parse:
                data.parse(parse, fmt='turtle')
            found = data.find(typ=typ, fmt='dict')
            self.json_data('result', {'items': found})
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
            with TemporaryDirectory(prefix='datadocweb') as workdir:
                wd = Path(workdir)
                graph: str = values['database']
                filedata = values.load_json('filedata')
                prefixes = values.load_json('prefixes')
                graph_file = None
                if graph.endswith('.ttl'):
                    backend = 'rdflib'
                    graph_file = wd / f'{uuid4()}.ttl'
                    self.read_bytes(f'graphs/{graph}', graph_file)
                data = DataDoc(backend)
                if graph_file:
                    if graph_file.exists():
                        data.parse(graph_file, fmt='turtle')
                columns = [c['name'] for c in filedata['columns']]
                data.add_table(filedata['rows'], columns, prefixes)
                if graph_file:
                    data.dump(graph_file, fmt='turtle')
                    self.write_bytes(graph_file, f'graphs/{graph}')
                    os.remove(graph_file)
                answer['nrow'] = len(filedata['rows'])
                answer['status'] = 'success'
        return self.json_response(answer)


REGISTERED_VIEWS = [Home, UploadData]
