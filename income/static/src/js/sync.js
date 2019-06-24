
odoo.define('income.sync', function (require) {
    "use strict";
        var ListView = require('web.ListView');
        var Model = require('web.DataModel');
        ListView.include({
            render_buttons: function() {
                this._super.apply(this, arguments)
                if (this.$buttons) {
                    var btn = this.$buttons.find('.sync_button')
                    btn.on('click', this.proxy('do_sync'))
                }
           },
            do_sync: function() {
                new Model('salary.tracker.load')
                    .call('load_payroll_data', [[]])
                    .done(function(result) {
                        location.reload();
                    })
            }
        });
    });


//https://stackoverflow.com/questions/52206679/odoo-custom-button-in-the-header-of-odoo-tree-view-doesnt-trigger-python-functi/52207984