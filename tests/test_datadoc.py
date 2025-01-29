"""
    Unit Tests on the DataDoc class
"""

import unittest
from pathlib import Path
import json
from datadocweb.datadoc import DataDoc


thisdir = Path(__file__).resolve().parent


class DataDocUnitTest(unittest.TestCase):

    def test_add(self):
        """ Test the methods "add" and "add_table" of the DataDoc class """
        inpdir = thisdir / 'input'
        outdir = thisdir / 'output'
        outdir.mkdir(exist_ok=True)

        prefix = dict(pm='https://www.ntnu.edu/physmet/data#')

        d1 = DataDoc()
        d1.bind(prefix)
        d1.add(inpdir / 'tem.csv')
        d1.dump(outdir / 'kb-csv.ttl')

        fil = inpdir / 'tem.json'
        filedata = json.loads(fil.read_text())
        columns = [c['name'] for c in filedata['columns']]
        d2 = DataDoc()
        d2.bind(prefix)
        d2.add_table(columns, filedata['rows'])
        d2.dump(outdir / 'kb-json.ttl')

        f1 = outdir / 'kb-csv.ttl'
        f2 = outdir / 'kb-json.ttl'
        self.assertTrue(f1.exists())
        self.assertTrue(f2.exists())
        self.assertTrue(f1.read_text(), f2.read_text())

    def test_find(self):
        """ Test the method "find" of the DataDoc class """
        d = DataDoc()
        kb = thisdir / 'input/kb-csv.ttl'
        if kb.exists():
            d.parse(kb)
        else:
            prefix = dict(pm='https://www.ntnu.edu/physmet/data#')
            d.bind(prefix)
            d.add(thisdir / 'input/tem.csv')
            d.dump(kb)
        table = d.find(typ='pm:BrightFieldImage', fmt='table')
        self.assertEqual(len(table['rows']), 2)
        names = [row[0].split('#')[1] for row in table['rows']]
        self.assertEqual(sorted(names), ['TEM_BF', 'TEM_BF_lowmag'])
        # data = d.fetch('pm:TEM_BF_lowmag', outdir / 'TEM_BF_lowmag.png')
        # print(data[0:10] if data else 'no data')


if __name__ == '__main__':
    unittest.main()
