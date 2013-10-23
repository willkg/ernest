'use strict';


// Declare app level module which depends on filters, and services
var ernest = angular.module('ernest', [
    'ngRoute',
    'ngResource',
    'ngCookies',
]);

ernest.config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);

        $routeProvider.when('/', {
            templateUrl: '/partials/home.html',
            controller: 'HomeCtrl'
        });
        $routeProvider.when('/projects', {
            templateUrl: '/partials/project-list.html',
            controller: 'ProjectListCtrl'
        });
        $routeProvider.when('/project/:projSlug', {
            templateUrl: '/partials/project-detail.html',
            controller: 'ProjectDetailCtrl',
        });
        $routeProvider.when('/project/:projSlug/:sprintSlug', {
            templateUrl: '/partials/sprint-detail.html',
            controller: 'SprintDetailCtrl',
        });
        $routeProvider.otherwise({
            redirectTo: '/'
        });
    }
]);
