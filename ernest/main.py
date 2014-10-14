import os
import re

import requests

from flask import (Flask, request, make_response, abort, jsonify,
                   send_file, session, json)
from flask.views import MethodView
from flask.ext.sqlalchemy import SQLAlchemy

from flask_sslify import SSLify
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.routing import BaseConverter

from .bugzilla import BugzillaTracker
from .version import VERSION, VERSION_RAW
from .utils import gravatar_url, smart_date


# ----------------------------------------
# "Constants"
# ----------------------------------------

DAY = 60 * 60 * 24
MONTH = DAY * 30


# ----------------------------------------
# Flask app setup and configuration
# ----------------------------------------

app = Flask(__name__)

# Convert Heroku variables into ones we like
for new_key, old_key in (('SQLALCHEMY_DATABASE_URI', 'DATABASE_URL'),
                         ('CACHE_MEMCACHED_USERNAME', 'MEMCACHIER_USERNAME'),
                         ('CACHE_MEMCACHED_PASSWORD', 'MEMCACHIER_PASSWORD')):
    app.config.setdefault(new_key, os.environ.get(old_key))

app.config.setdefault(
    'CACHE_MEMCACHED_SERVERS',
    os.environ.get('MEMCACHIER_SERVERS', '').split(','))

# Handle settings. These override environment variables.
settings_key = 'ERNEST_SETTINGS'.upper()
if os.environ.get(settings_key):
    app.config.from_envvar(settings_key, silent=True)

else:
    from ernest import settings
    app.config.from_object(settings)

# SSLify
sslify = SSLify(app)

# Register error handlers
from ernest.errors import register_error_handlers
register_error_handlers(app)

# Create DB
db = SQLAlchemy(app)


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    word_split_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    result = []
    for word in word_split_re.split(text.lower()):
        word = word.encode('ascii', 'ignore')
        if word:
            result.append(word)

    if not result:
        result = ['no', 'slug']

    return unicode(delim.join(result))


class ExtensibleJSONEncoder(json.JSONEncoder):
    """A JSON decoder that will check for a .__json__ methon on objects."""
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        return super(ExtensibleJSONEncoder, self).default(obj)


app.json_encoder = ExtensibleJSONEncoder


# ----------------------------------------
# Models
# ----------------------------------------


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    slug = db.Column(db.String(20), unique=True)

    github_owner = db.Column(db.String(20))
    github_repo = db.Column(db.String(20))

    def __init__(self, name):
        self.name = name
        self.slug = slugify(name)
        self.github_owner = ''
        self.github_repo = ''

    def __repr__(self):
        return '<Project {0}>'.format(self.name)

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'github_owner': self.github_owner,
            'github_repo': self.github_repo
        }


class ProjectAdmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(100))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship(
        'Project', backref=db.backref('admin', lazy='dynamic'))

    def __init__(self, project_id, account):
        self.project_id = project_id
        self.account = account

    def __repr__(self):
        return '<ProjectAdmin {0}>'.format(self.account)


class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    slug = db.Column(db.String(20))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    postmortem = db.Column(db.Text)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship(
        'Project', backref=db.backref('sprints', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('project_id', 'name', name='_project_sprint_uc'),
    )

    def __init__(self, project_id, name):
        self.project_id = project_id
        self.name = name
        self.slug = slugify(name)

    def __repr__(self):
        return '<Sprint {0}:{1}>'.format(self.project, self.name)

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'start_date': self.start_date.isoformat() if self.start_date else '',
            'end_date': self.end_date.isoformat() if self.end_date else '',
            'notes': self.notes,
            'postmortem': self.postmortem,
        }


# ----------------------------------------
# Template stuff
# ----------------------------------------


@app.context_processor
def basecontext():
    return {
        'VERSION': VERSION,
        'VERSION_RAW': VERSION_RAW,
    }


# ----------------------------------------
# Views and routes
# ----------------------------------------

def is_admin(username, project):
    try:
        (db.session
         .query(ProjectAdmin)
         .filter_by(account=username, project_id=project.id)
         .one())
        return True
    except NoResultFound:
        return False


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


class ProjectListView(MethodView):
    def get(self):
        projects = db.session.query(Project).all()
        return jsonify({
            'projects': projects,
        })


class ProjectDetailsView(MethodView):
    def get(self, projectslug):
        # FIXME - this can raise an error
        project = db.session.query(Project).filter_by(slug=projectslug).one()

        # FIXME - this can raise an error
        sprints = (db.session.query(Sprint)
                   .filter_by(project_id=project.id)
                   .order_by(Sprint.name)
                   .all())

        bugzilla_userid = session.get('Bugzilla_login')
        bugzilla_cookie = session.get('Bugzilla_logincookie')

        components = [
            {'product': project.name, 'component': '__ANY__'}
        ]

        bz = BugzillaTracker(app)
        bug_data = bz.fetch_bugs(
            fields=(
                'id',
                'priority',
                'summary',
                'last_change_time',
                'depends_on',
                'target_milestone',
            ),
            components=components,
            summary='[tracker]',
            userid=bugzilla_userid,
            cookie=bugzilla_cookie,
            status=['UNCONFIRMED', 'NEW', 'ASSIGNED', 'REOPENED'],
        )

        trackers = bug_data['bugs']
        for bug in trackers:
            bug['needinfo'] = []

            for flag in bug.get('flags', []):
                if flag['name'] == 'needinfo':
                    needinfo_requestee = flag['requestee']['name']
                    if '@' in needinfo_requestee:
                        needinfo_requestee = needinfo_requestee.split('@')[0]
                    bug['needinfo'].append({
                        'username': needinfo_requestee,
                        'name': flag['requestee']['name']
                    })
                # FIXME - are there other flags we're interested in?

        return jsonify({
            'is_admin': is_admin(session.get('username'), project),
            'trackers': trackers,
            'project': project,
            'sprints': sprints
        })

    def post(self, projectslug):
        """This creates a new sprint."""
        proj = db.session.query(Project).filter_by(slug=projectslug).one()

        if not is_admin(session.get('username'), proj):
            # This is bad since this is probably JSON.
            abort(403)

        json_data = request.get_json(force=True)

        if 'sprintname' in json_data:
            # Create a new sprint
            name = json_data['sprintname']
            new_sprint = Sprint(project_id=proj.id, name=name)
            db.session.add(new_sprint)
            db.session.commit()
            return jsonify({
                'new_sprint': new_sprint
            })

        # Update project details
        proj.name = json_data['name']
        proj.github_owner = json_data['github_owner']
        proj.github_repo = json_data['github_repo']
        db.session.add(proj)
        db.session.commit()
        return jsonify({
            'project': proj
        })


class ProjectSprintView(MethodView):
    def get(self, projectslug, sprintslug):
        # FIXME - this can raise an error
        project = db.session.query(Project).filter_by(slug=projectslug).one()

        # FIXME - this can raise an error
        sprint = (db.session.query(Sprint)
                  .filter_by(project_id=project.id, slug=sprintslug).one())
        sprints = list((db.session.query(Sprint)
                        .filter_by(project_id=project.id)
                        .all()))
        # FIXME - this sorts sprints on name to figure out prev/next sprints.
        # The code is gross.
        sprints.sort(key=lambda spr: spr.name)
        next_sprint = None
        prev_sprint = None
        for i, spr in enumerate(sprints):
            if spr.id == sprint.id:
                if i > 0:
                    prev_sprint = sprints[i-1]
                if i < len(sprints) - 1:
                    next_sprint = sprints[i+1]
                break

        bugzilla_userid = session.get('Bugzilla_login')
        bugzilla_cookie = session.get('Bugzilla_logincookie')
        my_email = session.get('username')
        changed_after = request.args.get('since')

        components = [
            {'product': project.name, 'component': '__ANY__'}
        ]

        bz = BugzillaTracker(app)
        bug_data = bz.fetch_bugs(
            fields=(
                'id',
                'priority',
                'summary',
                'status',
                'whiteboard',
                'last_change_time',
                'component',
                'depends_on',
                'flags',
                'groups',
                'assigned_to',
            ),
            components=components,
            sprint=sprint.name,
            userid=bugzilla_userid,
            cookie=bugzilla_cookie,
            changed_after=changed_after,
        )

        bugs = bz.mark_is_blocked(
            bug_data['bugs'], bugzilla_userid, bugzilla_cookie)
        total_bugs = len(bugs)
        closed_bugs = 0
        total_points = 0
        closed_points = 0
        bugs_with_no_points = 0

        priority_breakdown = {}
        points_breakdown = {}
        component_breakdown = {}

        for bug in bugs:
            bug['needinfo'] = []
            bug['confidentialgroup'] = False
            bug['securitygroup'] = False

            if bug.get('assigned_to', {}).get('real_name', '').startswith('Nobody'):
                # This nixes the assigned_to because it's silly long
                # when no one is assigned to the bug.
                bug['assigned_to'] = {}

            email = bug.get('assigned_to', {}).get('name')
            if email and my_email:
                bug['gravatar_url'] = gravatar_url(email, 40)
            else:
                bug['gravatar_url'] = False

            if email and email == my_email:
                bug['mine'] = True
            else:
                bug['mine'] = False

            for flag in bug.get('flags', []):
                if flag['name'] == 'needinfo':
                    needinfo_requestee = flag['requestee']['name']
                    if '@' in needinfo_requestee:
                        needinfo_requestee = needinfo_requestee.split('@')[0]
                    bug['needinfo'].append({
                        'username': needinfo_requestee,
                        'name': flag['requestee']['name']
                    })
                # FIXME - are there other flags we're interested in?

            for group in bug.get('groups', []):
                if group['name'] == 'mozilla-corporation-confidential':
                    bug['confidentialgroup'] = True
                elif group['name'] == 'websites-security':
                    bug['securitygroup'] = True

            # Pick out whiteboard data
            wb_data = bz.parse_whiteboard(bug['whiteboard'])
            bug['points'] = wb_data.get('p', None)
            bug['component'] = wb_data.get('c', None)

            if bug['points'] is None:
                bugs_with_no_points += 1
            else:
                total_points += bug['points']
                if bug['status'].lower() in ('resolved', 'verified'):
                    closed_points += bug['points']
                    closed_bugs += 1

            priority_breakdown[bug['priority']] = (
                priority_breakdown.get(bug['priority'], 0) + 1)
            points_breakdown[bug['points']] = (
                points_breakdown.get(bug['points'], 0) + 1)
            component_breakdown[bug['component']] = (
                component_breakdown.get(bug['component'], 0) + 1)

            bug['whiteboardflags'] = wb_data['flags']

        # FIXME - this fails if there's no bug data
        latest_change_time = max(
            [bug.get('last_change_time', 0) for bug in bug_data['bugs']])

        # FIXME - this is a stopgap until we have sorting in the
        # table. It tries hard to sort P1 through P5 and then bugs
        # that don't have a priority (for which the value is the
        # helpful '--') go at the bottom.
        bugs.sort(key=lambda bug: (
            bug.get('priority') if bug.get('priority') != '--' else 'P6')
        )

        # Convert this to a sorted list of dicts because Angular is Angular.
        priority_breakdown = [
            {'priority': key, 'count': priority_breakdown[key]}
            for key in sorted(priority_breakdown.keys(),
                              key=lambda p: p if p != '--' else 'P6')]
        points_breakdown = [
            {'num': key, 'count': points_breakdown[key]}
            for key in sorted(points_breakdown.keys(),
                              key=lambda p: p or '?')]
        component_breakdown = [
            {'name': key, 'count': component_breakdown[key]}
            for key in sorted(component_breakdown.keys())]

        return jsonify({
            'is_admin': is_admin(request.cookies.get('username'), project),
            'project': project,
            'prev_sprint': prev_sprint,
            'sprint': sprint,
            'next_sprint': next_sprint,
            'latest_change_time': latest_change_time,
            'bugs': bugs,
            'total_bugs': total_bugs,
            'closed_bugs': closed_bugs,
            'total_points': total_points,
            'closed_points': closed_points,
            'bugs_with_no_points': bugs_with_no_points,
            'priority_breakdown': priority_breakdown,
            'points_breakdown': points_breakdown,
            'component_breakdown': component_breakdown,
        })

    def post(self, projectslug, sprintslug):
        """Update sprint details."""
        # FIXME - this can raise an error
        proj = db.session.query(Project).filter_by(slug=projectslug).one()

        # FIXME - this can raise an error
        sprint = (db.session.query(Sprint)
                  .filter_by(project_id=proj.id, slug=sprintslug).one())

        if not is_admin(request.cookies.get('username'), proj):
            # This is bad since this is probably JSON.
            abort(403)

        json_data = request.get_json(force=True)

        # FIXME: Bad error handling here
        sprint.start_date = smart_date(json_data.get('start_date', None))
        sprint.end_date = smart_date(json_data.get('end_date', None))

        notes = json_data.get('notes', None)
        if notes is not None:
            sprint.notes = notes

        postmortem = json_data.get('postmortem', None)
        if postmortem is not None:
            sprint.postmortem = postmortem

        db.session.add(sprint)
        db.session.commit()
        return jsonify({
            'sprint': sprint
        })


class BugzillaBugDetailsView(MethodView):
    def get(self, bugid):
        bugzilla_userid = session.get('Bugzilla_login')
        bugzilla_cookie = session.get('Bugzilla_logincookie')
        my_email = session.get('username')

        bz = BugzillaTracker(app)

        bug_data = bz.fetch_bug(
            bugid,
            userid=bugzilla_userid,
            cookie=bugzilla_cookie,
            fields=(
                'id',
                'priority',
                'summary',
                'status',
                'whiteboard',
                'last_change_time',
                'product',
                'component',
                'depends_on',
                'target_milestone',
                'flags',
                'comments',
                'assigned_to',
                'reported',
            ))
        bug_data = bug_data['bugs'][0]

        if bug_data.get('assigned_to', {})['real_name'].startswith('Nobody'):
            # This nixes the assigned_to because it's silly long
            # when no one is assigned to the bug.
            bug_data['assigned_to'] = {}

        # FIXME - this is gross.
        bug_data['project_slug'] = slugify(bug_data['product'])

        bug_data['confidentialgroup'] = False
        bug_data['securitygroup'] = False

        for group in bug_data.get('groups', []):
            if group['name'] == 'mozilla-corporation-confidential':
                bug_data['confidentialgroup'] = True
            elif group['name'] == 'websites-security':
                bug_data['securitygroup'] = True

        blocker_bug_ids = bug_data.get('depends_on', [])
        if blocker_bug_ids:
            # FIXME: Using "private" methods is goofypants.
            blocker_bugs = bz._fetch_bugs(
                ids=blocker_bug_ids,
                userid=bugzilla_userid,
                cookie=bugzilla_cookie,
                fields=(
                    'id',
                    'priority',
                    'summary',
                    'status',
                    'whiteboard',
                    'last_change_time',
                    'component',
                    'depends_on',
                    'flags',
                    'groups',
                    'assigned_to',
                ),
            )

            for bug in blocker_bugs['bugs']:
                bug['needinfo'] = []
                bug['confidentialgroup'] = False
                bug['securitygroup'] = False

                if bug.get('assigned_to', {})['real_name'].startswith('Nobody'):
                    # This nixes the assigned_to because it's silly long
                    # when no one is assigned to the bug.
                    bug['assigned_to'] = {}

                email = bug.get('assigned_to', {}).get('name')
                if email and my_email:
                    bug['gravatar_url'] = gravatar_url(email, 40)
                else:
                    bug['gravatar_url'] = False

                if email and email == my_email:
                    bug['mine'] = True
                else:
                    bug['mine'] = False

                for flag in bug.get('flags', []):
                    if flag['name'] == 'needinfo':
                        needinfo_requestee = flag['requestee']['name']
                        if '@' in needinfo_requestee:
                            needinfo_requestee = needinfo_requestee.split('@')[0]
                        bug['needinfo'].append({
                            'username': needinfo_requestee,
                            'name': flag['requestee']['name']
                        })
                    # FIXME - are there other flags we're interested in?

                for group in bug.get('groups', []):
                    if group['name'] == 'mozilla-corporation-confidential':
                        bug['confidentialgroup'] = True
                    elif group['name'] == 'websites-security':
                        bug['securitygroup'] = True

                # Pick out whiteboard data
                wb_data = bz.parse_whiteboard(bug.get('whiteboard', ''))
                bug['sprint'] = wb_data.get('s', None)
                bug['points'] = wb_data.get('p', None)
                bug['component'] = wb_data.get('c', None)

            bug_data['blockers'] = blocker_bugs['bugs']

        else:
            bug_data['blockers'] = []

        # bug_data['comments'] = bz.fetch_comments(bug_data['id'])

        return jsonify({
            'bug': bug_data,
        })


class LogoutView(MethodView):
    def post(self):
        session.pop('Bugzilla_login', None)
        session.pop('Bugzilla_logincookie', None)
        session.pop('username', None)

        response = make_response('logout')

        # Make sure to nix the cookie that indicates we're logged in
        # to the client.
        response.set_cookie('username', '', expires=0)
        return response


class LoginView(MethodView):
    def post(self):
        # Get the POST data credentials and log into Bugzilla
        # via the login url
        json_data = request.get_json(force=True)
        login_payload = {
            'Bugzilla_login': json_data['login'],
            'Bugzilla_password': json_data['password'],
            'Bugzilla_remember': 'on',
            'GoAheadAndLogIn': 'Log in'
        }
        r = requests.post(app.config['BUGZILLA_LOGIN_URL'],
                          data=login_payload)
        cookies = requests.utils.dict_from_cookiejar(r.cookies)

        # Pull out the data from the response and stick it in our
        # session.
        if not 'Bugzilla_login' in cookies:
            abort(401, "Either your username or password was incorrect")
            return make_response(jsonify({'result': 'failed'}))

        session['Bugzilla_login'] = cookies['Bugzilla_login']
        session['Bugzilla_logincookie'] = cookies['Bugzilla_logincookie']
        session['username'] = json_data['login']

        response = make_response(jsonify({'result': 'success'}))

        # We put the username into a cookie that can be accessed by JS
        # so that the client knows we're logged in.
        response.set_cookie('username', json_data['login'])
        return response


@app.route('/')
@app.route('/<start>')
@app.route('/<start>/<path:path>')
def static_stuff(start=None, path=None):
    """Handles static files and falls back to serving the Angular homepage."""
    if start in ['css', 'img', 'js', 'font', 'partials']:
        return send_file('static/%s/%s' % (start, path))
    else:
        return send_file('static/index.html')


# FIXME - we don't use this so far. it allows you to do bugzilla api
# calls from javascript, but it seems to use urlencoded data, so I
# don't know what to do with this.
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    return BugzillaTracker(app).bugzilla_api(
        path,
        request,
        session.get('Bugzilla_login'),
        session.get('Bugzilla_logincookie'))


# Special rule for old browsers to correctly handle favicon.
@app.route('/favicon.ico')
def favicon():
    return send_file(
        'static/favicon.ico',
        mimetype='image/vnd.microsoft.icon')


app.add_url_rule(
    '/api/project/<projectslug>/<sprintslug>',
    view_func=ProjectSprintView.as_view('project-sprint'))
app.add_url_rule(
    '/api/project/<projectslug>',
    view_func=ProjectDetailsView.as_view('project-details'))
app.add_url_rule(
    '/api/project',
    view_func=ProjectListView.as_view('project-list'))
app.add_url_rule(
    '/api/bugzilla/bug/<bugid>',
    view_func=BugzillaBugDetailsView.as_view('bugzilla-bug-details'))

app.add_url_rule('/api/logout', view_func=LogoutView.as_view('logout'))
app.add_url_rule('/api/login', view_func=LoginView.as_view('login'))


if __name__ == '__main__':
    db.create_all()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port)
