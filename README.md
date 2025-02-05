Data Documentation Web Tools
============================

`datadocweb` is graphical user web interface (and in the future a web API will
be available) for data documentation using [tripper](https://github.com/EMMC-ASBL/tripper/).

The web GUI is developed with the [Django](https://www.djangoproject.com/)
framework, this repository contains only a Django App, to run and test the GUI
you need to include this app in your Django project. You can read more details
on the Django Project and Apps, for example [How to create an app in
Django](https://www.geeksforgeeks.org/how-to-create-an-app-in-django/) or in
the [Django Documentation](https://docs.djangoproject.com/en/5.1/).

Installation
------------

Clone the repository [datadocweb](https://gitlab.sintef.no/sfi-physmet/datadocweb) and install the Python package.
git@gitlab.sintef.no:sfi-physmet/datadoc.git

On Windows, with Python 3.11 (replace 3.11 by the version of your Python):

```sh
git clone git@gitlab.sintef.no:sfi-physmet/datadocweb.git
cd datadocweb
# create and activate a new Python virtual environment
py -3.11 -m pip install pipenv
py -3.11 -m pipenv shell
# upgrade pip in the virtual environment
python -m pip install --upgrade pip
# install in the virtual environment the required Python packages
pip install -r requirements.txt
# install the package "datadocweb" in "editable" mode (for development)
pip install --editable .
```

On Linux:

```sh
git clone git@gitlab.sintef.no:sfi-physmet/datadocweb.git
cd datadocweb
# create and activate a new Python virtual environment
python3 -m pip install --user pipenv
python3 -m pipenv shell
# upgrade pip in the virtual environment
python -m pip install --upgrade pip
# install in the virtual environment the required Python packages
pip install -r requirements.txt
# install the package "datadocweb" in "editable" mode (for development)
pip install --editable .
```

If your are using Visual Studio Code, press F1 then search and select the
command "Python: Select Interpreter", and then select, in the dropdown list,
the virtual environment name which starts with "datadocweb-".

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

Some examples of graphical user interface from various knowledge graph tools:

 - https://triplydb.com/academy/iris/
 - https://graphdb.ontotext.com/documentation/10.0/loading-data-using-the-workbench.html
 - https://json-ld.org/playground/
 - https://www.wikidata.org/wiki/Wikidata:Query_Builder
 - https://query.wikidata.org/querybuilder/?uselang=en
