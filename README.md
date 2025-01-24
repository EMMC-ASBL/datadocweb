datadoc
=======

Installation
------------

On Windows, with Python 3.11:

```sh
py -3.11 -m pip install pipenv
py -3.11 -m pipenv shell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Tasks to build an web interface for datadoc command
---------------------------------------------------

1. Django project ?
2. Web page to import

    - Select files to import (or drag and drop).-
    - if csv file, create a form to select the delimiter, the header row, and
       the rows to import.
    - if Excel file, create a form to select the worksheet, the header row, and
       the rows to import.
    - if csv or Excel, select the corresponding DCAT name to the header and
      select the column to import.

3. Web page to find

    - Create a form to enter criteria, type.
    - Visualzie the result as a table
    - Click on a link to download a file

External links
--------------

 - https://triplydb.com/academy/iris/
 - https://graphdb.ontotext.com/documentation/10.0/loading-data-using-the-workbench.html
 - https://json-ld.org/playground/
