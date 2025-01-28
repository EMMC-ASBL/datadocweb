
""" A subclass of django.views.generic.base.View to manage the login and the
    role-based permisssion.

    https://docs.djangoproject.com/en/5.0/topics/class-based-views/
"""

from typing import List
from pathlib import Path
from uuid import UUID
import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.apps import apps
from django.views import View

from azure.storage.blob import BlobServiceClient


class Validation(dict):

    def __getattr__(self, attr):
        return self.get(attr, '')

    def __call__(self, *keys):
        items = []
        for key in keys:
            if key:
                if isinstance(key, str):
                    items = key.strip().split()
                elif isinstance(key, (list, tuple)):
                    items += [k for k in key if isinstance(k, str)]
        return [self.get(item, '') for item in items]

    def load_json(self, attr, default_value=None):
        value = self.get(attr, None)
        result = default_value
        if value:
            try:
                result = json.loads(value)
            except Exception:
                result = default_value
        return result


class CheckList:

    def __init__(self, parent: 'Query', required: str, optional: str = ''):
        self.parent = parent
        self.names = []
        self.required = []
        self.types = {}
        self.add(required, optional)

    def _split(self, names: str):
        items = []
        if names:
            if isinstance(names, str):
                items = names.strip().split()
            elif isinstance(names, list):
                items += [name for name in names if isinstance(name, str)]
        return items

    def add(self, required: str = '', optional: str = ''):
        items = self._split(required)
        self.names += items
        self.required += items
        items = self._split(optional)
        self.names += items

    def typedef(self, name, typename, min=None, max=None):
        self.types[name] = dict(name=typename, min=min, max=max)

    def convert(self, name):
        error = ''
        value = self.parent.get_str(name)
        if value:
            if name in self.types:
                typ = self.types[name]
                typename = typ['name']
                func = getattr(self.parent.query, f'get_{typename}')
                v = func(value, None)
                if v is None:
                    error = f'is not a "{typename}"'
                    value = None
                else:
                    if typename in ['int', 'float']:
                        mi = typ['min']
                        ma = typ['max']
                        if (mi is not None) & (ma is not None):
                            if (v < mi) | (v > ma):
                                error = f'must be in [{mi},{ma}]'
                        elif mi is not None:
                            if v < mi:
                                error = f'must be greater than {mi}'
                        elif ma is not None:
                            if v > ma:
                                error = f'must be lower than {ma}'
                    value = v
        if error:
            error = f'the value "{value}" for the parameter "{name}" {error}.'
        return value, error

    def validate(self, **extra):
        """ Validate and convert required values """
        errors = []
        empty = []
        values = Validation()
        if extra:
            values.update(extra)
        for name in self.names:
            value = self.parent.get_str(name)
            if name in self.required:
                if not value:
                    empty.append(name)
            values[name] = value
        for name in self.names:
            if name not in empty:
                val, err = self.convert(name)
                if err:
                    if name in self.required:
                        errors.append(err)
                else:
                    values[name] = val
        err = ''
        if empty:
            p = 'properties are' if len(empty) > 1 else 'property is'
            n = ', '.join([c.capitalize() for c in empty])
            errors.append(f'the following {p} required: {n}.')
        if errors:
            values['error'] = '\n'.join(errors)
        return values


class Query:

    def __init__(self):
        self._values = None

    def set_request(self, request: HttpRequest):
        self._values = request.GET
        if request.method == 'POST':
            self._values = request.POST

    def get(self, *keys):
        return [self._values.get(key, '') for key in keys]

    def get_bool(self, key, default_value=False):
        val = str(self.get_str(key))
        return val.lower().strip() in ['yes', 'true', '1', 'on']

    def get_int(self, key, default_value=0):
        val, = self.get(key)
        try:
            v = int(val)
        except Exception:
            v = default_value
        return v

    def get_float(self, key, default_value=0.0):
        val, = self.get(key)
        try:
            v = float(val)
        except Exception:
            v = default_value
        return v

    def get_str(self, key, default_value=''):
        val, = self.get(key)
        return val if val else default_value

    def get_uuid(self, key, default_value=None):
        val, = self.get(key)
        try:
            v = UUID(val)
        except Exception:
            v = default_value
        return v

    def get_list(self, key, dtype=str, delimiter='-'):
        val = self.get_str(key)
        result = []
        if val:
            for item in val.split(delimiter):
                try:
                    v = dtype(item)
                    result.append(v)
                except Exception:
                    pass
        return result

    def check_list(self, required: str, optional: str = ''):
        return CheckList(self, required, optional)

    def validate(self, required: str, optional: str = '', **extra):
        ck = CheckList(self, required, optional)
        return ck.validate(**extra)


class MyJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


class AppView(View):

    name = ''
    path = ''
    template = ''
    login_required = True
    roles_required = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_data = {}
        self.json_keys = []
        self.query = Query()

    def dispatch(self, request, *args, **kwargs):
        """ Dispatch the request HTTP method to the view class method """
        self.context_data = {}
        self['viewname'] = self.name
        info = []
        for app in apps.get_app_configs():
            if getattr(app, 'physmet', False):
                info.append({'name': app.label, 'label': app.verbose_name})
        self['apps'] = info
        app = getattr(self, 'app', None)
        if app:
            self['menu_app_active'] = 'active'
            self['menu_app_text'] = app
        else:
            self[f'menu_{self.name}_active'] = 'active'
        self['user'] = dict(name='anonymous', email='')
        template = ''
        if self.login_required:
            authenticated = False
            if hasattr(settings, 'MS_IDENTITY_WEB'):
                ctx = getattr(request, 'identity_context_data', None)
                if ctx is not None:
                    authenticated = ctx.authenticated
                    self.update_userinfo(ctx)
                if not authenticated:
                    template = 'index'
                elif self.roles_required:
                    method = request.method.lower()
                    http_method_allowed = hasattr(self, method)
                    if http_method_allowed:
                        rr = self.roles_required.get(method, '')
                        if rr:
                            perm = self.has_perm(rr)
                            if not perm:
                                template = 'unauthorized'
                                self['reason'] = f'expected roles: {rr}'
                        else:
                            msg = f'no role defined for HTTP method "{method}"'
                            raise ValueError(msg)
            elif settings.DEBUG:
                authenticated = True
                template = ''
        if template:
            return render(request, f'{template}.html', self.context_data)
        else:
            self.request = request
            self.query.set_request(request)
            return super().dispatch(request, *args, **kwargs)

    def __getitem__(self, name):
        """ Get context data """
        return self.context_data[name]

    def __setitem__(self, name, value):
        """ Set context data """
        self.context_data[name] = value

    def json_dump(self, key, data):
        """ Set context data as JSON string """
        self.context_data[key] = json.dumps(data)

    def update_context(self, **kwargs):
        """ Update context data """
        for key, val in kwargs.items():
            self.context_data[key] = val

    def update_userinfo(self, identity_context_data):
        """ Update the user info from the identity context data """
        claims = identity_context_data._id_token_claims
        usr = self.context_data['user']
        # update name
        usr['name'] = claims.get('name', '')
        # update email
        usr['email'] = claims.get('email', '').lower()
        if not usr['email']:
            pu = claims.get('preferred_username', '')
            if '@' in pu:
                usr['email'] = pu.lower()
        # update roles
        roles = sorted(claims.get('roles', []))
        usr['roles'] = roles
        usr['roles_str'] = 'no role'
        if len(roles) == 1:
            usr['roles_str'] = f'App role: {roles[0]}'
        elif len(roles) > 1:
            usr['roles_str'] = f'App roles: {", ".join(roles)}'

    def has_perm(self, roles_required: str):
        """ Evaluate if the user has the permission (role based permission) """
        perm = False
        if roles_required:
            user_roles = self.context_data['user']['roles']
            values = {}
            name = ''
            for c in roles_required:
                if c in ' &|()':
                    if name:
                        values[name] = name in user_roles
                    name = ''
                else:
                    name += c
            if name:
                values[name] = name in user_roles
            expr = str(roles_required)
            for key, val in values.items():
                expr = expr.replace(key, str(val))
            try:
                perm = eval(expr, {}, {})
            except Exception:
                perm = False
        return perm

    def render(self, request):
        json_response = self.query.get_str('fmt') == 'json'
        if json_response:
            return self.json_response()
        else:
            return render(request, f'{self.template}.html', self.context_data)

    def json_response(self, data=None, json_dumps_params=None):
        if data is None:
            if len(self.json_keys) > 1:
                data = {k: self.context_data[k] for k in self.json_keys}
            else:
                data = self.context_data[self.json_keys[0]]
        if json_dumps_params is None:
            indent = self.query.get_int('indent')
            if indent > 0:
                json_dumps_params = dict(indent=indent)
        return JsonResponse(
            data=data,
            encoder=MyJsonEncoder,
            json_dumps_params=json_dumps_params
        )

    def json_data(self, key, value=None, **kwargs):
        """ Add data that will be sent in the JsonResponse """
        if key not in self.json_keys:
            self.json_keys.append(key)
        if value is not None:
            self[key] = value
        else:
            self[key] = kwargs

    def json_error(self, message, **kwargs):
        """ Set an error message that will be sent in the JsonResponse """
        self.json_keys = ['error']
        err = {'error': message}
        err.update(kwargs)
        self['error'] = err

    def _get_azure_container(self):
        cfg = settings.DATABASES['datadocweb']
        conn_str = cfg.get('CONNECTION_STRING', cfg.get('location', ''))
        if conn_str:
            container = cfg.get('CONTAINER', '')
            if not container:
                if isinstance(cfg.get('options', None), dict):
                    container = cfg['options'].get('container', '')
            if container:
                blob = BlobServiceClient.from_connection_string(conn_str)
                return blob.get_container_client(container)
            else:
                raise ValueError('Azure Container not defined.')
        else:
            raise ValueError('Azure Connection String not defined.')

    def read_bytes(self, remotepath: str, localpath: Path = None):
        """ Read a remote file from an Azure Storage """
        cont = self._get_azure_container()
        blob = cont.get_blob_client(remotepath)
        filedata = None
        if blob.exists():
            filedata = blob.download_blob().content_as_bytes()
            if isinstance(localpath, Path):
                localpath.write_bytes(filedata)
        return filedata

    def write_bytes(self, filedata: bytes, remotepath: str):
        """ Write a remote file in an Azure Storage """
        if isinstance(filedata, Path):
            filedata = filedata.read_bytes()
        result = False
        if isinstance(filedata, bytes):
            cont = self._get_azure_container()
            blob = cont.upload_blob(remotepath, filedata, overwrite=True)
            result = blob.exists()
        return result

    def list_blobs(self, prefix: str, fmt: str = 'name') -> List[str]:
        """ List the files in the Azure blob storage

            database: str
                Get the connection string of the database in settings.DATABASE
            prefix: str
                Return all blobs with the given prefix
            fmt: str
                Format of the returned item (comma sperated value):
                name,size,modified,size_str,modified_str
        """
        def sizeof_fmt(num):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if abs(num) < 1024.0:
                    return f'{num:3.1f} {unit}'
                num /= 1024.0
            return f'{num:.1f} PB'

        items = []
        cont = self._get_azure_container()
        if cont is not None:
            if fmt == 'name':
                for blob in cont.list_blobs(name_starts_with=prefix):
                    items.append(blob.name)
            else:
                attr = [x.strip() for x in fmt.split(',')]
                for blob in cont.list_blobs(name_starts_with=prefix):
                    item = dict(
                        name=blob.name,
                        size=blob.size,
                        size_str=sizeof_fmt(blob.size),
                        modified=blob.last_modified,
                        modified_str=str(blob.last_modified)[0: 16]
                    )
                    items.append({k: item[k] for k in attr if k in item})
        return items
