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

In addition, the project uses the following django packages:

- [django-htmx](https://pypi.org/project/django-htmx/)

Run using docker
------------

```
docker-compose -f docker-compose.yml  up -d
```

Installation
------------

Clone the repository [datadocweb](https://github.com/EMMC-ASBL/datadocweb.git)
and install the Python package.

On Windows, with Python 3.11 (replace 3.11 by the version of your Python):

```sh
git clone git@github.com:EMMC-ASBL/datadocweb.git
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
git clone git@github.com:EMMC-ASBL/datadocweb.git
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

Running local GraphDB
----------------------
Run the compose.yml file to get the GraphDB up and running locally at port 7200

New versions:
```
docker compose up -d
```
Old versions:
```
docker-compose -f compose.yml  up -d
```
Go to http://localhost:7200/repository and create a repository named 'matchmaker' .

Also you need to set a licence for the free version to get this working. 

Setting up environment variables
----------------------

Add a .env file to the base directory and if you are using your local graphDB add in the following variables

TRIPLESTORE_BASE_IRI="http://localhost:7200/repositories/matchmaker"
TRIPLESTORE_UPDATE_IRI="http://localhost:7200/repositories/matchmaker/statements"

Testing the Django app
----------------------

A Django project is available to test and develop the Django app. Follow the
steps to run the testing app:

```sh
python manage.py migrate
# run the server
python manage.py runserver
# open in a web browser http://localhost:8000/
```

In the settings.py file, you can define the triple store options
(see the dict DATADOCWEB). A triple store could be: the local 
(or a remote) file system that store triples in one ttl file,
or a triple store could be a online server (the comunication 
with the server will be done by using the library sparqlwrapper).


Running tests for the Django app
----------------------
```sh
 python manage.py test datadoc.tests
 ```

Install the "datadoc" Django App in a Django Project
----------------------------------------------------

1. Install in the Python virtual environment of the Django Project the package
   "datadoc".
2. In your "settings.py", add an item "datadoc" in the INSTALLED_APPS.
3. In your "settings.py", add a dict DATADOCWEB to configure the base
   template and the triplestore (see [core/settings.py](./core/settings.py)).

```sh
cd datadocweb
pip install --editable .
```

Design and Mockups
============================

Available in the docs folder
