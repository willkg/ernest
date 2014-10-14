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

ernest.controller('ProjectDetailCtrl', ['$scope', '$routeParams', '$cacheFactory', 'Api',
    function($scope, $routeParams, $cacheFactory, Api) {
        $scope.bugSortBy = {key: 'target_milestone', reverse: true};
        $scope.bugSort = function(bug) {
            var val = bug[$scope.bugSortBy.key];
            if ($scope.bugSortBy.key === 'target_milestone') {
                if (val === '---' || val === 'Future') {
                    val = '\0';
                } else {
                    // Sorting by target milestone is actually target
                    // milestone then priority
                    val = bug.target_milestone + '::' + bug.priority;
                }
            } else if ($scope.bugSortBy.key === 'priority' && val === '--') {
                val = 'P6';
            } else if ($scope.bugSortBy.key === 'assigned_to') {
                if (bug.mine) {
                    // '\0' aka the null character will be sorted before
                    // anything else. It's kind of like -Infinity for strings.
                    val = '\0';
                } else {
                    val = val.real_name;
                }
            }
            return val;
        };

        function getData() {
            $scope.$emit('loading+');

            var p = Api.get($routeParams).$promise.then(
                function(data) {
                    $scope.project = data.project;
                    $scope.sprints = data.sprints;
                    $scope.is_admin = data.is_admin;
                    $scope.trackers = data.trackers;
                    $scope.$emit('loading-');
                },
                function(error) {
                    console.log('ERNEST ERROR: ' + error);
                    $scope.$emit('loading-');
                });
            return p;
        }

        $scope.refresh = function() {
            var url = '/api/project/' + $routeParams.projSlug;
            $cacheFactory.get('$http').remove(url);
            return getData();
        };

        $scope.$on('newSprint', function() { $scope.refresh(); });
        $scope.$on('login', function() { $scope.refresh(); });
        $scope.$on('logout', function() { $scope.refresh(); });

        getData();
    }
]);

ernest.controller('SprintNewCtrl', ['$scope', '$routeParams', '$http',
    function($scope, $routeParams, $http) {
        $scope.newSprint = {name: ''};

        $scope.createSprint = function() {
            var url = '/api/project/' + $routeParams.projSlug;
            $scope.$emit('loading+');
            $http.post(url, $scope.newSprint)
                .success(function(err) {
                    $scope.$emit('newSprint');
                    $scope.$emit('loading-');
                    $scope.newSprint = {name: ''};
                })
                .error(function(err) {
                    console.log(err);
                    $scope.$emit('loading-');
                });
        };
    }
]);

ernest.controller('SprintDetailCtrl', ['$scope', '$routeParams', '$http', '$cacheFactory', 'Api', 'localStorageService',
    function($scope, $routeParams, $http, $cacheFactory, Api, localStorageService) {
        $scope.showClosed = true;
        $scope.showNonStarred = true;

        $scope.bugSortBy = {key: 'priority', reverse: false};
        $scope.bugSort = function(bug) {
            var val = bug[$scope.bugSortBy.key];
            if ($scope.bugSortBy.key === 'priority' && val === '--') {
                val = 'P6';
            } else if ($scope.bugSortBy.key === 'assigned_to') {
                if (bug.mine) {
                    // '\0' aka the null character will be sorted before
                    // anything else. It's kind of like -Infinity for strings.
                    val = '\0';
                } else {
                    val = val.real_name;
                }
            }
            return val;
        };

        $scope.isClosed = function(val) {
            // Bugs are "closed" if they're either resolved or
            // verified.
            return (val.toLowerCase() === 'resolved'
                    || val.toLowerCase() === 'verified');
        };

        $scope.isJeopardyWarning = function(val) {
            return val === 'warning';
        };

        $scope.isJeopardyError = function(val) {
            return val === 'error';
        };

        $scope.isEstimated = function(val) {
            // Points field can be a number or null. Numbers indicate
            // it was estimated and null indicates it hasn't been
            // estimated.
            return val != null;
        };

        $scope.bugFilter = function(bug) {
            if (!$scope.showClosed && $scope.isClosed(bug.status)) {
                return false;
            }
            if (!$scope.showNonStarred && bug.star === '0') {
                return false;
            }
            return true;
        };

        $scope.updateSprint = function() {
            var sprint = $scope.sprint;
            var proj = sprint.project;
            var url = '/api/project/' + proj.slug + '/' + sprint.slug;

            var data = {
                start_date: sprint.start_date,
                end_date: sprint.end_date,
                notes: sprint.notes,
                postmortem: sprint.postmortem
            };

            $scope.$emit('loading+');
            $http.post(url, data)
                .success(function(err) {
                    $scope.$emit('updateSprint');
                    $scope.$emit('loading-');
                })
                .error(function(err) {
                    console.log(err);
                    $scope.$emit('loading-');
                });
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

        $scope.changeShowHideClosed = function() {
            if ($scope.showClosed) {
                $scope.showClosed = false;
                $scope.show_hide_closed = 'Show closed';
            } else {
                $scope.showClosed = true;
                $scope.show_hide_closed = 'Hide closed';
            }
        };

        $scope.changeShowHideNonStarred = function() {
            if ($scope.showNonStarred) {
                $scope.showNonStarred = false;
                $scope.show_hide_non_starred = 'Show non-starred';
            } else {
                $scope.showNonStarred = true;
                $scope.show_hide_non_starred = 'Hide non-starred';
            }
        };

        $scope.changeStar = function() {
            var bug = this.bug;

            if (bug.star == '1') {
                localStorageService.set('star' + bug.id, '1');
            } else {
                localStorageService.remove('star' + bug.id);
            }
        };

        $scope.changeSprint = function() {
            var sprint = $scope.sprint;
            var proj = sprint.project;
            if (!sprint || !proj) {
                return;
            }
            var url = '/api/project/' + proj.slug + '/' + sprint.slug;

            $scope.$emit('loading+');
            $http.post(url, $scope.sprintNotes)
                .success(function(err) {
                    $scope.$emit('loading-');
                    $scope.newSprint = {name: ''};
                })
                .error(function(err) {
                    console.log(err);
                    $scope.$emit('loading-');
                });
        };

        function getData() {
            $scope.$emit('loading+');

            var p = Api.get($routeParams).$promise.then(
                function(data) {
                    $scope.$emit('loading-');

                    $scope.project = data.project;
                    $scope.is_admin = data.is_admin;

                    $scope.allBugs = data.bugs;
                    $scope.openBugs = data.bugs.filter(function(bug) {
                        return (bug.status !== 'VERIFIED' && bug.status !== 'RESOLVED');
                    });

                    if ($scope.showClosed) {
                        $scope.bugs = $scope.allBugs;
                        $scope.show_hide_closed = 'Hide closed';
                    } else {
                        $scope.bugs = $scope.openBugs;
                        $scope.show_hide_closed = 'Show closed';
                    }

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
                    $scope.points_breakdown = data.points_breakdown;
                    $scope.component_breakdown = data.component_breakdown;
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
                },
                function(error) {
                    // FIXME - should show an error here
                    console.log('ERNEST ERROR: ' + error);
                    $scope.$emit('loading-');
                    $scope.last_load = new Date();
                });

            if ($scope.showClosed) {
                $scope.show_hide_closed = 'Hide closed';
            } else {
                $scope.show_hide_closed = 'Show closed';
            }

            if ($scope.showNonStarred) {
                $scope.show_hide_non_starred = 'Hide non-starred';
            } else {
                $scope.show_hide_non_starred = 'Show non-starred';
            }

            return p;
        }

        getData();
    }
]);

ernest.controller('BugzillaDetailCtrl', ['$scope', '$routeParams', '$cacheFactory', 'BugApi',
    function($scope, $routeParams, $cacheFactory, BugApi) {
        $scope.bugSortBy = {key: 'priority', reverse: false};
        $scope.bugSort = function(bug) {
            var val = bug[$scope.bugSortBy.key];
            if ($scope.bugSortBy.key === 'priority' && val === '--') {
                val = 'P6';
            } else if ($scope.bugSortBy.key === 'assigned_to') {
                if (bug.mine) {
                    // '\0' aka the null character will be sorted before
                    // anything else. It's kind of like -Infinity for strings.
                    val = '\0';
                } else {
                    val = val.real_name;
                }
            }
            return val;
        };

        $scope.isClosed = function(val) {
            // Bugs are "closed" if they're either resolved or
            // verified.
            return (val.toLowerCase() === 'resolved'
                    || val.toLowerCase() === 'verified');
        };

        $scope.isEstimated = function(val) {
            // Points field can be a number or null. Numbers indicate
            // it was estimated and null indicates it hasn't been
            // estimated.
            return val != null;
        };

        $scope.refresh = function() {
            var bug = $scope.bug;
            if (!bug) {
                return;
            }
            var url = '/api/bugzilla/bug/' + bug.id;
            $cacheFactory.get('$http').remove(url);
            return getData();
        };

        $scope.$on('login', function() { $scope.refresh(); });
        $scope.$on('logout', function() { $scope.refresh(); });

        function getData() {
            $scope.$emit('loading+');

            var p = BugApi.get($routeParams).$promise.then(function(data) {
                $scope.$emit('loading-');

                $scope.bug = data.bug;
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
