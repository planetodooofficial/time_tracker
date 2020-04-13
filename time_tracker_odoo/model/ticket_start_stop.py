from odoo import api,fields,models, _
from datetime import datetime
import re
from dateutil import relativedelta
from odoo.exceptions import ValidationError,UserError


class TicketStart(models.Model):

    _inherit = 'project.task'

    date_start=fields.Datetime("Start")
    date_stop=fields.Datetime("Stop")
    activity_description=fields.Char("Activity Description")
    active_timesheet=fields.Boolean('Timesheet Active')
    state = fields.Selection(string="States", selection=[('a1', 'Activity Stopped'),
                                                         ('a2', 'Activity Started'),
                                                          ],
                             default="a1", track_visibility='onchange', )
    duration = fields.Float(
        'Real Duration', store=True)

    task_timer = fields.Boolean()

    @api.depends('timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        for task in self:
            task.effective_hours = round(sum(task.timesheet_ids.mapped('unit_amount')), 2)
            if self.user_has_groups('siga_erp_custom.initial_planned_hrs_group'):
                if task.effective_hours > task.planned_hours:
                    raise UserError(_('Your Hours spend is more than Task Planned Hours .'))

    def default_get(self, fields_list):
        result = super(TicketStart, self).default_get(fields_list)
        if self.env.user.has_group('siga_erp_custom.timesheet_start_stop'):
            result.update({'active_timesheet': True})
        return result

    def start_ticket(self):
        if self.planned_hours <= 0:
            raise UserError(_('Fill the Planned Hours'))
        task=self.env['project.task'].search([])
        for item in task:
            if item.state == 'a2':
                raise UserError(_('Finished the ongoing activity first in %s,'%(item.number)))

        self.date_start = datetime.now()
        self.write({'state': 'a2'})

    def stop_ticket(self):
        self.date_stop = datetime.now()
        self.write({'state': 'a1'})
        date1 = datetime.strptime(str(self.date_start), '%Y-%m-%d %H:%M:%S.%f')
        date2 = datetime.strptime(str(self.date_stop), '%Y-%m-%d %H:%M:%S.%f')
        r = relativedelta.relativedelta(date2, date1)
        time_min=r.days*1440 + r.hours*60+r.minutes
        time= time_min/60

        if self.date_stop:
            view = self.env.ref('time_tracker_odoo.timesheet_wizard_form_view')
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_unit_amount': time,
                'default_date_start': self.date_start,
                'default_date_stop': self.date_stop,
                'default_task_id': self.id,
            })
            return {
                'name': _('Stop Activity?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.task.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }


class TicketWizard(models.TransientModel):

    _name = 'project.task.wizard'

    date=fields.Date("Date")
    emp_id=fields.Many2one("hr.employee", string="Employee")
    unit_amount=fields.Float("Duration")
    name=fields.Text("Task Description")
    date_start = fields.Datetime("Start")
    date_stop = fields.Datetime("Stop")
    task_id=fields.Many2one('project.task','Task')

    def set_activity(self):
        if self.task_id:
            values = {'name': self.name, 'unit_amount': self.unit_amount,'date_start':self.date_start,
                       'date_stop':self.date_stop,'account_id':1,}
            self.task_id.write({'timesheet_ids': [(0, 0, values)]})

    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class TimeStart(models.Model):

    _inherit = 'account.analytic.line'

    activity_description = fields.Char("Activity Description")
    date_start = fields.Datetime("Start Date")
    date_stop = fields.Datetime("End Date")
    # account_id=fields.Many2one('account.analytic.account','Analytic Account')

    @api.onchange('date_stop','date_start')
    def _onchange_stop_date(self):
        if self.date_stop and self.date_start:
            date1 = datetime.strptime(str(self.date_start), '%Y-%m-%d %H:%M:%S')
            date2 = datetime.strptime(str(self.date_stop), '%Y-%m-%d %H:%M:%S')
            # date3 = datetime.strptime(str(self.date_start), '%Y-%m-%d').date()
            # date4 = datetime.strptime(str(self.date_stop), '%Y-%m-%d').date()
            # r = relativedelta.relativedelta(date2, date1)
            # time_min =r.days*1440 + r.hours * 60 + r.minutes
            # time = time_min / 60
            # self.unit_amount = time
            delta = date2 - date1

            date_to_sec = ((delta.days*24)*60)*60

            sec = date_to_sec + delta.seconds

            sec_to_hours = (sec/60)/60

            self.unit_amount = sec_to_hours
