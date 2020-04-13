odoo.define('siga_erp_custom.dashboard', function (require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var session = require('web.session');
var ajax = require('web.ajax');
var ActionManager = require('web.ActionManager');
var view_registry = require('web.view_registry');
var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');
var ControlPanelMixin = require('web.ControlPanelMixin');
var QWeb = core.qweb;

var _t = core._t;
var _lt = core._lt;

var HelpdeskDashboardView = AbstractAction.extend(ControlPanelMixin, {
    events: {
		'click .tech_ticket': 'action_tech_ticket',
		'click .func_ticket': 'action_func_ticket',
		'click .sup_ticket': 'action_sup_ticket',
	},
	init: function(parent, context) {
        this._super(parent, context);
        var helpdesk_data = [];
        var self = this;
        if (context.tag == 'siga_erp_custom.dashboard') {
            self._rpc({
                model: 'helpdesk.support.template',
                method: 'get_status_details',
            }, []).then(function(result){
                self.helpdesk_data = result[0]
            }).done(function(){
                self.render();
                self.href = window.location.href;
            });
        }
    },
    willStart: function() {
         return $.when(ajax.loadLibs(this), this._super());
    },
    start: function() {
        var self = this;

        return this._super();
    },
    render: function() {
        var super_render = this._super;
        var self = this;
        var hr_dashboard = QWeb.render('siga_erp_custom.dashboard', {
            widget: self,
        });
        $( ".o_control_panel" ).addClass( "o_hidden" );
        $(hr_dashboard).prependTo(self.$el);
        return hr_dashboard
    },
    reload: function () {
            window.location.href = this.href;
    },


     action_tech_ticket: function(event) {
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Technical Tickets"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.support',
            view_mode: 'kanban,form',
            view_type: 'form',
            views: [[false, 'kanban'],[false, 'form']],
            context: {},
            domain: [['category','=','technical']],
            target: 'current'
        },{on_reverse_breadcrumb: function(){ return self.reload();}})
    }
    ,action_func_ticket: function(event) {
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Functional Tickets"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.support',
            view_mode: 'kanban,form',
            view_type: 'form',
            views: [[false, 'kanban'],[false, 'form']],
            context: {},
            domain: [['category','=','functional']],
            target: 'current'
        },{on_reverse_breadcrumb: function(){ return self.reload();}})
    }
    ,action_sup_ticket: function(event) {
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Support Tickets"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.support',
            view_mode: 'kanban,form',
            view_type: 'form',
            views: [[false, 'kanban'],[false, 'form']],
            context: {},
            domain: [['category','=','support']],
            target: 'current'
        },{on_reverse_breadcrumb: function(){ return self.reload();}})
    }

});
core.action_registry.add('siga_erp_custom.dashboard', HelpdeskDashboardView);
return HelpdeskDashboardView
});