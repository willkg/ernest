'use strict';

/* Controllers */


angular.module('ernest.controllers', []).

    controller('HomeCtrl', [function() {

    }])

    .controller('ProjectListCtrl', ['$rootScope', '$scope', 'Api',
        function($rootScope, $scope, Api) {
            $rootScope.loading++;

            Api.query().$promise.then(function(data) {
                $scope.projects = data.projects;

                $rootScope.loading--;
            });
        }
    ])

    .controller('ProjectDetailCtrl', ['$rootScope', '$scope', '$routeParams', 'Api',
        function($rootScope, $scope, $routeParams, Api) {
            $rootScope.loading++;
            
            Api.get($routeParams).$promise.then(function(data) {
                $scope.project = data.project;
                $scope.sprints = data.sprints;

                $rootScope.loading--;
            });
        }
    ])

    .controller('SprintDetailCtrl', ['$rootScope', '$scope', '$routeParams', 'Api',
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
  
