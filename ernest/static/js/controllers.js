'use strict';

/* Controllers */


var ernest = angular.module('ernest');

ernest.controller('HomeCtrl', [function() {}]);

ernest.controller('ProjectListCtrl', ['$scope', 'Api',
    function($scope, Api) {
        $scope.$emit('loading+');
        $scope.projects = [];

        Api.get().$promise.then(function(data) {
            $scope.projects = data.projects;

            $scope.$emit('loading-');
        });
    }
]);

ernest.controller('ProjectDetailCtrl', ['$scope', '$routeParams', '$http', '$cacheFactory', 'Api',
    function($scope, $routeParams, $http, $cacheFactory, Api) {
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
            var p = Api.get($routeParams).$promise
                .then(function(data) {
                    $scope.project = data.project;
                    $scope.sprints = data.sprints;
                    $scope.is_admin = data.is_admin;
                    $scope.trackers = data.trackers;
                    $scope.$emit('loading-');
                })
                .catch(function(error) {
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

        $scope.updateProject = function() {
            var params = {
                name: $scope.project.name,
                bugzilla_product: $scope.project.bugzilla_product,
                github_owner: $scope.project.github_owner,
                github_repo: $scope.project.github_repo
            };

            var url = '/api/project/' + $routeParams.projSlug;
            $scope.$emit('loading+');
            $http.post(url, params)
                .success(function(err) {
                    $scope.$emit('loading-');
                })
                .error(function(err) {
                    console.log(err);
                    $scope.$emit('loading-');
                });
        };
    }
]);

ernest.controller('SprintNewCtrl', ['$scope', '$routeParams', '$http',
    function($scope, $routeParams, $http) {
        $scope.newSprint = {sprintname: '', error: ''};

        $scope.createSprint = function() {
            var url = '/api/project/' + $routeParams.projSlug;
            if ($scope.newSprint.sprintname === '') {
                $scope.newSprint.error = 'Sprint must have a name.';
                return;
            }

            $scope.$emit('loading+');
            $http.post(url, $scope.newSprint)
                .success(function(err) {
                    $scope.$emit('newSprint');
                    $scope.$emit('loading-');
                    $scope.newSprint.sprintname = '';
                    $scope.newSprint.error = '';
                })
                .error(function(err) {
                    console.log(err);
                    $scope.newSprint.error = err.error;
                    $scope.$emit('loading-');
                });
        };
    }
]);

ernest.controller('SprintDetailCtrl', ['$scope', '$routeParams', '$http', '$q', '$cacheFactory', '$interval',
                                       'Api', 'GitHubRepoApi', 'localStorageService',
    function($scope, $routeParams, $http, $q, $cacheFactory, $interval, Api, GitHubRepoApi, localStorageService) {
        $scope.showClosed = true;
        $scope.showNonStarred = true;
        $scope.nobugs = false;

        $scope.autoRefreshInterval = null;
        $scope.enabledAutoRefresh = false;
        $scope.enable_disable_auto_refresh = 'Enable autorefresh';

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

        $scope.isClosed = function(bug) {
            // Bugs are "closed" if they're either resolved or
            // verified.
            return (bug.status.toLowerCase() === 'resolved'
                    || bug.status.toLowerCase() === 'verified');
        };

        $scope.isJeopardyWarning = function(bug) {
            return !$scope.isClosed(bug) && bug.jeopardy === 'warning';
        };

        $scope.isJeopardyError = function(bug) {
            return !$scope.isClosed(bug) && bug.jeopardy === 'error';
        };

        $scope.isEstimated = function(val) {
            // Points field can be a number or null. Numbers indicate
            // it was estimated and null indicates it hasn't been
            // estimated.
            return val != null;
        };

        $scope.bugFilter = function(bug) {
            if (!$scope.showClosed && $scope.isClosed(bug)) {
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

        $scope.changeEnabledAutoRefresh = function() {
            if ($scope.enabledAutoRefresh) {
                $scope.enabledAutoRefresh = false;
                if ($scope.autoRefreshInterval !== null) {
                    $interval.cancel($scope.autoRefreshInterval);
                    $scope.autoRefreshInterval = null;
                }
                $scope.enable_disable_auto_refresh = 'Enable autorefresh';
            } else {
                $scope.enabledAutoRefresh = true;
                $scope.autoRefreshInterval = $interval($scope.refresh, 10 * 60 * 1000);
                $scope.enable_disable_auto_refresh = 'Disable autorefresh';
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

            var prom = Api.get($routeParams).$promise
                .then(function (data) {
                    $scope.project = data.project;
                    $scope.is_admin = data.is_admin;
                    $scope.bugs = data.bugs;

                    if ($scope.showClosed) {
                        $scope.show_hide_closed = 'Hide closed';
                    } else {
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

                    if ($scope.bugs_with_no_points > 0 || $scope.total_points === 0) {
                        $scope.completionState = 'notready';
                    } else if ($scope.closed_points === $scope.total_points) {
                        $scope.completionState = 'done';
                    } else if ($scope.closed_points > $scope.total_points / 2) {
                        $scope.completionState = 'almost';
                    } else {
                        $scope.completionState = 'incomplete';
                    }

                    if ($scope.bugs.length === 0) {
                        $scope.nobugs = true;
                    } else {
                        $scope.nobugs = false;
                    }

                    var newPromise = null;

                    if (data.project.github_owner && data.project.github_repo) {
                        // If we have GitHub data, then execute an
                        // API request to get the list of pull
                        // requests.
                        var params = {owner: data.project.github_owner, repo: data.project.github_repo};
                        var githubP = GitHubRepoApi.get(params).$promise;
                        newPromise = githubP;
                    } else {
                        newPromise = $q.when([]);
                    }

                    return newPromise;
                })
                .then(function (ghData) {
                    // Handle the GitHubRepoApi promise
                    if (ghData !== undefined && ghData.length > 0) {
                        var bugToPR = {};
                        ghData.forEach(function (item) {
                            item.bugNum.forEach(function (num) {
                                var tmp = bugToPR[num] || [];
                                tmp.push(item);
                                bugToPR[num] = tmp;
                            });
                        });

                        $scope.bugs.forEach(function (bug) {
                            bug.pulls = bugToPR[bug.id] || [];
                        });
                    }

                    $scope.$emit('loading-');
                    $scope.last_load = new Date();
                })
                .catch(function(error) {
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

            if ($scope.enabledAutoRefresh) {
                $scope.enable_disable_auto_refresh = 'Disable autorefresh';
            } else {
                $scope.enable_disable_auto_refresh = 'Enable autorefresh';
            }
            return prom;
        }

        getData();
        // Refresh the data every 10 minutes. Since it does a GH API
        // request, we probably don't want to do it more often than
        // that.
        $scope.$on('$destroy', function() {
            if ($scope.autoRefreshInterval !== null) {
                $interval.cancel($scope.autoRefreshInterval);
            }
        });
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
