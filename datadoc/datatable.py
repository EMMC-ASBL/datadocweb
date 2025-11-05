
""" Data Tables """

from typing import List, Dict, Any, Literal
from uuid import uuid4
import random

try:
    from .datatable_schema import Table, Schema, PrettyTable
except Exception:
    from datatable_schema import Table, Schema, PrettyTable


class Row(Dict[str, Any]):

    def __init__(self, other: dict = None):
        super().__init__()
        self['uid'] = f'{uuid4()}'
        if other:
            self.update(other)

    def to_list(self):
        return list(self.values())

    def match(self, **kwargs):
        c = 0
        for key, val in kwargs.items():
            if key in self:
                if isinstance(val, list):
                    if self[key] in val:
                        c += 1
                elif self[key] == val:
                    c += 1
        return c == len(kwargs)


class DataTable:

    def __init__(self, schema: Table):
        self.schema = schema
        self.rows: List[Row] = []

    def _row_index(self, row):
        if isinstance(row, int):
            return row
        elif isinstance(row, str):
            pk = self.schema.primary_key()
            if pk:
                query = {pk: row}
                for i, r in enumerate(self.rows):
                    if r.match(**query):
                        return i
        return -1

    def _col_name(self, col):
        col = self.schema.find(col)
        return '' if col is None else col.name

    def __str__(self):
        return self.to_string()

    def add_row(self, *args, **kwargs):
        n = len(self.rows)
        row = Row(self.schema.default_values(n))
        if kwargs:
            for key, val in kwargs.items():
                if key in row:
                    row[key] = val
        elif args:
            pk = self.schema.primary_key()
            names = [name for name in self.schema.column_names if name != pk]
            for name, value in zip(names, args):
                row[name] = value
        self.rows.append(row)
        return row

    def set_cell(self, row, col, value):
        r = self._row_index(row)
        c = self._col_name(col)
        if (r >= 0) & (len(c) > 0):
            self.rows[r][c] = value

    def get_cell(self, row, col):
        r = self._row_index(row)
        c = self._col_name(col)
        if (r >= 0) & (len(c) > 0):
            return self.rows[r][c]
        return None

    def pretty_table(self, header: Literal['name', 'title'] = 'title'):
        names = ['uid']
        names += [c.name for c in self.schema.columns.values()]
        if header == 'title':
            names = [c.title for c in self.schema.columns.values()]
            names.insert(0, 'Id')
        table = PrettyTable(names)
        table.add_rows([row.to_list() for row in self.rows])
        return table

    def to_string(self, **kwargs):
        header = kwargs.pop('col_header', 'title')
        return self.pretty_table(header).get_string(**kwargs)

    def search(self, **kwargs):
        return [row for row in self.rows if row.match(**kwargs)]

    def drop_rows(self, **kwargs):
        remove = self.search(**kwargs)
        for row in remove:
            self.rows.remove(row)
        return remove

    def generate(self, nrow: int, choices: dict):
        values = {}
        for key, val in choices.items():
            if isinstance(val, list):
                values[key] = random.choices(val, k=nrow)
            elif isinstance(val, tuple):
                a, b = val
                if isinstance(a, float):
                    values[key] = [random.uniform(a, b) for _ in range(nrow)]
                elif isinstance(a, int):
                    values[key] = [random.randint(a, b) for _ in range(nrow)]
        for i in range(nrow):
            row = self.add_row()
            for col in row:
                if col in values:
                    row[col] = values[col][i]


class DataTables(Dict[str, DataTable]):

    def __init__(self, schema: Schema, title: str = ''):
        super().__init__()
        self.schema = schema
        self.uid = f'{uuid4()}'
        self.name = title
        self.title = title
        for table in self.schema.tables.values():
            self[table.name] = DataTable(table)

    def update_choices(self):
        for table in self.schema.tables.values():
            for col in table.columns.values():
                if '.' in col.dtype:
                    t, c = col.dtype.split('.')
                    col.choices = {row['uid']: row[c] for row in self[t].rows}
                print(col)

    def generate(self, nmax: int = 100, choices: dict = None):
        for table in self.values():
            table.generate(random.randint(2, nmax), choices)

    def dump(self):
        data = {
            'schema': self.schema.uid,
            'uid': self.uid,
            'name': self.name,
            'title': self.title,
            'tables': {}
        }
        for name, table in self.items():
            rows = [row.to_list() for row in table.rows]
            data['tables'][name] = rows
        return data

    def load(self, data: dict):
        self.uid = data.get('uid', '')
        self.name = data.get('name', '')
        self.title = data.get('title', '')
        for name, rows in data.get('tables', {}).items():
            for row in rows:
                self[name].add_row(*row)
        return data
