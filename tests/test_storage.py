
""" Unit tests for the module datadocweb.storage """

import unittest
from pathlib import Path
import environ
from datadocweb.storage import Storage, create_storage


thisdir = Path(__file__).resolve().parent


class StorageUnitTest(unittest.TestCase):

    def test_find_config(self):
        cfg = {
            'ConnectionString': 'hello',
            'LOCATION': 'hello-world',
            'Container': 'container',
            'path': 'my/path',
        }
        storage = Storage(cfg)
        value = storage.find_config('connection_string', 'location')
        self.assertEqual(value, 'hello')
        storage.config.pop('ConnectionString')
        value = storage.find_config('connection_string', 'location')
        self.assertEqual(value, 'hello-world')
        value = storage.find_config('container')
        self.assertEqual(value, 'container')
        value = storage.find_config('path')
        self.assertEqual(value, 'my/path')


class FileStorageTest(unittest.TestCase):

    def test_datadoc(self):
        config = {
            'ENGINE': 'tempfile',
            'PATH': '{tempdir}/datadocweb',
            'DATABASE': 'test-tem.ttl'
        }
        storage = create_storage(config)
        self.assertTrue(storage.path.exists())

        prefix = dict(pm='https://www.ntnu.edu/physmet/data#')
        datadoc = storage.datadoc(prefixes=prefix)
        datadoc.add(thisdir / 'input/tem.csv')
        storage.dump(datadoc)

        outfile = storage.path / 'test-tem.ttl'
        self.assertTrue(outfile.exists())
        table1 = datadoc.find(typ='pm:BrightFieldImage', fmt='table')
        self.assertEqual(len(table1['rows']), 2)

        newdatadoc = storage.datadoc(prefixes=prefix)
        table2 = newdatadoc.find(typ='pm:BrightFieldImage', fmt='table')
        self.assertEqual(len(table2['rows']), 2)

        files = storage.databases()
        self.assertIn('test-tem.ttl', files)


class AzureStorageTest(unittest.TestCase):

    def test_datadoc(self):
        env = environ.Env()
        env.read_env(thisdir / '.env')
        cs = env.str('AZURE_STORAGE', '')
        if cs:
            config = {
                'ENGINE': 'azure.storage.blob',
                'NAME': 'My Blob Storage',
                'CONNECTION_STRING': env('AZURE_STORAGE'),
                'CONTAINER': env('AZURE_STORAGE_CONTAINER'),
                'FOLDER': 'datadocweb-test',
                'DATABASE': 'test-tem.ttl'
            }
            storage = create_storage(config)
            prefix = dict(pm='https://www.ntnu.edu/physmet/data#')
            datadoc = storage.datadoc(prefixes=prefix)
            datadoc.add(thisdir / 'input/tem.csv')
            storage.dump(datadoc)

            files = storage.databases()
            self.assertIn('test-tem.ttl', files)

            table1 = datadoc.find(typ='pm:BrightFieldImage', fmt='table')
            self.assertEqual(len(table1['rows']), 2)

            newdatadoc = storage.datadoc(prefixes=prefix)
            table2 = newdatadoc.find(typ='pm:BrightFieldImage', fmt='table')
            self.assertEqual(len(table2['rows']), 2)

            files = storage.databases()
            self.assertIn('test-tem.ttl', files)


if __name__ == '__main__':
    unittest.main()
