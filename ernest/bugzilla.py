import collections
import json

import requests


class BugzillaError(Exception):
    pass


class BugzillaTracker(object):
    def __init__(self, app):
        self.app = app
        self.bzurl = app.config['BUGZILLA_API_URL']

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

    def fetch_bugs(self, components, fields, sprint=None, token=None,
                   bucket_requests=3, changed_after=None):

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
        return self._fetch_bugs(id=id_, token=token, fields=fields)

    def _fetch_bugs(self, id_=None, components=None, sprint=None, fields=None,
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

        if id_:
            url += '/%s' % id_

        r = requests.request(
            'GET',
            url,
            params=params,
        )
        if r.status_code != 200:
            raise BugzillaError(r.text)

        response_text = r.text
        return json.loads(response_text)
