#!/usr/bin/env python
import os
import subprocess

from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy

from ernest.wsgi import app


manager = Manager(app)


def call_command(cmd, verbose=False):
    if verbose:
        print cmd
    subprocess.call(cmd)


@manager.command
def db_create():
    """Create the database"""
    db = SQLAlchemy(app)
    db.create_all()
    print 'Database created: {0}'.format(app.config.get('SQLALCHEMY_DATABASE_URI'))


if __name__ == '__main__':
    manager.run()
