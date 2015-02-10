#!/usr/bin/env python
import subprocess
import sys

from flask.ext.script import Manager
from prettytable import PrettyTable
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound

from ernest.main import app, db, Project, ProjectAdmin, Sprint


manager = Manager(app)


def call_command(cmd, verbose=False):
    if verbose:
        print cmd
    subprocess.call(cmd)


def get_project(projectname, exit_on_error=False):
    try:
        return db.session.query(Project).filter_by(name=projectname).one()
    except NoResultFound:
        # FIXME: Change this to print to stderr
        print 'Error: Project "{0}" does not exist.'.format(projectname)
        if exit_on_error:
            sys.exit(1)


@manager.command
def db_create():
    """Create the tables and do alembic stuff"""
    print 'db at: {0}'.format(
        app.config['SQLALCHEMY_DATABASE_URI'])
    try:
        db.engine.execute('select * from project')
        print 'Database already exists with tables.'
        return

    except (OperationalError, ProgrammingError):
        # An operational error here means that the "project" table
        # doesn't exist so we should create things!
        pass

    print 'Creating {0}....'.format(
        app.config['SQLALCHEMY_DATABASE_URI'])

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
def create_admin(projectname, adminaccount):
    """Add an admin to a project"""
    proj = get_project(projectname, exit_on_error=True)

    try:
        new_admin = ProjectAdmin(project_id=proj.id, account=adminaccount)
        db.session.add(new_admin)
        db.session.commit()
    except IntegrityError:
        print 'Error: Admin with account "{0}" already exists for project {1}.'.format(
            adminaccount, projectname)
        return

    print 'Created admin {0} for project {1}.'.format(adminaccount, projectname)


@manager.command
def create_sprint(projectname, sprintname):
    """Create a new sprint for a project"""
    proj = get_project(projectname, exit_on_error=True)

    try:
        new_sprint = Sprint(project_id=proj.id, name=sprintname)
        db.session.add(new_sprint)
        db.session.commit()
    except IntegrityError:
        print 'Error: Sprint with name "{0}" already exists for project {1}.'.format(
            sprintname, projectname)
        return

    print 'Created sprint {0} for project {1}.'.format(sprintname, projectname)


@manager.command
def list_sprints(projectname):
    """Lists all the sprints for a given project"""
    proj = get_project(projectname, exit_on_error=True)

    sprints = (db.session.query(Sprint)
               .filter_by(project_id=proj.id)
               .order_by(Sprint.name)
               .all())

    print 'Sprints for project {}'.format(proj.name)
    print ''

    if sprints:
        table = PrettyTable(['name', 'slug', 'start', 'end'])
        table.align['name'] = 'l'
        table.align['slug'] = 'l'
        table.align['start'] = 'l'
        table.align['end'] = 'l'

        for sprint in sprints:
            table.add_row([sprint.name, sprint.slug, sprint.start_date, sprint.end_date])
        print table
    else:
        print 'No sprints'


@manager.command
def delete_sprint(projectname, sprintname):
    proj = get_project(projectname, exit_on_error=True)

    try:
        sprint = db.session.query(Sprint).filter_by(project_id=proj.id, name=sprintname).one()
    except NoResultFound:
        print 'Error Sprint "{0}" does not exist.'.format(sprintname)
        return

    db.session.delete(sprint)
    db.session.commit()
    print '{0} deleted.'.format(sprintname)


if __name__ == '__main__':
    manager.run()
