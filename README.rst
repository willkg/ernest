======
README
======

Summary
=======

This is a project we hacked together.

The code is distributed under XXX. See LICENSE file for more details.


Install and configure
=====================

1. Create a virtual environment.

2. Install the dependencies::

       $ pip install -r requirements.txt

3. Read through the settings in ``ernest/settings_local.py``

   TODO: Document settings that need to be set here.

4. Create the database::

       $ python manage.py db_create

   This creates the database based on the settings in
   ``ernest/settings_local.py``.


Run server
==========

Run::

    $ python manage.py runserver


Run tests
=========

Run::

    $ nosetests


Locations of things
===================

:Project settings: ``ernest/settings.py`` and ``ernest/settings_local.py-dist``
:View code:        ``ernest/view.py``
:Database models:  ``ernest/models.py``
:Templates:        ``ernest/templates/``
:Static assets:    ``ernest/static/``
