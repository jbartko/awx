/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$scope', '$state', '$stateParams', 'PageRangeSetup', 'GetBasePath', 'DashboardHostsList',
	'generateList', 'PaginateInit', 'SetStatus', 'DashboardHostService', 'hosts', '$rootScope', 'SearchInit',
	function($scope, $state, $stateParams, PageRangeSetup, GetBasePath, DashboardHostsList, GenerateList, PaginateInit, SetStatus, DashboardHostService, hosts, $rootScope, SearchInit){
		var setJobStatus = function(){
			_.forEach($scope.hosts, function(value){
				SetStatus({
					scope: $scope,
					host: value
				});
			});
		};
		var generator = GenerateList,
			list = DashboardHostsList,
			defaultUrl = GetBasePath('hosts');
		$scope.hostPageSize = 10;
		$scope.editHost = function(id){
			$state.go('dashboardHosts.edit', {id: id});
		};
		$scope.toggleHostEnabled = function(host){
			DashboardHostService.setHostStatus(host, !host.enabled)
			.then(function(res){
				var index = _.findIndex($scope.hosts, function(o) {return o.id === res.data.id;});
				$scope.hosts[index].enabled = res.data.enabled;
			});
		};
		$scope.$on('PostRefresh', function(){
        	$scope.hosts = _.map($scope.hosts, function(value){
    			value.inventory_name = value.summary_fields.inventory.name;
    			value.inventory_id = value.summary_fields.inventory.id;
    			return value;
        	});
        	setJobStatus();
		});
		var cleanUpStateChangeListener = $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
             if (toState.name === "dashboardHosts.edit") {
                 $scope.rowBeingEdited = toParams.id;
                 $scope.listBeingEdited = "hosts";
             }
             else {
                 delete $scope.rowBeingEdited;
                 delete $scope.listBeingEdited;
             }
        });
        // Remove the listener when the scope is destroyed to avoid a memory leak
        $scope.$on('$destroy', function() {
            cleanUpStateChangeListener();
        });
		var init = function(){
			$scope.list = list;
			$scope.host_active_search = false;
			$scope.host_total_rows = hosts.results.length;
			$scope.hosts = hosts.results;
			setJobStatus();
			generator.inject(list, {mode: 'edit', scope: $scope});
			SearchInit({
		        scope: $scope,
		        set: 'hosts',
		        list: list,
		        url: defaultUrl
		    });
			PaginateInit({
				scope: $scope,
				list: list,
				url: defaultUrl,
				pageSize: 10
			});
            PageRangeSetup({
                scope: $scope,
                count: hosts.count,
                next: hosts.next,
                previous: hosts.previous,
                iterator: list.iterator
            });
			$scope.hostLoading = false;
			if($state.current.name === "dashboardHosts.edit") {
	            $scope.rowBeingEdited = $state.params.id;
	            $scope.listBeingEdited = "hosts";
	        }
			$scope.search(list.iterator);
		};
		init();
	}];