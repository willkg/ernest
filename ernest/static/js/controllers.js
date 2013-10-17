'use strict';

/* Controllers */


var ernestControllers = angular.module('ernest.controllers', []);

ernestControllers.controller('HomeCtrl', [function() {}])

ernestControllers.controller('ProjectListCtrl', ['$rootScope', '$scope', 'Api',
    function($rootScope, $scope, Api) {
        $rootScope.loading++;

        Api.query().$promise.then(function(data) {
            $scope.projects = data.projects;

            $rootScope.loading--;
        });
    }
])

ernestControllers.controller('ProjectDetailCtrl', ['$rootScope', '$scope', '$routeParams', 'Api',
    function($rootScope, $scope, $routeParams, Api) {
        $rootScope.loading++;
        
        Api.get($routeParams).$promise.then(function(data) {
            $scope.project = data.project;
            $scope.sprints = data.sprints;

            $rootScope.loading--;
        });
    }
])

ernestControllers.controller('SprintDetailCtrl', ['$rootScope', '$scope', '$routeParams', 'Api',
    function($rootScope, $scope, $routeParams, Api) {
        $rootScope.loading++;
        
        Api.get($routeParams).$promise.then(function(data) {
            $scope.bugs = data.bugs;
            $scope.bugs_with_no_points = data.bugs_with_no_points;
            $scope.latest_change_time = data.latest_change_time;
            $scope.sprint = data.sprint;
            $scope.total_points = data.total_points;
            $scope.closed_points = data.closed_points;
            $scope.last_load = new Date();

            $rootScope.loading--;

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
    }
]);

ernestControllers.controller('AuthCtrl', ['$scope', '$cookies', '$http',
    function($scope, $cookies, $http) {
        $scope.creds = {login: '', password: ''};
        $scope.loggingIn = false;

        if ($cookies.username) {
            $scope.creds.login = $cookies.username;
        }

        $scope.startLogin = function() {
            $scope.loggingIn = true;
        }

        $scope.login = function() {
            $http.post('/api/login', $scope.creds)
                .success(function(err) {
                    $scope.creds.password = null;
                })
                .error(function(err) {
                    console.log(err);
                });
        };

        $scope.logout = function() {
            $http.post('/api/logout');
        };

        $scope.loggedIn = function() {
            return !!$cookies.username;
        };
    }
]);
