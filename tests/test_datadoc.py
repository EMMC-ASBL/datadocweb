"""
    Unit Tests on the DataDoc class
"""

import unittest
from pathlib import Path
from datadocweb.datadoc import DataDoc


thisdir = Path(__file__).resolve().parent
# storage_info = read_dotenv(thisdir / '.env', 'RAUFOSS_MONGODB')


class DataDocUnitTest(unittest.TestCase):

    def test_add(self):
        """ Test the add method of the DataDoc class """
        inpdir = thisdir / 'input'
        outdir = thisdir / 'output'
        outdir.mkdir(exist_ok=True)

        datadoc = DataDoc()
        datadoc.bind(['pm=https://www.ntnu.edu/physmet/data#'])
        kb = outdir / 'kb.ttl'
        if kb.exists():
            datadoc.parse(kb)
        # datadoc.add(inpdir / 'tem.csv')
        # datadoc.dump(kb)
        # found = datadoc.find(typ='pm:BrightFieldImage')
        # print(found)
        data = datadoc.fetch('pm:TEM_BF_lowmag', outdir / 'TEM_BF_lowmag.png')
        print(data[0:10] if data else 'no data')


if __name__ == '__main__':
    unittest.main()
