'use strict';

/* Directives */

var ernestDirectives = angular.module('ernest.directives', []);

ernestDirectives.directive('appVersion', ['version',
  function(version) {
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }
]);


ernestDirectives.directive('sortToggle', function() {
  return {
    restrict: 'E',
    replace: true,
    scope: {
      name: '=',
      value: '@'
    },

    template:
      '<span class="sort-toggle">' +
        '<button class="btn btn-mini" ng-click="changeSort(false)" ' +
         'ng-show="highlight() === 0">◇</button>' +
        '<button class="btn btn-mini" ng-click="changeSort(true)" ' +
         'ng-show="highlight() === 1">⬘</button>' +
        '<button class="btn btn-mini" ng-click="changeSort(false)" ' +
         'ng-show="highlight() === -1">⬙</button>' +
      '</span>',

    link: function($scope, element, attrs) {
      $scope.changeSort = function(reverse) {
        $scope.name.key = $scope.value;
        $scope.name.reverse = reverse;
      };
      $scope.highlight = function() {
        if ($scope.name.key === $scope.value) {
          return $scope.name.reverse ? -1 : 1;
        }
        return 0;
      }
    }
  };
});
