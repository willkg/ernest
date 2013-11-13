var assert = chai.assert;

/* This is almost like the promise that comes from the requests service,
/* but it runs kind of syncronously in a way that helps tests. */
function MockRequestPromise() {
    this.callbacks = [];
    this.$promise = this;
    this.promise = this;
}
MockRequestPromise.prototype.then = function(cb) {
    this.callbacks.push(cb);
};
MockRequestPromise.prototype.thenAfterResolve = function(cb) {
    cb(this.resolvedWith);
};
MockRequestPromise.prototype.resolve = function(data) {
    this.resolvedWith = data;
    this.callbacks.forEach(function(cb) {
        cb(data);
    });
    this.then = this.thenAfterResolve;
};


describe('ernest controllers', function() {

    beforeEach(module('ernest'));

    describe('ProjectListCtrl', function(){
        var scope, ctrl, emitSpy, mockApi;

        beforeEach(inject(function($rootScope, $controller, $q) {
            mockApi = {
                query: sinon.stub(),
                queryDeferred: new MockRequestPromise()
            };
            mockApi.query.returns(mockApi.queryDeferred);

            scope = $rootScope.$new();
            emitSpy = sinon.spy(scope, '$emit');
            ctrl = $controller('ProjectListCtrl', {
                $scope: scope,
                Api: mockApi
            });
        }));

        afterEach(function() {
            emitSpy.restore();
        });


        it('should fetch projects from the API.', function() {
            mockApi.queryDeferred.resolve({
                projects: ['some', 'projects'],
            });
            assert.deepEqual(scope.projects, ['some', 'projects']);
        });

        it('should emit loading events', function() {
            assert(emitSpy.calledWith('loading+'));
            mockApi.queryDeferred.resolve({projects: []});
            assert(emitSpy.calledWith('loading-'));
        });

    });

    describe('ProjectDetailCtrl', function() {
        var scope, ctrl, emitSpy, mockApi;

        beforeEach(inject(function($rootScope, $controller, $q) {
            mockApi = {
                get: sinon.stub(),
                getDeferred: new MockRequestPromise(),
            };
            mockApi.get.returns(mockApi.getDeferred);

            scope = $rootScope.$new();
            emitSpy = sinon.spy(scope, '$emit');
            ctrl = $controller('ProjectDetailCtrl', {
                $scope: scope,
                $routeParams: {projSlug: 'support'},
                Api: mockApi,
            });
        }));

        afterEach(function() {
            emitSpy.restore();
        });

        it('should fetch a project from the API', function() {
            assert(mockApi.get.calledWith({projSlug: 'support'}));
            mockApi.getDeferred.resolve({
                project: 'A project',
                sprints: ['some', 'sprints'],
            });
            assert.equal(scope.project, 'A project');
            assert.deepEqual(scope.sprints, ['some', 'sprints']);
        });

        it('should emit loading events', function() {
            assert(emitSpy.calledWith('loading+'));
            mockApi.getDeferred.resolve({project: {}, sprints: []});
            assert(emitSpy.calledWith('loading-'));
        });
    });

    describe('SprintDetailCtrl', function() {
        var scope, ctrl, emitSpy, mockApi;

        var mockData = {
            bugs: [],
            bugs_with_no_points: 0,
            latest_change_time: new Date(),
            sprint: {},
            total_points: 4,
            closed_points: 2,
            next_sprint: 'a sprint',
            prev_sprint: 'another sprint',
            total_bugs: 2,
            closed_bugs: 1,
            priority_breakdown: 'a breakdown',
        };

        beforeEach(inject(function($rootScope, $controller, $q) {
            mockApi = {
                get: sinon.stub(),
                getDeferred: new MockRequestPromise(),
            };
            mockApi.get.returns(mockApi.getDeferred);

            scope = $rootScope.$new();
            emitSpy = sinon.spy(scope, '$emit');
            ctrl = $controller('SprintDetailCtrl', {
                $scope: scope,
                $routeParams: {projSlug: 'support', sprintSlug: 'sprint1'},
                Api: mockApi,
            });
        }));

        afterEach(function() {
            emitSpy.restore();
        });

        it('should fetch a sprint from the API', function() {
            assert(mockApi.get.calledWith({projSlug: 'support', sprintSlug: 'sprint1'}));
            mockApi.getDeferred.resolve(mockData);

            for (var key in mockData) {
                assert.equal(scope[key], mockData[key]);
            }
        });

        it('should emit loading events', function() {
            assert(emitSpy.calledWith('loading+'));
            mockApi.getDeferred.resolve({sprint: {}, sprints: []});
            assert(emitSpy.calledWith('loading-'));
        });

        it('should responsd to login events', function() {
            scope.refresh = sinon.spy();
            scope.$emit('login', 'alice@example.com');
            assert.ok(scope.refresh.calledOnce);
        });

        it('should responsd to logout events', function() {
            scope.refresh = sinon.spy();
            scope.$emit('logout', 'alice@example.com');
            assert.ok(scope.refresh.calledOnce);
        });

        describe('bugSort', function() {
            it('should treat priority -- as P6', function() {
                scope.bugSortBy.key = 'priority';
                assert.equal(scope.bugSort({priority: '--'}), 'P6');
            });

            it('should pull out real names from assignee', function() {
                scope.bugSortBy.key = 'assigned_to';
                var assignee = {assigned_to: {real_name: 'Alice Gregory'}};
                assert.equal(scope.bugSort(assignee), 'Alice Gregory');
            });
        });
    });

    describe('AuthCtrl', function() {
        var scope, ctrl, $httpBackend, mockCookies, broadcastSpy;

        beforeEach(inject(function($rootScope, $controller, _$httpBackend_) {
            $httpBackend = _$httpBackend_;
            scope = $rootScope.$new();
            broadcastSpy = sinon.spy(scope, '$broadcast');
            mockCookies = {username: '"bob@example.com"'};

            ctrl = $controller('AuthCtrl', {
                $rootScope: scope,
                $scope: scope,
                $cookies: mockCookies
            });
        }));

        afterEach(function() {
            broadcastSpy.restore();
        });

        it('should get a username from cookies', function() {
            assert.equal(scope.creds.login, 'bob@example.com');
        });

        describe('login', function() {
            it('should make a request to the server.', function() {
                $httpBackend.expectPOST('/api/login').respond();
                scope.login();
                $httpBackend.flush();
            });

            it('should clear out the password', function() {
                $httpBackend.expectPOST('/api/login').respond();
                scope.login();
                $httpBackend.flush();
            });

            it('should broadcast a login event', function() {
                scope.creds.login = 'alice@example.com';
                $httpBackend.expectPOST('/api/login').respond();
                scope.login();
                $httpBackend.flush();
                assert(broadcastSpy.calledWith('login', 'alice@example.com'));
            });
        });

        describe('logout', function() {
            it('should make a request to the server.', function() {
                $httpBackend.expectPOST('/api/logout').respond();
                scope.logout();
                $httpBackend.flush();
            });

            it('should broadcast a logout event', function() {
                $httpBackend.expectPOST('/api/logout').respond();
                scope.logout();
                $httpBackend.flush();
                assert(broadcastSpy.calledWith('logout'));
            });
        });

        describe('loggedIn', function() {
            it('should be true at first', function() {
                assert.ok(scope.loggedIn());
            });

            it('should be false after logging out', function() {
                $httpBackend.expectPOST('/api/logout').respond();
                scope.logout();
                $httpBackend.flush();
                // Normally the server would clear the cookie, so mock that.
                mockCookies.username = '';
                assert.notOk(scope.loggedIn());
            });

            it('should be true after logging out and then logging in.', function() {
                $httpBackend.expectPOST('/api/logout').respond();
                scope.logout();
                $httpBackend.flush();

                $httpBackend.expectPOST('/api/login').respond();
                scope.creds.username = 'alice@example.com';
                scope.login();
                $httpBackend.flush();
                // Normally the server would set the cookie, so mock that.
                mockCookies.username = 'alice@example.com';
                assert.ok(scope.loggedIn());
            });
        });
    });

    describe('LoadingCtrl', function() {
        var scope, ctrl;

        beforeEach(inject(function($rootScope, $controller) {
            scope = $rootScope.$new();

            ctrl = $controller('LoadingCtrl', {
                $rootScope: scope,
                $scope: scope,
            });
        }));

        it('should set loading to 0 initially', function() {
            assert.equal(scope.loading, 0);
        });

        it('should increment loading when a loading+ event is emitted', function() {
            scope.$emit('loading+');
            assert.equal(scope.loading, 1);
        });

        it('should decrement loading when a loading- event is emitted', function() {
            // loading- before loading+ is an error, so call both.
            scope.$emit('loading+');
            scope.$emit('loading-');
            assert.equal(scope.loading, 0);
        });

        it('should throw an error when there are more loading- than loading+', function() {
            try {
                scope.$emit('loading-');
                assert(false, 'An error should have been thrown.');
            } catch(e) {
                assert.match(e.message, /.*loading\-.*/);
            }
        });

    });

});
