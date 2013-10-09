import datetime
import json
import os
import uuid

import requests

from flask import Flask, request, make_response, abort, jsonify, send_file, render_template
from flask.views import MethodView
from flask.ext.sqlalchemy import SQLAlchemy

from werkzeug.routing import BaseConverter

from .bugzilla import BugzillaTracker
from .cache import build_cache
from .version import VERSION, VERSION_RAW


DAY = 60 * 60 * 24
MONTH = DAY * 30

# FIXME - move this to config file
LOGIN_URL = 'https://bugzilla.mozilla.org/index.cgi'

# Create the app
app = Flask(__name__)

# Handle settings--look at os.environ first
settings_key = 'ERNEST_SETTINGS'.upper()
if os.environ.get(settings_key):
    app.config.from_envvar(settings_key, silent=True)

else:
    from ernest import settings
    app.config.from_object(settings)

# Register error handlers
from ernest.errors import register_error_handlers
register_error_handlers(app)

# Create DB
db = SQLAlchemy(app)


app.cache = build_cache(app.config)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


def cache_set(key, value, *args, **options):
    if isinstance(value, (dict, list, bool)):
        value = json.dumps(value)
    app.cache.set(key, value, *args, **options)


def cache_get(key, default=None):
    value = app.cache.get(key)
    if value is None:
        value = default
    if value is not None and not isinstance(value, (dict, list, bool)):
        value = json.loads(value)
    return value


@app.template_filter('df')
def dateformat_filter(d, fmt):
    if isinstance(d, basestring):
        d = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
    return d.strftime(fmt)


@app.context_processor
def basecontext():
    return {
        'VERSION': VERSION,
        'VERSION_RAW': VERSION_RAW,
    }

class QueueListView(MethodView):
    def get(self):
        return render_template(
            'queue.html'
        )


class SprintListView(MethodView):
    def get(self):
        return render_template(
            'sprint_list.html',
            # FIXME - hard-coded
            sprints=[
                ('support.mozilla.org', '2013.19'),
                ('support.mozilla.org', '2013.20'),
            ]
        )


class SprintView(MethodView):
    def get(self, product, sprint):
        token = request.cookies.get('token')
        changed_after = request.args.get('since')

        components = [
            {'product': product, 'component': '__ANY__'}
        ]

        bz = BugzillaTracker(app)
        bug_data = bz.fetch_bugs(
            components,
            fields=(
                'id',
                'summary',
                'status',
                'whiteboard',
                'last_change_time',
                'component',
                'depends_on',
                'flags',
                'groups',
            ),
            sprint=sprint,
            token=token,
            changed_after=changed_after,
        )

        bugs = bug_data['bugs']
        total_points = 0
        closed_points = 0
        bugs_with_no_points = 0

        for bug in bugs:
            bug['needinfo'] = []
            bug['confidentialgroup'] = False
            bug['securitygroup'] = False

            for flag in bug.get('flags', []):
                if flag['name'] == 'needinfo':
                    bug['needinfo'].append(flag['requestee']['name'])
                # FIXME - are there other flags we're interested in?

            for group in bug.get('groups', []):
                if group['name'] == 'mozilla-corporation-confidential':
                    bug['confidentialgroup'] = True
                elif group['name'] == 'websites-security':
                    bug['securitygroup'] = True

            # Pick out whiteboard data
            wb_data = bz.parse_whiteboard(bug['whiteboard'])
            bug['points'] = wb_data.get('p', None)

            if bug['points'] is None:
                bugs_with_no_points += 1
            else:
                total_points += bug['points']
                if bug['status'].lower() in ('resolved', 'verified'):
                    closed_points += bug['points']

            bug['whiteboardflags'] = wb_data['flags']

        # FIXME - this fails if there's no bug data
        latest_change_time = max(
            [bug.get('last_change_time', 0) for bug in bug_data['bugs']])

        return render_template(
            'sprint.html',
            sprint=sprint,
            latest_change_time=latest_change_time,
            bugs=bugs,
            total_points=total_points,
            closed_points=closed_points,
            bugs_with_no_points=bugs_with_no_points,
            last_load=datetime.datetime.now(),
        )


class LogoutView(MethodView):
    def post(self):
        cookie_token = str(request.cookies.get('token'))
        response = make_response('logout')
        response.set_cookie('token', '', expires=0)
        response.set_cookie('username', '', expires=0)
        # delete from cache too
        token_cache_key = 'token:%s' % cookie_token
        app.cache.delete(token_cache_key)
        return response


class LoginView(MethodView):
    def get(self):
        return render_template('index.html')

    def post(self):
        json_data = request.get_json(force=True)
        login_payload = {
            'Bugzilla_login': json_data['login'],
            'Bugzilla_password': json_data['password'],
            'Bugzilla_remember': 'on',
            'GoAheadAndLogIn': 'Log in'
        }
        login_response = {}
        r = requests.post(LOGIN_URL, data=login_payload)
        cookies = requests.utils.dict_from_cookiejar(r.cookies)
        if 'Bugzilla_login' in cookies:
            token = str(uuid.uuid4())
            token_cache_key = 'auth:%s' % token
            cache_set(token_cache_key, {
                'Bugzilla_login': cookies['Bugzilla_login'],
                'Bugzilla_logincookie': cookies['Bugzilla_logincookie'],
                'username': request.json['login']
            }, MONTH)
            login_response['result'] = 'success'
            login_response['token'] = token
            response = make_response(jsonify(login_response))
            response.set_cookie('token', token)
            response.set_cookie('username', request.json['login'])
            return response
        else:
            abort(401, "Either your username or password was incorrect")
            login_response['result'] = 'failed'
            response = make_response(jsonify(login_response))
            return response


# FIXME - we don't use this so far. it allows you to do bugzilla api
# calls from javascript, but it seems to use urlencoded data, so I
# don't know what to do with this.
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    return BugzillaTracker(app).bugzilla_api(path, request)


# Special rule for old browsers to correctly handle favicon.
@app.route('/favicon.ico')
def favicon():
    return send_file(
        'static/favicon.ico',
        mimetype='image/vnd.microsoft.icon')


# Handles all static files
@app.route('/<regex("css|img|js|font"):start>/<path:path>')
def static_stuff(start, path):
    return send_file('static/%s/%s' % (start, path))


@app.route('/')
def index():
    return render_template('index.html')


app.add_url_rule('/api/sprint/<product>/<sprint>',
                 view_func=SprintView.as_view('sprint'))
app.add_url_rule('/api/sprint/', view_func=SprintListView.as_view('sprint-list'))
app.add_url_rule('/api/logout', view_func=LogoutView.as_view('logout'))
app.add_url_rule('/api/login', view_func=LoginView.as_view('login'))


if __name__ == '__main__':
    db.create_all()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port)
