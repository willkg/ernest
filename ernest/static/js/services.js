/* Services */

var ernestServices = angular.module('ernest.services', []);

// To do: this should pull from the server.
ernestServices.value('version', '0.1a1');

ernestServices.factory('Api', ['$resource',
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

        function augmentSprint(project, sprint) {
            sprint.project = project;
            sprint.url = '/project/' + project.slug + '/' + sprint.slug;
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
            if (data.sprints) {
                data.sprints = data.sprints.map(augmentSprint.bind(null, data.project));
            }
            if (data.prev_sprint) {
                data.prev_sprint = augmentSprint(data.project, data.prev_sprint);
            }
            if (data.sprint) {
                data.sprint = augmentSprint(data.project, data.sprint);
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
            },
        });
    }
]);
