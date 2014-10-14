/* Services */

var ernest = angular.module('ernest');

// To do: this should pull from the server.
ernest.value('version', '0.1a1');

ernest.factory('Api', ['$resource', 'localStorageService',
    function($resource, localStorageService) {

        function bugUrl() {
            return 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + this.id;
        }

        function augmentProject(proj) {
            proj.url = '/project/' + proj.slug;
            return proj;
        }

        function augmentSprint(project, sprint, bugs) {
            var i,
                buglist_all = [],
                buglist_open = [],
                today = new Date();

            sprint.project = project;
            sprint.url = '/project/' + project.slug + '/' + sprint.slug;

            if (today >= new Date(sprint.start_date) && today <= new Date(sprint.end_date)) {
                sprint.current = true;
            } else {
                sprint.current = false;
            }

            // bugzilla buglist urls
            if (bugs) {
                for (i = 0; i < bugs.length; i++) {
                    buglist_all.push(bugs[i].id);
                    if (bugs[i].status.toLowerCase() !== 'resolved'
                        && bugs[i].status.toLowerCase() !== 'verified') {

                        buglist_open.push(bugs[i].id);
                    }
                }
                sprint.buglist_all_url = 'https://bugzilla.mozilla.org/buglist.cgi?bug_id=' +
                    buglist_all.join(',');

                sprint.buglist_open_url = 'https://bugzilla.mozilla.org/buglist.cgi?bug_id=' +
                    buglist_open.join(',');
            }

            return sprint;
        }

        function augmentBug(bug, sprint) {
            var baseUrl = 'https://bugzilla.mozilla.org/show_bug.cgi?id=';
            bug.url = baseUrl + bug.id;
            if (bug.open_blockers) {
                bug.open_blockers = bug.open_blockers.map(function(bugId) {
                    return {
                        id: bugId,
                        url: baseUrl + bugId,
                    };
                });
            }
            bug.details_url = '/bugzilla/bug/' + bug.id;

            if (bug.points !== null && sprint !== undefined && sprint.end_date !== null) {
                // If the bug has points allocated and we know the
                // sprint end_date, then we can calculate whether the
                // bug is "in jeopardy".

                // FIXME - This is hard-coded for now. It should be part of
                // the sprint data.
                var pointsToHours = {
                    0: {start: 1, end: 1},
                    1: {start: 12, end: 12},
                    2: {start: 24, end: 48},
                    3: {start: 72, end: 120}
                };

                var endDate = new Date(sprint.end_date);
                endDate.setUTCHours(23, 59, 59, 999);

                var getBound = function (hours) {
                    var now = new Date();
                    now.setUTCHours(now.getUTCHours() + hours);
                    return now;
                };

                var startBound = getBound(pointsToHours[bug.points].start);
                var endBound = getBound(pointsToHours[bug.points].end);

                if (startBound > endDate) {
                    bug.jeopardy = 'error';
                }
                if (endBound > endDate) {
                    bug.jeopardy = 'warning';
                }
            }

            bug.star = localStorageService.get('star' + bug.id) || '0';

            return bug;
        }

        function augment(data, headersGetter) {
            if (data.projects) {
                data.projects = data.projects.map(augmentProject);
            }
            if (data.project) {
                data.project = augmentProject(data.project);
            }
            if (data.trackers) {
                data.trackers = data.trackers.map(augmentBug);
            }
            if (data.sprints) {
                data.sprints = data.sprints.map(augmentSprint.bind(null, data.project));
            }
            if (data.prev_sprint) {
                data.prev_sprint = augmentSprint(data.project, data.prev_sprint);
            }
            if (data.sprint) {
                data.sprint = augmentSprint(data.project, data.sprint, data.bugs);
            }
            if (data.next_sprint) {
                data.next_sprint = augmentSprint(data.project, data.next_sprint);
            }
            if (data.bugs) {
                data.bugs = data.bugs.map(function (bug) { return augmentBug(bug, data.sprint); });
            }
            return data;
        }

        return $resource('/api/project/:projSlug/:sprintSlug/', {}, {
            query: {
                method: 'GET',
                isArray: false,
                transformResponse: [augment],
                cache: true,
                responseType: 'json'
            },
            get: {
                method: 'GET',
                isArray: false,
                transformResponse: [augment],
                cache: true,
                responseType: 'json'
            }
        });
    }
]);

ernest.factory('BugApi', ['$resource',
    function($resource) {

        function bugUrl() {
            return 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + this.id;
        }

        function augmentBug(bug) {
            var baseUrl = 'https://bugzilla.mozilla.org/show_bug.cgi?id=';
            bug.url = baseUrl + bug.id;
            if (bug.blockers) {
                bug.blockers = bug.blockers.map(function(bug_data) {
                    bug_data.url = baseUrl + bug_data.id;
                    return bug_data;
                });
            }
            bug.details_url = '/bugzilla/bug/' + bug.id;

            return bug;
        }

        function augment(data, headersGetter) {
            if (data.bugs) {
                data.bugs = data.bugs.map(augmentBug);
            }
            if (data.bug) {
                data.bug = augmentBug(data.bug);
            }
            return data;
        }

        return $resource('/api/bugzilla/bug/:bugId', {}, {
            get: {
                method: 'GET',
                isArray: false,
                transformResponse: [augment],
                cache: true,
                responseType: 'json'
            }
        });
    }
]);
