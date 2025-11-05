
""" Generate random data tables """

from pathlib import Path
try:
    from .datatable_storage import DataTableStorage
except Exception:
    from datatable_storage import DataTableStorage


class Generator:

    def __init__(self, storage: DataTableStorage):
        self.storage = storage

    def register_schema_alloys(self):
        storage = self.storage
        res = storage.post_schema('example-alloys', 'Heat Treatment of Alloys')
        tables = storage.post_tables(res.uid, dict(
            alloy='Alloy composition',
            treatment='Heat treatment',
            tests='Mechanical tests'
        ))
        storage.post_columns(res.uid, tables[0].uid, dict(
            name='str', Mn='float', Fe='float'
        ))
        storage.post_columns(res.uid, tables[1].uid, dict(
            name='str', cooling='str', temperature='float'
        ))
        storage.post_columns(res.uid, tables[2].uid, dict(
            alloy='alloy.name',
            treatment='treatment.name',
            test_type='choice',
            result='filepath'
        ))

    def generate_examples(self):
        """ Generate examples of schema and tables """
        schemas = [s.name for s in self.storage.get_list('schema')]
        name = 'example-alloys'
        if name not in schemas:
            self.register_schema_alloys()
        uid = ''
        for s in self.storage.get_list('schema'):
            if s.name == name:
                uid = s.uid
        print(uid)
        res = self.storage.post({
            'category': 'datatable',
            'title': 'Example 1',
            'schema': uid
        })
        alloys = ['AA6005.63', 'AA7046.63', 'AA7046.42', 'AA6082.60']
        methods = [f'Method {i+1}' for i in range(5)]
        cooling = ['Cold water quench', 'Air cooling']
        test_type = ['Tensile test', 'Plate bending test', 'Component test']
        choices = {
            'name': alloys,
            'alloy': alloys,
            'treatment': methods,
            'Mn': (0.1, 0.5),
            'Fe': (0.1, 0.5),
            'temperature': (140, 220),
            'cooling': cooling,
            'test_type': test_type
        }
        res.datatable['alloy'].generate(4, choices)
        for i, row in enumerate(res.datatable['alloy'].rows):
            row['name'] = alloys[i]

        choices['name'] = methods
        res.datatable['treatment'].generate(5, choices)
        for i, row in enumerate(res.datatable['treatment'].rows):
            row['name'] = methods[i]

        res.datatable['tests'].generate(15, choices)
        print(res.datatable['alloy'])

        storage._store_result(res)


if __name__ == '__main__':

    thisdir = Path(__file__).resolve().parent
    datadir = thisdir / 'tests/storage'
    datadir.mkdir(exist_ok=True)

    storage = DataTableStorage.from_config({
        'backend': 'json',
        'workdir': datadir
    })

    gen = Generator(storage)
    gen.generate_examples()

    # schema = Schema(name='alloys', title='Heat Treatment of Alloys')
    # schema.add(
    #     name='alloy',
    #     title='Alloy composition',
    #     columns=dict(name='str', Mn='float', Fe='float')
    # )
    # schema.add(
    #     name='treatment',
    #     title='Heat treatment',
    #     columns=dict(name='str', cooling='str', temperature='float')
    # )
    # schema.add(
    #     name='tests',
    #     title='Mechanical tests',
    #     columns=dict(
    #         alloy='alloy.name',
    #         treatment='treatment.name',
    #         test_type='choice',
    #         result='filepath'
    #     )
    # )
    # schema['tests'].add_choices(
    #     column='test_type',
    #     choices={
    #         'tensile': 'Tensile test',
    #         'bending': 'Plate bending test',
    #         'component': 'Component test'
    #     }
    # )
    # print(schema.to_string())
    # tables = DataTables(schema)

    # alloy = tables['alloy']
    # alloy.add_row(name='AA6005.63', Mn=0.047, Fe=0.198)
    # alloy.add_row(name='AA7046.63', Mn=0.531, Fe=0.218)
    # alloy.add_row(name='AA7046.42', Mn=0.147, Fe=0.398)
    # alloy.add_row(name='AA6082.60', Mn=0.007, Fe=0.144)

    # treat = tables['treatment']
    # treat.add_row('Method 1', 'Cold water quench', 150)
    # treat.add_row('Method 2', 'Cold water quench', 180)
    # treat.add_row('Method 3', 'Air cooling', 150)

    # tests = tables['tests']
    # tests.add_row('AA6005.63', 'Method 2', 'Tensile test', 'file1.csv')
    # tests.add_row('AA6005.63', 'Method 2', 'Bending test', 'file2.csv')
    # tests.add_row('AA6005.63', 'Method 3', 'Component test', 'file5.csv')

    # tables.update_choices()

    # print(tests)

    # print(tables.schema.to_string('choice'))
