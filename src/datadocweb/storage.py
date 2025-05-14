
""" Interface for different storage type:
    - FileStorage: each triplestore is a ttl file stored in the temp dir.
    - AzureStorage: each triplestore is a ttl file stored in Azure Storage Blob
    - ServerStorage: triplestore is on a server (backend used is sparqlwrapper)
"""

from typing import List, Dict
import os
import json
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4
from azure.storage.blob import BlobServiceClient
from datadocweb.datadoc import DataDoc


def find_config(values: dict, key: str, default: str = None):
    """ Try to find the value of the given key (lower, upper or camel case).
        For example, if key is equal to "CONFIG_KEY", search for:
        CONFIG_KEY, config_key, ConfigKey
    """
    if isinstance(values, dict):
        if key.find('.') > 0:
            keys = key.split('.')
            parent = values
            for k in keys:
                parent = find_config(parent, k, None)
            return default if parent is None else parent
        else:
            keys = [
                key.lower(),
                key.upper(),
                ''.join([k.capitalize() for k in key.split('_')])
            ]
            for k in keys:
                if k in values:
                    return values[k]
    return default


class Storage:

    engine: str = 'none'

    def __init__(self, config: dict):
        # the parameters of the storage
        self.config = config
        # the storage name / label
        self.name = self.find_config('name')

    def _new_datadoc(self, options: dict, prefixes: dict, parse: Path = None):
        """ Create a new DataDoc instance """
        datadoc = DataDoc(**options)
        if prefixes:
            datadoc.bind(**prefixes)
        if parse:
            if parse.exists():
                datadoc.parse(parse, fmt='turtle')
        return datadoc

    def find_config(self, *keys) -> str:
        """ Find a config value """
        for key in keys:
            val = find_config(self.config, key, None)
            if val is not None:
                return val
        return ''

    def databases(self) -> List[str]:
        """ Returns the list of database/triplestore for this storage """
        return []

    def datadoc(self, database: str = '', prefixes: dict = None) -> DataDoc:
        """ Returns an instance of DataDoc with the right triplestore """
        raise NotImplementedError

    def dump(self, datadoc: DataDoc, database: str = ''):
        """ Dump triplestore in a ttl file, if needed """
        pass


class FileStorage(Storage):

    engine = 'tempfile'

    def __init__(self, config: dict):
        super().__init__(config)
        folder = self.find_config('folder', 'path')
        if not folder:
            msg = 'The folder/path to store the ttl files in the temp '
            msg += 'directory is not defined.'
            raise ValueError(msg)
        if '{tempdir}' in folder:
            folder = folder.format(tempdir=gettempdir())
        self.path = Path(folder)
        self.path.mkdir(parents=True, exist_ok=True)
        self.default_database = self.find_config('database')

    def _filepath(self, database: str = ''):
        """ Returns the localpath of a database/triplestore """
        if not database:
            database = self.default_database
        if not database.endswith('.ttl'):
            database = f'{database}.ttl'
        return self.path / database

    def databases(self):
        """ Returns the list of database/triplestore for this storage """
        return [fil.name for fil in self.path.glob('*.ttl')]

    def datadoc(self, database: str = '', prefixes: dict = None):
        """ Returns an instance of DataDoc with the right triplestore """
        filepath = self._filepath(database)
        return self._new_datadoc({'backend': 'rdflib'}, prefixes, filepath)

    def dump(self, datadoc: DataDoc, database: str = ''):
        """ Dump triplestore in a ttl file, if needed """
        filepath = self._filepath(database)
        datadoc.dump(filepath, fmt='turtle')


class AzureStorage(Storage):

    engine = 'azure.storage.blob'

    def __init__(self, config: dict):
        super().__init__(config)
        self.conn_str = self.find_config('CONNECTION_STRING', 'location')
        if not self.conn_str:
            raise ValueError('Azure Connection String not defined.')
        cont = self.find_config('container', 'options.container')
        self.container = cont
        if not self.container:
            raise ValueError('Azure Container not defined.')
        self.folder = self.find_config('folder')
        if not self.folder:
            msg = 'The folder to store the ttl files in the Azure Container '
            msg += f'{cont} is not defined.'
            raise ValueError(msg)
        if not self.folder.endswith('/'):
            self.folder += '/'
        self.default_database = self.find_config('database')

    def _get_container(self):
        """ Returns the ContainerClient """
        blob = BlobServiceClient.from_connection_string(self.conn_str)
        return blob.get_container_client(self.container)

    def _paths(self, database: str = ''):
        """ Returns the remotepath and localpath of a database/triplestore """
        if not database:
            database = self.default_database
        if not database.endswith('.ttl'):
            database = f'{database}.ttl'
        workdir = Path(gettempdir()) / 'datadocweb'
        workdir.mkdir(exist_ok=True)
        remote = f'{self.folder}{database}'
        local = workdir / f'{uuid4()}.ttl'
        return remote, local

    def read_bytes(self, remotepath: str, localpath: Path = None):
        """ Read a remote file from an Azure Storage """
        cont = self._get_container()
        blob = cont.get_blob_client(remotepath)
        filedata = None
        if blob.exists():
            filedata = blob.download_blob().readall()
            if isinstance(localpath, Path):
                localpath.write_bytes(filedata)
        return filedata

    def write_bytes(self, filedata: bytes, remotepath: str):
        """ Write a remote file in an Azure Storage """
        if isinstance(filedata, Path):
            filedata = filedata.read_bytes()
        result = False
        if isinstance(filedata, bytes):
            cont = self._get_container()
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
        cont = self._get_container()
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

    def databases(self):
        """ Returns the list of database/triplestore for this storage """
        blobs = self.list_blobs(self.folder)
        i = len(self.folder)
        return [name[i:] for name in blobs if name.endswith('.ttl')]

    def datadoc(self, database: str = '', prefixes: dict = None):
        """ Returns an instance of DataDoc with the right triplestore """
        remotepath, localpath = self._paths(database)
        self.read_bytes(remotepath, localpath)
        datadoc = self._new_datadoc({'backend': 'rdflib'}, prefixes, localpath)
        if localpath.exists():
            os.remove(localpath)
        return datadoc

    def dump(self, datadoc: DataDoc, database: str = ''):
        """ Dump triplestore in a ttl file, if needed """
        remotepath, localpath = self._paths(database)
        datadoc.dump(localpath, fmt='turtle')
        self.write_bytes(localpath, remotepath)
        os.remove(localpath)


class ServerStorage(Storage):

    engine = 'sparqlwrapper'

    def __init__(self, config: dict):
        super().__init__(config)
        self.options: Dict[str, str] = {}
        for key in ['base_iri', 'update_iri', 'username', 'password']:
            self.options[key] = self.find_config(key)
        names = self.find_config('databases')
        if isinstance(names, str):
            names = [x.strip() for x in names.split(',')]
        elif isinstance(names, list):
            names = [x.strip() for x in names if isinstance(x, str)]
        else:
            names = []
        self.database_names = names
        self.default_database = names[0] if names else ''
        prefix = self.find_config('prefixes')
        self.prefixes = {}
        if prefix:
            if isinstance(prefix, str):
                self.prefixes = json.loads(prefix)
            elif isinstance(prefix, dict):
                self.prefixes = prefix

    def databases(self):
        """ Returns the list of database/triplestore for this storage """
        return self.database_names

    def datadoc(self, database: str = '', prefixes: dict = None):
        """ Returns an instance of DataDoc with the right triplestore """
        db = database if database else self.default_database
        opt = {'backend': 'sparqlwrapper'}
        for key in ['base_iri', 'update_iri']:
            val = self.options[key]
            opt[key] = val.format(database=db) if '{database}' in val else val
        for key in ['username', 'password']:
            val = self.options[key]
            if val:
                opt[key] = val
        if not isinstance(prefixes, dict):
            prefixes = {}
            if '*' in self.prefixes:
                prefixes.update(self.prefixes['*'])
            if database in self.prefixes:
                prefixes.update(self.prefixes[database])
        return self._new_datadoc(opt, prefixes)


def create_storage(config: dict):
    """ Create a storage from the given config """
    engine = find_config(config, 'engine', '')
    for cls in Storage.__subclasses__():
        if cls.engine == engine:
            return cls(config)
    raise ValueError(f'Storage engine not found: "{engine}"')
