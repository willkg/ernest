import collections
import json
import os
import urllib
import uuid

import requests

from flask import Flask, request, make_response, abort, jsonify, send_file, render_template
from flask.views import MethodView
from flask.ext.sqlalchemy import SQLAlchemy

from werkzeug.contrib.cache import MemcachedCache
from werkzeug.routing import BaseConverter


DAY = 60 * 60 * 24
MONTH = DAY * 30

# FIXME - move these to config file
LOGIN_URL = 'https://bugzilla.mozilla.org/index.cgi'
BUGZILLA_API_URL = 'https://api-dev.bugzilla.mozilla.org/latest'


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


app.memcache = MemcachedCache(
    # FIXME - if app.config.get some non-string, this fails
    servers=app.config.get('MEMCACHE_URL').split(','),
    key_prefix=app.config.get('MEMCACHE_PREFIX', 'ernest:'))


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


def cache_set(key, value, *args, **options):
    if isinstance(value, (dict, list, bool)):
        value = json.dumps(value)
    app.memcache.set(key, value, *args, **options)


def cache_get(key, default=None):
    value = app.memcache.get(key)
    if value is None:
        value = default
    if value is not None and not isinstance(value, (dict, list, bool)):
        value = json.loads(value)
    return value


class SprintListView(MethodView):
    def get(self):
        return render_template(
            'sprint_list.html',
            # FIXME - hard-coded
            sprints=['2013.19', '2013.20']
        )


class SprintView(MethodView):
    def get(self, sprint=None):
        token = request.cookies.get('token')
        changed_after = request.args.get('since')

        components = [
            # FIXME - hardcoded
            {'product': 'support.mozilla.org', 'component': '__ANY__'}
        ]

        bug_data = fetch_bugs(
            components,
            fields=(
                'id',
                'summary',
                'status',
                'whiteboard',
                'last_change_time',
                'component'
            ),
            sprint=sprint,
            token=token,
            changed_after=changed_after,
        )

        # FIXME - this fails if there's no bug data
        latest_change_time = max(
            [bug.get('last_change_time', 0) for bug in bug_data['bugs']])

        return render_template(
            'sprint.html',
            sprint=sprint,
            latest_change_time=latest_change_time,
            bugs=bug_data['bugs']
        )


class LogoutView(MethodView):
    def post(self):
        cookie_token = str(request.cookies.get('token'))
        response = make_response('logout')
        response.set_cookie('token', '', expires=0)
        response.set_cookie('username', '', expires=0)
        # delete from memcache too
        token_cache_key = 'token:%s' % cookie_token
        app.memcache.delete(token_cache_key)
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


def augment_with_auth(request_arguments, token):
    user_cache_key = 'auth:%s' % token
    user_info = cache_get(user_cache_key)
    if user_info:
        request_arguments['userid'] = user_info['Bugzilla_login']
        request_arguments['cookie'] = user_info['Bugzilla_logincookie']


def fetch_bugs(components, fields, sprint=None, token=None, bucket_requests=3,
               changed_after=None):

    combined = collections.defaultdict(list)
    for i in range(0, len(components), bucket_requests):
        some_components = components[i:i + bucket_requests]
        bug_data = _fetch_bugs(
            components=some_components,
            sprint=sprint,
            fields=fields,
            token=token,
            changed_after=changed_after,
        )
        for key in bug_data:
            if key == 'bugs' and changed_after:
                # For some ungodly reason, even if you pass `changed_after`
                # into the bugzilla API you sometimes get bugs that were last
                # updated BEFORE the `changed_after` parameter specifies.
                # We suspect this is due to certain changes not incrementing
                # the `last_change_time` on the bug. E.g. whiteboard changes.
                # Also, the `changed_after` parameter does a:
                # `last_change_time >= :changed_after` operation but we only
                # want those that are greater than `:changed_after`.
                bugs = [
                    bug for bug in bug_data[key]
                    if bug['last_change_time'] > changed_after
                ]
                combined[key].extend(bugs)
            else:
                combined[key].extend(bug_data[key])

    return combined


def fetch_bug(id, token=None, refresh=False, fields=None):
    # @refresh is currently not implemented
    return _fetch_bugs(id=id, token=token, fields=fields)


class BugzillaError(Exception):
    pass


def _fetch_bugs(id=None, components=None, sprint=None, fields=None, token=None, changed_after=None):
    params = {}

    if fields:
        params['include_fields'] = ','.join(fields)

    if components:
        for each in components:
            p = params.get('product', [])
            p.append(each['product'])
            params['product'] = p
            # c = params.get('component', [])
            # c.append(each['component'])
            # params['component'] = c

    if sprint:
        params['whiteboard'] = 's=' + sprint
        params['whiteboard_type'] = 'contains'

    if token:
        augment_with_auth(params, token)

    if changed_after:
        params['changed_after'] = changed_after

    url = BUGZILLA_API_URL
    url += '/bug'

    if id:
        url += '/%s' % id

    r = requests.request(
        'GET',
        url,
        params=params,
    )
    if r.status_code != 200:
        raise BugzillaError(r.text)

    response_text = r.text
    return json.loads(response_text)


# FIXME - we don't use this so far. it allows you to do bugzilla api
# calls from javascript, but it seems to use urlencoded data, so I
# don't know what to do with this.
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    path = str(path)
    request_arguments = dict(request.args)
    # str() because it's a Cookie Morsel
    token = str(request.cookies.get('token'))
    augment_with_auth(request_arguments, token)
    r = requests.request(
        request.method,
        BUGZILLA_API_URL + '/{0}'.format(path),
        params=request_arguments,
        data=request.form
    )
    return r.text


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


app.add_url_rule('/api/sprint/<sprint>', view_func=SprintView.as_view('sprint'))
app.add_url_rule('/api/sprint/', view_func=SprintListView.as_view('sprint-list'))
app.add_url_rule('/api/logout', view_func=LogoutView.as_view('logout'))
app.add_url_rule('/api/login', view_func=LoginView.as_view('login'))


if __name__ == '__main__':
    db.create_all()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port)
