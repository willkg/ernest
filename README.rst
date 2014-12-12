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

3. (optional) ``npm install`` if you want to run the JS tests.

4. ``cp ernest/settings_local.py-dist ernest/settings_local.py``

5. Edit ``ernest/settings_local.py``.

   You can see which settings are editable/overrideable in
   ``ernest/settings.py``.

   Note: You **MUST** provide a SECRET_KEY either in
   ``settings_local.py`` or in the environment.  No secret key--no
   soup!

6. Create the database and give it the alembic stamp::

       $ python manage.py db_create

   This creates the database based on the settings in
   ``ernest/settings_local.py``.


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

Run the python tests with::

    $ nosetests

Run the clientside tests with::

    $ karma start karma.conf.js --single-run


Manage db and migrations
========================

To generate the tables for your db, do::

    $ python manage.py db_create

Note: If you run this command twice, it shouldn't wipe your data.

To update your db by applying all unapplied migrations, do::

    $ alembic upgrade head

To create a new migration make the model changes you need
to make and then, do::

    $ alembic revision -m "some message" --autogenerate

See: https://alembic.readthedocs.org/en/latest/tutorial.html#auto-generating-migrations

You can see the current migration with::

    $ alembic current


Setup on Heroku
===============

Create the app:

    ::

        # Log in if you haven't already
        $ heroku login

        # Use the buchner buildpack
        $ heroku create --stack cedar --buildpack \
            git://github.com/rehandalal/heroku-buildpack-python.git

        # Push the repository
        $ git push heroku master

    More details on `Buchner build pack here
    <https://github.com/rehandalal/heroku-buildpack-buchner>`_.

Create the db:

    ::

        $ heroku config | grep POSTGRESQL

        # Heroku creates a color db and tells you the variable.
        $ heroku pg:promote <COLOR VAR FROM PREVIOUS OUTPUT>

        # Create db
        $ heroku run "python manage.py db_create"

    More details on `Postgres on Heroku here
    <https://devcenter.heroku.com/articles/heroku-postgresql>`_.

Create a dyno and make sure it's working:

    ::

        # Create a dyno
        $ heroku ps:scale web=1

        # Make sure it's working
        $ heroku ps

        # Open in your browser
        $ heroku open


Helpful documentation
=====================

* Bugzilla API: https://wiki.mozilla.org/Bugzilla:REST_API
* Flask: http://flask.pocoo.org/docs/
* Bootstrap: http://getbootstrap.com/2.3.2/index.html
* jQuery: http://api.jquery.com/
* SQLAlchemy: http://www.sqlalchemy.org/
* Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/index.html
* Alembic: https://alembic.readthedocs.org/en/latest/index.html
* Angular: http://angularjs.org/


Locations of things
===================

Project settings:
    ``ernest/settings.py`` and ``ernest/settings_local.py-dist``

API View code:
    ``ernest/main.py``

Database models:
    ``ernest/models.py``

Templates:
    ``ernest/templates/``

Static assets:
    ``ernest/static/``
