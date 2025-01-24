
""" Try tripper and datadoc """

from typing import List
import os
from pathlib import Path
from io import StringIO
import json
from tripper import Triplestore
from tripper.datadoc import (
    TableDoc,
    get_jsonld_context,
    load,
    load_dict,
    save_datadoc,
    save_dict,
    search_iris,
)


class DataDoc:

    def __init__(self, backend: str = 'rdflib', base_iri: str = None,
                 database: str = None, package: str = None):
        self.store = Triplestore(backend, base_iri, database, package)

    def bind(self, prefix: List[str]):
        for item in prefix:
            if isinstance(item, tuple):
                if len(item) == 2:
                    self.store.bind(item[0], item[1])
            elif isinstance(item, str):
                pr, ns = item.split('=', 1)
                self.store.bind(pr, ns)

    def parse(self, src: Path, fmt: str = None):
        self.store.parse(src, fmt)

    def dump(self, dst: Path, fmt: str = 'turtle'):
        self.store.serialize(dst, fmt)

    def add(self, inp: Path, fmt: str = None, csv_options: List[str] = None,
            context: str = None):
        ts = self.store
        extension = fmt if fmt else inp.suffix
        ext = extension.lower().lstrip(".")
        if ext in ("yml", "yaml"):
            save_datadoc(ts, inp)
        elif ext in ("csv",):
            kw = {}
            if csv_options:
                for token in csv_options:
                    option, value = token.split("=", 1)
                    kw[option] = value
            td = TableDoc.parse_csv(
                inp, context=get_jsonld_context(context), **kw
            )
            td.save(ts)
        else:
            raise ValueError(f"Unknown input format: {fmt}")

    def find(self,
             criteria: List[str] = None,
             typ: str = None,
             fmt: str = None,
             output: Path = None):
        criterias = {}
        contains = {}
        if criteria:
            for crit in criteria:
                if "~=" in crit:
                    key, value = crit.split("~=", 1)
                    contains[key] = value
                else:
                    key, value = crit.split("=", 1)
                    criterias[key] = value

        iris = search_iris(
            ts=self.store,
            type=typ,
            criterias=criterias,
            contains=contains
        )

        # Infer format
        if fmt:
            fmt = fmt.lower()
        elif output:
            fmt = Path(output).suffix.lower().lstrip('.')
        else:
            fmt = 'iris'

        # Create output
        if fmt in ("iris", "txt"):
            s = "\n".join(iris)
        elif fmt == "json":
            ts = self.store
            s = json.dumps([load_dict(ts, iri) for iri in iris], indent=2)
        elif fmt in ("turtle", "ttl"):
            ts2 = Triplestore("rdflib")
            for iri in iris:
                d = load_dict(self.store, iri)
                save_dict(ts2, d)
            s = ts2.serialize()
        elif fmt == "csv":
            dicts = [load_dict(self.store, iri) for iri in iris]
            td = TableDoc.fromdicts(dicts)
            with StringIO() as f:
                td.write_csv(f, prefixes=self.store.namespaces)
                s = f.getvalue()
        else:
            raise ValueError(f"Unknown format: {fmt}")

        if output:
            with open(output, "wt", encoding="utf-8") as f:
                f.write(s + os.linesep)
        return s

    def fetch(self, iri: str, output: Path = None):
        data = load(self.store, iri)
        if output:
            with open(output, "wb") as f:
                f.write(data)
        return data


if __name__ == '__main__':

    thisdir = Path(__file__).resolve().parent
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
    found = datadoc.find(typ='pm:BrightFieldImage')
    print(found)
    data = datadoc.fetch('pm:TEM_BF_lowmag', outdir / 'TEM_BF_lowmag.png')
    print(data[0:10] if data else 'no data')
