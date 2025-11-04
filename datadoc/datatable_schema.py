
""" Define schema for data table """

from typing import Dict, Any, Literal
from dataclasses import dataclass, fields
from uuid import uuid4
import nanoid
from prettytable import PrettyTable


@dataclass
class Model:

    uid: str = ''
    name: str = ''
    title: str = ''
    dtype: str = 'str'

    def __post_init__(self):
        if not self.uid:
            self.uid = f'{uuid4()}'
        if not self.title:
            names = [x.capitalize() for x in self.name.split('_')]
            self.title = ' '.join(names)

    def load(self, other: dict, keymap: dict = None):
        if keymap:
            for key, name in keymap.items():
                if hasattr(self, key):
                    if name in other:
                        setattr(self, key, other[name])
                    elif key in other:
                        setattr(self, key, other[key])
        else:
            for key, val in other.items():
                if hasattr(self, key):
                    setattr(self, key, other[key])

    def dump(self, keymap: dict = None, exclude: list = None):
        if not exclude:
            exclude = []
        dst = {}
        if keymap:
            if isinstance(keymap, dict):
                for key, name in keymap.items():
                    if key not in exclude:
                        dst[name] = getattr(self, key)
        else:
            for field in fields(self):
                if field.name not in exclude:
                    dst[field.name] = getattr(self, field.name)
        return dst


@dataclass
class Column(Model):

    schema: str = ''
    table: str = ''
    default: Any = None
    choices: dict = None
    concept: str = ''

    def __post_init__(self):
        super().__post_init__()
        if self.choices is None:
            self.choices = {}

    def default_value(self, nrow):
        if self.dtype == 'inc':
            return nrow + 1
        elif self.dtype == 'uuid':
            return f'{uuid4()}'
        elif self.dtype.startswith('nanoid'):
            sz = self.dtype.split('-')
            size = int(sz[1]) if len(sz) == 2 else 21
            return f'{nanoid.generate(size=size)}'
        else:
            return self.default

    def add_choice(self, value: str, text: str = ''):
        self.choices[value] = text if text else value

    def add_choices(self, choices: dict):
        self.choices.update(choices)


@dataclass
class Table(Model):

    schema: str = ''
    columns: Dict[str, Column] = None

    def __post_init__(self):
        super().__post_init__()
        self.dtype = 'table'
        if self.columns is None:
            self.columns = {}

    def add(self, name: str, title: str = '', dtype: str = 'str',
            uid: str = ''):
        """ Add a column """
        col = Column(uid=uid, name=name, title=title, dtype=dtype)
        col.schema = self.schema
        col.table = self.uid
        self.columns[col.uid] = col
        return col

    def find(self, column: str):
        """ Find a column by name or title """
        for col in self.columns.values():
            if col.name == column:
                return col
            elif col.title == column:
                return col
            elif col.uid == column:
                return col
        return col

    def dump(self, keymap: dict = None):
        return super().dump(keymap, ['columns'])

    def primary_key(self) -> str:
        pk = set(['inc', 'uuid', 'nanoid'])
        for col in self.columns.values():
            if col.dtype.split('-')[0] in pk:
                return col.name
        return ''

    def default_values(self, nrow):
        return {c.name: c.default_value(nrow) for c in self.columns.values()}

    @property
    def column_names(self):
        return [c.name for c in self.columns.values()]

    def add_choices(self, column: str, choices: dict):
        col = self.find(column)
        if col is not None:
            col.choices.update(choices)


@dataclass
class Schema(Model):

    tables: Dict[str, Table] = None

    def __post_init__(self):
        super().__post_init__()
        self.dtype = 'schema'
        if self.tables is None:
            self.tables = {}

    def __getitem__(self, table: str):
        for tab in self.tables.values():
            if tab.uid == table:
                return tab
            elif tab.name == table:
                return tab
        raise KeyError(f'Table not found "{table}".')

    def add(self, name: str, title: str = '', uid: str = '',
            columns: dict = None):
        """ Add table to the schema """
        tab = Table(uid=uid, name=name, title=title, schema=self.uid)
        if isinstance(columns, dict):
            for key, val in columns.items():
                tab.add(name=key, dtype=val)
        self.tables[tab.uid] = tab
        return tab

    def find(self, uid: str):
        if uid in self.tables:
            return self.tables[uid]
        else:
            for table in self.tables.values():
                if uid in table.columns:
                    return table.columns[uid]

    def update(self, uid: str, name: str, value: str):
        item = self.find(uid)
        if hasattr(item, name):
            setattr(item, name, value)
            return True
        return False

    def delete(self, uid: str):
        item = self.find(uid)
        if isinstance(item, Table):
            self.tables.pop(item.uid)
            return True
        elif isinstance(item, Column):
            self.tables[item.table].columns.pop(item.uid)
            return True
        return False

    def load(self, other: dict, keymap: dict = None):
        """ Load schema from a dict (or a list of dict) """
        if isinstance(other, list):
            for item in other:
                self.load(item)
        elif isinstance(other, dict):
            dtype = other.get('dtype', '')
            if isinstance(keymap, dict):
                if 'dtype' in keymap:
                    dtype = other.get(keymap['dtype'], dtype)
            if dtype == 'schema':
                super().load(other, keymap)
            elif dtype == 'table':
                tab = Table()
                tab.load(other)
                if tab.schema == self.uid:
                    self.tables[tab.uid] = tab
            else:
                col = Column()
                col.load(other)
                if (col.schema == self.uid) & (col.table in self.tables):
                    self.tables[col.table].columns[col.uid] = col

    def dump(self, keymap: dict = None):
        if not keymap:
            keymap = dict(schema={}, table={}, column={})
        data = []
        data.append(super().dump(keymap['schema'], ['tables']))
        for table in self.tables.values():
            data.append(table.dump(keymap['table']))
        for table in self.tables.values():
            for col in table.columns.values():
                data.append(col.dump(keymap['column']))
        return data

    def to_string(self, layout: Literal['table', 'choice'] = 'table'):
        """ Returns a string to displaty the schema """
        tab = PrettyTable()
        if layout == 'table':
            tab.field_names = ['schema', 'table', 'column', 'type', 'concept']
            for table in self.tables.values():
                for col in table.columns.values():
                    tab.add_row([self.name, table.name, col.name, col.dtype,
                                col.concept])

        elif layout == 'choice':
            tab.field_names = ['table', 'column', 'value', 'text']
            for table in self.tables.values():
                for col in table.columns.values():
                    if col.choices:
                        for key, val in col.choices.items():
                            tab.add_row([table.name, col.name, key, val])

        return tab.get_string()

    def column_table(self):
        data = {'class': 'table'}
        data['cols'] = [
            'Table', 'Column', 'Data Type', 'Default', 'Choices', 'Concept'
        ]
        rows = []
        for table in self.tables.values():
            for col in table.columns.values():
                rows.append([table.name, col.name, col.dtype, col.default,
                             len(col.choices), col.concept])
        data['rows'] = rows
        return data
