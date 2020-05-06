odoo.define('project_timesheet_time_control.timer', function (require) {
"use strict";
var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var time = require('web.time');
var FieldManagerMixin = require('web.FieldManagerMixin');

var _t = core._t;

//  $(document).on('click','#timer', function(){
//  if ($(this).hasClass('btn-secondary'))
//  { $(this).removeClass('btn-secondary');
//    $(this).addClass('btn-primary');
//  }
//    });

var TimeCounter  = AbstractField.extend({

        willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'account.analytic.line',
            method: 'search_read',
            domain:  [['task_id', '=', this.res_id], ['user_id', '=', self.record.context['uid']]],
        }).then(function (result) {
            if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.duration = 0;
                _.each(result, function (data) {
                    self.duration += data.date_stop ?
                        self._getDateDifference(data.date_time, data.date_stop):
                        self._getDateDifference(time.auto_str_to_date(data.date_time), currentDate);
                });
            }
        });
        return $.when(this._super.apply(this, arguments), def);
    },
    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },
    isSet: function () {
        return true;
    },
    _getDateDifference: function (date_time, date_stop) {
        return moment(date_stop).diff(moment(date_time));
    },

    _render: function () {
        this._startTimeCounter();
    },
    _startTimeCounter: function () {
        var self = this;
        clearTimeout(this.timer);
        if (this.record.data.is_user_working) {
            this.timer = setTimeout(function () {
                self.duration += 1000;
                self._startTimeCounter();
            }, 1000);
        }
         else {
            clearTimeout(this.timer);
        }
        this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
    },
});
field_registry.add('timesheet_uoms', TimeCounter);
});