/* Services */

var ernestServices = angular.module('ernest.services', []);

// To do: this should pull from the server.
ernestServices.value('version', '0.1a1');

ernestServices.factory('Api', ['$resource',
    function($resource) {

        function parseJSON(data, headersGetter) {
            return JSON.parse(data);
        }

        function projUrl() {
            return '#/project/' + this.slug;
        }

        function sprintUrl() {
            return '#/project/' + this.project.slug + '/' + this.slug;
        }

        function addMethods(data, headersGetter) {
            if (data.projects) {
                data.projects = data.projects.map(function(proj) {
                    proj.url = projUrl.bind(proj);
                    return proj;
                });
            }
            if (data.project) {
                data.project.url = projUrl.bind(data.project);
            }
            if (data.sprints) {
                data.sprints = data.sprints.map(function(sprint) {
                    sprint.project = data.project;
                    sprint.url = sprintUrl.bind(sprint);
                    return sprint;
                });
            }
            if (data.sprint) {
                data.sprint.project = data.project;
                data.sprint.url = sprintUrl.bind(data.sprint);
            }
            return data;
        }

        return $resource('/api/project/:projSlug/:sprintSlug/', {}, {
            query: {
                method: 'GET',
                isArray: false,
                transformResponse: [parseJSON, addMethods],
                cache: true
            },
            get: {
                method: 'GET',
                isArray: false,
                transformResponse: [parseJSON, addMethods],
                cache: true
            },
        });
    }
]);
