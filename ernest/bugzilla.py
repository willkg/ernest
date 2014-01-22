import collections
import json
import re

import requests


def show_me_the_logs():
    """Turns on debug-level logging in requests

    This helps to find out wtf is going wrong.

    """
    import httplib
    httplib.HTTPConnection.debuglevel = 1

    import logging
    # you need to initialize logging, otherwise you will not see
    # anything from requests
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

# Uncomment this line to get better logging from requests.
# show_me_the_logs()


WHITEBOARD_SPRINT_RE = re.compile(
    r'u=(?P<user>[^\s]*) '
    r'c=(?P<component>[^\s]*) '
    r'p=(?P<points>[^\s]*) '
    r's=(?P<sprint>[^\s]*)')
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
            # Points are either an integer or an empty string
            try:
                wb_data['p'] = int(wb_sprint_match.group('points'))
            except ValueError:
                pass
            wb_data['s'] = wb_sprint_match.group('sprint')

        wb_data['flags'] = WHITEBOARD_FLAGS_RE.findall(whiteboard)

        return wb_data

    def augment_with_auth(self, request_arguments, userid, cookie):
        if userid and cookie:
            request_arguments['userid'] = userid
            request_arguments['cookie'] = cookie

    def bugzilla_api(self, path, request, userid=None, cookie=None):
        path = str(path)
        request_arguments = dict(request.args)
        self.augment_with_auth(request_arguments, userid, cookie)
        r = requests.request(
            request.method,
            self.bzurl + '/{0}'.format(path),
            params=request_arguments,
            data=request.form,
            timeout=60.0
        )
        return r.text

    def is_closed(self, status):
        return status.lower() in ('resolved', 'verified')

    def mark_is_blocked(self, bugs, userid=None, cookie=None):
        """Adds 'is_blocked' to all bugs

        Goes through the bugs and generates a set of bug ids from the
        depends_on field. Then it figures out whether those bugs are
        open or closed and sets the 'is_blocked' field accordingly.

        It does a bunch of loops so that it can do everything it needs
        with at most one additional Bugzilla API request.

        :arg bugs: The list of bugs to operate on
        :arg userid: (Optional) Bugzilla username
        :arg cookie: (Optional) Bugzilla cookie for userid

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
            userid=userid,
            cookie=cookie,
            fields=('id', 'status'))

        for bug in blocker_bugs['bugs']:
            id_to_status[bug['id']] = bug['status']

        # Go through all the original bugs and set the 'is_blocked' field
        # if any of the bugs it depends on is not closed.
        for bug in bugs:
            for blocker in bug.get('depends_on', []):
                try:
                    if not self.is_closed(id_to_status[blocker]):
                        bug['is_blocked'] = True
                        bug['open_blockers'].append(blocker)
                except KeyError:
                    # FIXME: This most likely means that the user
                    # viewing the bug list doesn't have access to this
                    # blocker and therefore cannot see it. I don't
                    # know what the right thing to do here is. So I'm
                    # going to ignore it for now.
                    pass

        return bugs

    def fetch_bugs(self, fields, components=None, sprint=None,
                   userid=None, cookie=None, changed_after=None,
                   summary=None, status=None, bucket_requests=3):

        combined = collections.defaultdict(list)
        for i in range(0, len(components), bucket_requests):
            some_components = components[i:i + bucket_requests]
            bug_data = self._fetch_bugs(
                components=some_components,
                sprint=sprint,
                fields=fields,
                userid=userid,
                cookie=cookie,
                changed_after=changed_after,
                summary=summary,
                status=status,
            )
            for key in bug_data:
                if key == 'bugs' and changed_after:
                    # For some ungodly reason, even if you pass
                    # `changed_after` into the bugzilla API you
                    # sometimes get bugs that were last updated BEFORE
                    # the `changed_after` parameter specifies.  We
                    # suspect this is due to certain changes not
                    # incrementing the `last_change_time` on the
                    # bug. E.g. whiteboard changes.  Also, the
                    # `changed_after` parameter does a:
                    # `last_change_time >= :changed_after` operation
                    # but we only want those that are greater than
                    # `:changed_after`.
                    bugs = [
                        bug for bug in bug_data[key]
                        if bug['last_change_time'] > changed_after
                    ]
                    combined[key].extend(bugs)
                else:
                    combined[key].extend(bug_data[key])

        return combined

    def fetch_bug(self, id_, userid=None, cookie=None, refresh=False,
                  fields=None):
        # @refresh is currently not implemented
        return self._fetch_bugs(ids=[id_], userid=userid, cookie=cookie,
                                fields=fields)

    def _fetch_bugs(self, ids=None, components=None, sprint=None, fields=None,
                    userid=None, cookie=None, changed_after=None, summary=None,
                    status=None):
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

        if summary:
            params['summary'] = summary
            params['summary_type'] = 'contains'

        if status:
            params['status'] = status

        self.augment_with_auth(params, userid, cookie)

        if changed_after:
            params['changed_after'] = changed_after

        url = self.bzurl + '/bug'

        if ids:
            params['id'] = ','.join(ids)

        r = requests.request(
            'GET',
            url,
            params=params,
            timeout=60.0
        )
        if r.status_code != 200:
            raise BugzillaError(r.text)

        return json.loads(r.text)

    def fetch_comments(self, bugid, userid=None, cookie=None):
        params = {}
        self.augment_with_auth(params, userid, cookie)

        url = '{0}/bug/{1}/comment'.format(self.bzurl, bugid)

        r = requests.request(
            'GET',
            url,
            params=params,
            timeout=60.0
        )
        if r.status_code != 200:
            raise BugzillaError(r.text)

        return json.loads(r.text)
