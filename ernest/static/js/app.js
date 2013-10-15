'use strict';


// Declare app level module which depends on filters, and services
var ernest = angular.module('ernest', [
    'ngRoute',
    'ngResource',
    'ernest.filters',
    'ernest.services',
    'ernest.directives',
    'ernest.controllers'
]);

ernest.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/', {
        templateUrl: 'partials/home.html',
        controller: 'HomeCtrl'
    });
    $routeProvider.when('/projects', {
        templateUrl: 'partials/project-list.html',
        controller: 'ProjectListCtrl'
    });
    $routeProvider.when('/project/:projSlug', {
        templateUrl: 'partials/project-detail.html',
        controller: 'ProjectDetailCtrl',
    });
    $routeProvider.when('/project/:projSlug/:sprintSlug', {
        templateUrl: 'partials/sprint-detail.html',
        controller: 'SprintDetailCtrl',
    });
    $routeProvider.otherwise({
        redirectTo: '/'
    });
}]);

ernest.run(['$rootScope', function($rootScope) {
    $rootScope.loading = 0;
}]);
