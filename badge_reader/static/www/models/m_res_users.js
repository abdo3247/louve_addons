'use strict';


angular.module('starter').factory('ResUsersModel', ['$q', 'jsonRpc', function ($q, jsonRpc) {

    return {
        GetByBarcode: function(barcode) {
            return jsonRpc.searchRead('res.users', [['barcode', '=', barcode]], ['id', 'partner_id']).then(function (user_res) {
                return user_res.records;
            });
        }
    };
}]);
