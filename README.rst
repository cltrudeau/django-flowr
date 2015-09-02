django-flowr
************

Most state machine libraries are "static" and require the flow in the state
machine to be definied programmatically.  Flowr is designed so that you can
build state machine flows and store them in a database.  There are two key
concepts: rule graphs and state machines.  The programmer defines one or more
sets of rules that describe the allowed flow between states, the user can then
use the GUI tools to construct state machines that follow these rules and
store the machines in the database.  The state machines can then be
instantiated for processing the flow which triggers call-back mechanisms in
the rule objects on entering and leaving a state.


Installation
============

Add 'flowr' to your ``settings.INSTALLED_APPS`` field.

Run

.. code-block:: bash

    $ manage.py makemigrations
    $ manage.py migrate


Demo Installation
=================

A full django project is included in the repository that is used for testing
and can give you a quick idea what flowr is about.  The project is available
in ``extras/sample_site``

.. code-block:: bash

    $ cd django-flowr
    $ pip install -r requirements.txt
    $ cd extras/sample_site
    $ pip install -r requirements.txt
    $ ./resetdb.sh
    $ ./runserver.sh

This will create an ``sqlite`` database with some sample rules.  Point your
browser at ``http://localhost:8000/admin`` and login with the username
``admin`` and the password ``admin``.  Use the django admin screens to view
the flows and rules in the system.

Docs
====

Docs available at: http://django-flowr.readthedocs.org/en/latest/
