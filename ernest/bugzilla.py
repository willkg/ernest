import collections
import json
import re

import requests


WHITEBOARD_SPRINT_RE = re.compile(
    r'u=(?P<user>[^\s]+) '
    r'c=(?P<component>[^\s]+) '
    r'p=(?P<points>[^\s]+) '
    r's=(?P<sprint>[^\s]+)')
WHITEBOARD_FLAGS_RE = re.compile(r'\[(?P<flag>[^\]]+)\]')


class BugzillaError(Exception):
    pass


class BugzillaTracker(object):
    def __init__(self, app):
        self.app = app
        self.bzurl = app.config['BUGZILLA_API_URL']

    def parse_whiteboard(self, whiteboard):
        if not whiteboard:
            return {}

        wb_data = {}

        wb_sprint_match = WHITEBOARD_SPRINT_RE.search(whiteboard)
        if wb_sprint_match:
            wb_data['u'] = wb_sprint_match.group('user')
            wb_data['c'] = wb_sprint_match.group('component')
            try:
                wb_data['p'] = int(wb_sprint_match.group('points'))
            except ValueError:
                pass
            wb_data['s'] = wb_sprint_match.group('sprint')

        wb_data['flags'] = WHITEBOARD_FLAGS_RE.findall(whiteboard)

        return wb_data

    def augment_with_auth(self, request_arguments, token):
        user_cache_key = 'auth:%s' % token
        user_info = self.app.cache.get(user_cache_key)
        if user_info:
            user_info = json.loads(user_info)
            request_arguments['userid'] = user_info['Bugzilla_login']
            request_arguments['cookie'] = user_info['Bugzilla_logincookie']

    def bugzilla_api(self, path, request):
        path = str(path)
        request_arguments = dict(request.args)
        # str() because it's a Cookie Morsel
        token = str(request.cookies.get('token'))
        self.augment_with_auth(request_arguments, token)
        r = requests.request(
            request.method,
            self.bzurl + '/{0}'.format(path),
            params=request_arguments,
            data=request.form
        )
        return r.text

    def is_closed(self, status):
        return status.lower() in ('resolved', 'verified')

    def mark_is_blocked(self, bugs, token=None):
        """Adds 'is_blocked' to all bugs

        Goes through the bugs and generates a set of bug ids from the
        depends_on field. Then it figures out whether those bugs are
        open or closed and sets the 'is_blocked' field accordingly.

        It does a bunch of loops so that it can do everything it needs
        with at most one additional Bugzilla API request.

        :arg bugs: The list of bugs to operate on
        :arg token: The bugzilla session token (optional)

        :returns: The bugs with the 'is_blocked' field set to True or
            False

        """

        id_to_status = {}
        blockers = set()

        # Go through all the bugs and initialize the 'is_blocked' field
        # to False, build up the id_to_status map and add any bugs
        # that the bug depends on to the blockers set.
        for bug in bugs:
            bug['is_blocked'] = False
            bug['open_blockers'] = []
            id_to_status[bug['id']] = bug['status']
            blockers.update(bug.get('depends_on', []))

        blockers = [bug for bug in blockers
                    if not self.is_closed(id_to_status.get(bug, ''))]

        if not blockers:
            # No blockers, so nothing to do!
            return bugs

        blocker_bugs = self._fetch_bugs(
            ids=list(blockers),
            token=token,
            fields=('id', 'status'))

        for bug in blocker_bugs['bugs']:
            id_to_status[bug['id']] = bug['status']

        # Go through all the original bugs and set the 'is_blocked' field
        # if any of the bugs it depends on is not closed.
        for bug in bugs:
            for blocker in bug.get('depends_on', []):
                if not self.is_closed(id_to_status[blocker]):
                    bug['is_blocked'] = True
                    bug['open_blockers'].append(blocker)

        return bugs

    def fetch_bugs(self, fields, components=None, sprint=None,
                   token=None, bucket_requests=3, changed_after=None):

        combined = collections.defaultdict(list)
        for i in range(0, len(components), bucket_requests):
            some_components = components[i:i + bucket_requests]
            bug_data = self._fetch_bugs(
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

    def fetch_bug(self, id_, token=None, refresh=False, fields=None):
        # @refresh is currently not implemented
        return self._fetch_bugs(ids=[id_], token=token, fields=fields)

    def _fetch_bugs(self, ids=None, components=None, sprint=None, fields=None,
                    token=None, changed_after=None):
        params = {}

        if fields:
            params['include_fields'] = ','.join(fields)

        if components:
            for each in components:
                p = params.get('product', [])
                p.append(each['product'])
                params['product'] = p

        if sprint:
            params['whiteboard'] = 's=' + sprint
            params['whiteboard_type'] = 'contains'

        if token:
            self.augment_with_auth(params, token)

        if changed_after:
            params['changed_after'] = changed_after

        url = self.bzurl + '/bug'

        if ids:
            params['id'] = ','.join(ids)

        r = requests.request(
            'GET',
            url,
            params=params,
        )
        if r.status_code != 200:
            raise BugzillaError(r.text)

        response_text = r.text
        return json.loads(response_text)
