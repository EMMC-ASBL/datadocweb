
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import os
import json

try:
    from .datatable_schema import Schema
    from .datatable import DataTables
except Exception:
    from datatable_schema import Schema
    from datatable import DataTables


@dataclass
class Result:

    category: str = ''
    uid: str = ''
    name: str = ''
    title: str = ''
    status: str = ''
    message: str = ''
    data: Dict[str, Any] = None

    def exists(self):
        return (self.status != 'error') and self.uid and self.category

    def update_data(self, **kwargs):
        if self.data is None:
            self.data = {}
        self.data.update(**kwargs)

    def error(self, message: str):
        self.status = 'error'
        self.message = message

    def to_dict(self, with_data=True):
        data = asdict(self)
        if not with_data:
            data.pop('data')
        return data


class DataTableStorage:

    def __init__(self, connection_string: str):
        """ Init storage """
        self.conn_str = connection_string

    def get_list(self, category: str) -> List[Result]:
        """ Returns a list of schema or datatable """
        return []

    def get(self, category: str, uid: str) -> Result:
        """ Read a schema or datatable """
        pass

    def post(self, data: dict) -> Result:
        """ Create or update a schema or datatable """
        pass

    def post_schema(self, name: str, title: str = '') -> Result:
        data = dict(category='schema', name=name, title=title)
        return self.post(data)

    def post_tables(self, schema: str, tables: dict) -> List[Result]:
        data = dict(category='table', schema=schema)
        results = []
        for name, title in tables.items():
            data['name'] = name
            data['title'] = title
            results.append(self.post(data))
        return results

    def post_columns(self, schema: str, table: str,
                     columns: dict) -> List[Result]:
        data = dict(category='column', schema=schema, table=table)
        results = []
        for name, dtype in columns.items():
            data['name'] = name
            data['dtype'] = dtype
            results.append(self.post(data))
        return results

    def delete(self, category: str, uid: str) -> Result:
        """ Delete a schema or datatable """
        pass

    def create_schema(self, title: str):
        """ Create a schema in the storage """
        pass

    def create_datatable(self, schema: str):
        """ Create a data table in the storage """
        pass

    def read_schema(self, uid: str):
        """ Read a schema from the storage """
        pass

    def read_datatable(self, uid: str):
        """ Read a data table from the storage """
        pass

    def update_schema(self, schema: str, column: str, prop: str, value: str):
        pass

    def delete_schema(self, schema: str, column: str = ''):
        pass

    def update_datatable(self, table: str, row: str, column: str, value: str):
        pass

    def delete_datatable(self, uid: str, entity_type: str):
        pass

    @staticmethod
    def from_config(config: dict):
        backend = config.get('backend', '')
        if backend == 'json':
            return JsonStorage(config['workdir'])
        else:
            raise ValueError(f'storage not supported "{backend}"')


class JsonStorage(DataTableStorage):

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.workdir = Path(connection_string)

    def _store_result(self, result: Result):
        """ Store a result """
        if result.exists():
            if result.category in ['schema', 'table', 'column']:
                schema: Schema = result.data['schema']
                fil = self.workdir / f'schema/{schema.uid}.json'
                fil.parent.mkdir(exist_ok=True)
                fil.write_text(json.dumps(schema.dump(), indent=2))

            elif result.category in ['datatable', 'row']:
                tables: DataTables = result.data['datatable']
                fil = self.workdir / f'datatable/{tables.uid}.json'
                fil.parent.mkdir(exist_ok=True)
                fil.write_text(json.dumps(tables.dump(), indent=2))

    def _remove_item(self, fil, uid):
        rows = json.loads(fil.read_text())
        item = None
        for row in rows:
            if row['uid'] == uid:
                item = row
                break
        found = item is not None
        if found:
            rows.remove(item)
            fil.write_text(json.dump(rows, indent=2))
        return found

    def get_list(self, category: str):
        """ Returns a list of schema or datatable """
        items = []
        wd = self.workdir / category
        if wd.exists():
            key = 'dtype'
            value = 'schema'
            title_key = 'title'
            if category == 'datatable':
                key = 'row'
                value = 'title'
                title_key = 'value'
            for fil in wd.glob('*.json'):
                data = json.loads(fil.read_text())
                for item in data:
                    if isinstance(item, dict):
                        if item.get(key, '') == value:
                            item = Result(
                                status='loaded',
                                uid=item['uid'],
                                title=item[title_key],
                                name=item.get('name', '')
                            )
                            items.append(item)
                            break
        return items

    def get(self, category: str, uid: str):
        """ Read a schema or datatable """
        res = Result(category=category, uid=uid)
        fil = self.workdir / f'{category}/{uid}.json'
        if fil.exists():
            rows = json.loads(fil.read_text())
            if category == 'schema':
                schema = Schema()
                schema.load(rows)
                res.update_data(schema=schema)
                res.status = 'loaded'
            elif category == 'datatable':
                pass
        else:
            res.error(f'{category} not found "{uid}"')
        return res

    def post(self, data: dict):
        """ Create or update a schema or datatable """
        result = Result(
            category=data.get('category', ''),
            uid=data.get('uid', '')
        )
        if result.uid:
            if result.category in ['schema', 'table', 'column']:
                pass
            result.status = 'updated'
        else:
            result.status = 'created'

            name = data.get('name', '')
            title = data.get('title', '')
            dtype = data.get('dtype', '')
            schema_id = data.get('schema', '')

            if result.category == 'schema':
                schema = Schema(name=name, title=title)
                result.uid = schema.uid
                result.update_data(schema=schema)

            elif result.category == 'table':
                res = self.get('schema', schema_id)
                if res.exists():
                    schema: Schema = res.data['schema']
                    table = schema.add(name, title)
                    result.uid = table.uid
                    result.update_data(schema=schema, table=table)

            elif result.category == 'column':
                res = self.get('schema', schema_id)
                if res.exists():
                    schema: Schema = res.data['schema']
                    result.update_data(schema=schema)
                    table_id = data.get('table', '')
                    if table_id in schema.tables:
                        result.update_data(table=schema.tables[table_id])
                        col = schema.tables[table_id].add(name, title, dtype)
                        result.uid = col.uid
                        result.update_data(column=col)
                    else:
                        result.error(f'table not found {table_id}')

            elif result.category == 'datatable':
                res = self.get('schema', schema_id)
                if res.exists():
                    tables = DataTables(res.data['schema'])
                    result.uid = tables.uid
                    result.update_data(datatable=tables)

        self._store_result(result)
        return result

    def delete(self, category: str, uid: str):
        """ Delete a schema or datatable """
        deleted = False
        fil = self.workdir / f'{category}/{uid}.json'
        if fil.exists():
            if category in ['schema', 'table', 'column']:
                if category == 'schema':
                    os.remove(fil)
                    deleted = True
                else:
                    deleted = self._remove_item(fil, uid)
            elif category in ['datatable', 'row']:
                if category == 'datatable':
                    os.remove(fil)
                    deleted = True
                elif category == 'row':
                    deleted = self._remove_item(fil, uid)
        return deleted

    # def create_schema(self, name: str, title: str = ''):
    #     """ Create a schema in the storage """
    #     schema = Schema(name=name, title=title)
    #     self._write_schema(schema)
    #     return schema

    # def create_table(self, schema: str, name: str, title: str = ''):
    #     """ Create a column in the storage """
    #     s = self.read_schema(schema)
    #     t = s.add(name, title)
    #     self._write_schema(s)
    #     return t

    # def create_column(self, table: str, name: str, dtype: str = 'str',
    #                   title: str = ''):
    #     """ Create a column in the storage """
    #     s: Schema = None
    #     t: Table = None
    #     c: Column = None
    #     if isinstance(table, tuple):
    #         s = self.read_schema(table[0])
    #         t = s.tables[table[1]]
    #     elif hasattr(table, 'schema') & hasattr(table, 'uid'):
    #         s = self.read_schema(table.schema)
    #         t = s.tables[table.uid]
    #     if (s is not None) & (t is not None):
    #         c = t.add(name, title, dtype)
    #         print(s.dump())
    #         self._write_schema(s)
    #     else:
    #         raise KeyError(f'Table not found: "{table}".')
    #     return c

    # def create_datatable(self, schema: str):
    #     """ Create a data table in the storage """
    #     pass

    # def read_schema(self, uid: str):
    #     """ Read a schema from the storage """
    #     fil = self.workdir / f'schemas/{uid}.json'
    #     if fil.exists():
    #         rows = json.loads(fil.read_text())
    #         schema = Schema()
    #         schema.load(rows)
    #         return schema
    #     else:
    #         raise FileNotFoundError(f'Schema not found: "{uid}".')

    # def get_list(self, typ: str = 'schema'):
    #     schemas = []
    #     wd = self.workdir / 'schemas'
    #     if wd.exists():
    #         for fil in wd.glob('*.json'):
    #             data = json.loads(fil.read_text())
    #             for item in data:
    #                 if isinstance(item, dict):
    #                     if item.get('dtype', '') == 'schema':
    #                         s = Schema()
    #                         s.load(item)
    #                         schemas.append(s)
    #                         break
    #     return schemas

    # def read_datatable(self, uid: str):
    #     """ Read a data table from the storage """
    #     pass

    # def update_schema(self, schema: str, uid: str, name: str, value: str):
    #     s = self.read_schema(schema)
    #     if s.update(uid, name, value):
    #         self._write_schema(s)

    # def delete_schema(self, schema: str, uid: str = ''):
    #     if schema:
    #         if uid:
    #             s = self.read_schema(schema)
    #             if s.delete(uid):
    #                 self._write_schema(s)
    #         else:
    #             fil = self.workdir / f'{schema}.json'
    #             if fil.exists():
    #                 os.remove(fil)

    # def update_datatable(self, table: str, row: str, column: str, value: str):
    #     pass

    # def delete_datatable(self, uid: str, entity_type: str):
    #     pass


if __name__ == '__main__':

    thisdir = Path(__file__).resolve().parent
    datadir = thisdir / 'tests/storage'
    datadir.mkdir(exist_ok=True)

    storage = JsonStorage(datadir)
    # s = storage.create_schema('hello_world')
    # t = storage.create_table(s.uid, 'table1')
    # a = storage.create_column(t, 'a', 'str')
    # b = storage.create_column(t, 'b', 'int')
    # s = storage.read_schema(s.uid)
    print(storage.list_schemas())
