======
README
======

Summary
=======

I'm always frank and earnest with bugs. Uh, in GitHub I'm Frank, and
Bugzilla I'm Ernest.

Ernest is a Bugzilla dashboard.

The code is distributed under MPL-v2. See LICENSE file for more details.


**October 2nd, 2013 status**

This is pretty hard-coded for SUMO as we fiddle with it and get it to
our liking. Then maybe I'll work on generalizing it. If you're
interested in working on it, that's totally cool---just let us know.


Install and configure
=====================

1. Create a virtual environment.

2. ``pip install -r requirements.txt``

3. ``cp ernest/setting_local.py-dist ernest/settings_local.py``

4. Edit ``ernest/settings_local.py``.

   You can see which settings are editable/overrideable in
   ``ernest/settings.py``.

5. Create the database and give it the alembic stamp::

       $ python manage.py db_create

   This creates the database based on the settings in
   ``ernest/settings_local.py``.

6. Install and run memcached.


Create projects and sprints
===========================

To create a project::

    $ python manage.py create_project <projectname>

To create a sprint for that project::

    $ python manage.py create_sprint <projectname> <sprintname>


Run server
==========

Run::

    $ python manage.py runserver


Run tests
=========

Run tests with::

    $ nosetests


Helpful documentation
=====================

* Bugzilla API: https://wiki.mozilla.org/Bugzilla:REST_API
* Flask: http://flask.pocoo.org/docs/
* Bootstrap: http://getbootstrap.com/2.3.2/index.html
* jQuery: http://api.jquery.com/
* SQLAlchemy: http://www.sqlalchemy.org/
* Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/index.html
* Alembic: https://alembic.readthedocs.org/en/latest/index.html


Locations of things
===================

Project settings:
    ``ernest/settings.py`` and ``ernest/settings_local.py-dist``

View code:
    ``ernest/main.py``

Database models:
    ``ernest/models.py``

Templates:
    ``ernest/templates/``

Static assets:
    ``ernest/static/``
