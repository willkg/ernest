#!/usr/bin/env python
import subprocess

from flask.ext.script import Manager
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

from ernest.main import app, db, Project, Sprint


manager = Manager(app)


def call_command(cmd, verbose=False):
    if verbose:
        print cmd
    subprocess.call(cmd)


@manager.command
def db_create():
    """Create the tables and do alembic stuff"""
    try:
        db.engine.execute('select * from project')
        print 'Database already exists with tables.'
        return

    except OperationalError:
        # An operational error here means that the "project" table
        # doesn't exist so we should create things!
        pass

    print 'Creating {0}....'.format(
        app.config.get('SQLALCHEMY_DATABASE_URI'))

    db.create_all()

    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option("sqlalchemy.url",
        app.config["SQLALCHEMY_DATABASE_URI"])

    command.stamp(alembic_cfg, 'head')
    print 'Done.'


@manager.command
def create_project(projectname):
    """Create a single project"""
    try:
        new_project = Project(projectname)
        db.session.add(new_project)
        db.session.commit()
    except IntegrityError:
        print 'Error: Project with name "{0}" already exists.'.format(projectname)
        return

    print 'Created project "{0}"'.format(projectname)


@manager.command
def create_sprint(projectname, sprintname):
    """Create a new spring for a project"""
    try:
        proj = db.session.query(Project).filter_by(name=projectname).one()
    except NoResultFound:
        print 'Error: Project "{0}" does not exist.'.format(projectname)
        return

    try:
        new_sprint = Sprint(project_id=proj.id, name=sprintname)
        db.session.add(new_sprint)
        db.session.commit()
    except IntegrityError:
        print 'Error: Sprint with name "{0}" already exists for project {1}.'.format(
            sprintname, projectname)
        return

    print 'Created sprint {0} for project {1}.'.format(sprintname, projectname)


if __name__ == '__main__':
    manager.run()
