
""" Define the class DataDoc that implement the methods from the module
    tripper.datadoc.clitool:

    - add triples in the triple store from yaml or csv files
    - find/search in the triples store
    - fetch a file

"""

from typing import List, Optional, Sequence, Union
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname
import requests
from io import StringIO
import json
from tripper import Triplestore, DCAT
from tripper.datadoc.dataset import get
from tripper.datadoc import (
    TableDoc,
    get_jsonld_context,
    load_dict,
    save_datadoc,
    save_dict,
    search_iris,
)


def load_dataset(
    ts: Triplestore,
    iri: str,
    distributions: Optional[Union[str, Sequence[str]]] = None,
    use_sparql: Optional[bool] = None,
) -> bytes:
    """Load dataset with given IRI from its source.

    Arguments:
        ts: Triplestore documenting the data to load.
        iri: IRI of the data to load.
        distributions: Name or sequence of names of distribution(s) to
            try in case the dataset has multiple distributions.  The
            default is to try all documented distributions.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.

    Returns:
        Bytes object with the underlying data.

    Note:
        For now this requires DLite.
    """
    dct = load_dict(ts, iri=iri, use_sparql=use_sparql)
    if DCAT.Dataset not in get(dct, "@type"):
        raise TypeError(
            f"expected IRI '{iri}' to be a dataset, but got: "
            f"{', '.join(get(dct, '@type'))}"
        )

    if distributions is None:
        distributions = get(dct, "distribution")

    data = []
    for dist in distributions:
        url = dist.get("downloadURL", dist.get("accessURL"))  # type: ignore
        if url:
            p = urlparse(url)
            if p.scheme.startswith('http'):
                response = requests.get(url)
                if response.ok:
                    data.append(response.content)
            elif p.scheme == 'file':
                path = Path(url2pathname(p.path))
                if path.exists():
                    data.append(path.read_bytes())
    if len(data) == 1:
        return data[0]
    elif len(data) > 1:
        return data
    else:
        raise IOError(f"Cannot access dataset: {iri}")


class DataDoc:

    """
        Methods to init a triple store, add triples from yaml or csv in the
        store, find triple from the store and fetch file from IRI.
    """

    def __init__(self, **kwargs):
        """ Init a DataDoc object the kwargs can contains:
            - backend: str, default backend="rdflib"
            - base_iri: str
            - update_iri: str
            - database: str,
            - username: str,
            - password: str
        """
        backend = kwargs.get('backend', '')
        if not backend:
            kwargs['backend'] = 'rdflib'
        self.store = Triplestore(**kwargs)

    def bind(self, prefix: List[str] = None, **kwargs):
        """ Bind a list of prefix to the triple store """
        for pr, ns in kwargs.items():
            self.store.bind(pr, ns)
        if isinstance(prefix, dict):
            for pr, ns in prefix.items():
                self.store.bind(pr, ns)
        elif isinstance(prefix, list):
            for item in prefix:
                if isinstance(item, tuple):
                    if len(item) == 2:
                        self.store.bind(item[0], item[1])
                elif isinstance(item, str):
                    pr, ns = item.split('=', 1)
                    self.store.bind(pr, ns)

    def parse(self, src: Path, fmt: str = None):
        """ Parse an existing graph and add it to the triple store """
        self.store.parse(src, fmt)

    def dump(self, dst: Path, fmt: str = 'turtle'):
        """ Dump the store to file """
        self.store.serialize(dst, fmt)

    def add(self, inp: Path, fmt: str = None, csv_options: List[str] = None,
            context: str = None):
        """ Add triples from csv or yml files """
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

    def add_table(self, columns, rows):
        """ Add triples from a table """
        table = TableDoc(columns, rows)
        table.save(self.store)

    def find(self,
             criteria: List[str] = None,
             typ: str = None,
             fmt: str = None,
             output: Path = None):
        """ Find triples from the store """
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
            criterias=criterias
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
        elif fmt == "dict":
            ts = self.store
            s = [load_dict(ts, iri) for iri in iris]
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
        elif fmt == "table":
            dicts = [load_dict(self.store, iri) for iri in iris]
            td = TableDoc.fromdicts(dicts)
            s = {
                'columns': td.header,
                'rows': td.data,
                'prefix': {k: f'{v}' for k, v in self.store.namespaces.items()}
            }
        else:
            raise ValueError(f"Unknown format: {fmt}")

        if output:
            with open(output, "wt", encoding="utf-8") as f:
                f.write(s + os.linesep)
        return s

    def fetch(self, iri: str, output: Path = None):
        """ Find the file URL from an IRI, then download and returns the
            content of the file.
        """
        data = load_dataset(self.store, iri)
        if isinstance(data, bytes) & isinstance(output, Path):
            output.write_bytes(data)
        return data
