/* Services */

var ernest = angular.module('ernest');

// To do: this should pull from the server.
ernest.value('version', '0.1a1');

ernest.factory('Api', ['$resource',
    function($resource) {

        function parseJSON(data, headersGetter) {
            return JSON.parse(data);
        }

        function bugUrl() {
            return 'https://bugzilla.mozilla.org/show_bug.cgi?id=' + this.id;
        }

        function augmentProject(proj) {
            proj.url = '/project/' + proj.slug;
            return proj;
        }

        function augmentSprint(project, sprint, bugs) {
            var i, buglist_all = [], buglist_open = [];

            sprint.project = project;
            sprint.url = '/project/' + project.slug + '/' + sprint.slug;

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

        function augmentBug(bug) {
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
                data.bugs = data.bugs.map(augmentBug);
            }
            return data;
        }

        return $resource('/api/project/:projSlug/:sprintSlug/', {}, {
            query: {
                method: 'GET',
                isArray: false,
                transformResponse: [parseJSON, augment],
                cache: true
            },
            get: {
                method: 'GET',
                isArray: false,
                transformResponse: [parseJSON, augment],
                cache: true
            }
        });
    }
]);
