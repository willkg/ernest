'use strict';

/* Controllers */


var ernest = angular.module('ernest');

ernest.controller('HomeCtrl', [function() {}]);

ernest.controller('ProjectListCtrl', ['$scope', 'Api',
    function($scope, Api) {
        $scope.$emit('loading+');
        $scope.projects = [];

        Api.query().$promise.then(function(data) {
            $scope.projects = data.projects;

            $scope.$emit('loading-');
        });
    }
]);

ernest.controller('ProjectDetailCtrl', ['$scope', '$routeParams', 'Api',
    function($scope, $routeParams, Api) {
        $scope.$emit('loading+');

        Api.get($routeParams).$promise.then(function(data) {
            $scope.project = data.project;
            $scope.sprints = data.sprints;

            $scope.$emit('loading-');
        });
    }
]);

ernest.controller('SprintDetailCtrl', ['$scope', '$routeParams', '$cacheFactory', 'Api',
    function($scope, $routeParams, $cacheFactory, Api) {

        $scope.bugSortBy = {key: 'priority', reverse: false};
        $scope.bugSort = function(bug) {
            var val = bug[$scope.bugSortBy.key];
            if ($scope.bugSortBy.key === 'priority' && val === '--') {
                val = 'P6';
            } else if ($scope.bugSortBy.key === 'assigned_to') {
                val = val.real_name;
            }
            return val;
        };

        $scope.refresh = function() {
            var sprint = $scope.sprint;
            var proj = sprint.project;
            if (!sprint || !proj) {
                return;
            }
            var url = '/api/project/' + proj.slug + '/' + sprint.slug;
            $cacheFactory.get('$http').remove(url);
            return getData();
        };

        $scope.$on('login', function() { $scope.refresh(); });
        $scope.$on('logout', function() { $scope.refresh(); });

        function getData() {
            $scope.$emit('loading+');

            var p = Api.get($routeParams).$promise.then(function(data) {
                $scope.$emit('loading-');

                $scope.bugs = data.bugs;
                $scope.bugs_with_no_points = data.bugs_with_no_points;
                $scope.latest_change_time = data.latest_change_time;
                $scope.prev_sprint = data.prev_sprint;
                $scope.sprint = data.sprint;
                $scope.next_sprint = data.next_sprint;
                $scope.total_bugs = data.total_bugs;
                $scope.closed_bugs = data.closed_bugs;
                $scope.total_points = data.total_points;
                $scope.closed_points = data.closed_points;
                $scope.priority_breakdown = data.priority_breakdown;
                $scope.last_load = new Date();

                if ($scope.bugs_with_no_points > 0) {
                    $scope.completionState = 'notready';
                } else if ($scope.closed_points === $scope.total_points) {
                    $scope.completionState = 'done';
                } else if ($scope.closed_points > $scope.total_points / 2) {
                    $scope.completionState = 'almost';
                } else {
                    $scope.completionState = 'incomplete';
                }
            });
            return p;
        }

        getData();
    }
]);

ernest.controller('AuthCtrl', ['$rootScope', '$scope', '$cookies', '$http',
    function($rootScope, $scope, $cookies, $http) {
        $scope.creds = {login: '', password: ''};
        $scope.loggingIn = false;

        if ($cookies.username) {
            // This has quotes around it, for some reason, remove it.
            $scope.creds.login = $cookies.username.slice(1, -1);
        }

        $scope.login = function() {
            $http.post('/api/login', $scope.creds)
                .success(function(err) {
                    $scope.creds.password = null;
                    $rootScope.$broadcast('login', $scope.creds.login);
                })
                .error(function(err) {
                    console.log(err);
                });
        };

        $scope.logout = function() {
            $http.post('/api/logout')
                .success(function() {
                    $rootScope.$broadcast('logout');
                });
        };

        $scope.loggedIn = function() {
            return !!$cookies.username;
        };
    }
]);

ernest.controller('LoadingCtrl', ['$rootScope', '$scope',
    function($rootScope, $scope) {
        $scope.loading = 0;

        $rootScope.$on('loading+', function() {
            $scope.loading++;
        });
        $rootScope.$on('loading-', function() {
            $scope.loading--;
            if ($scope.loading < 0) {
                throw Error('More loading- events than loading+ events.');
            }
        });
    }
]);
