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
        'Real Duration',compute='_compute_duration', store=True)

    task_timer = fields.Boolean()
    is_user_working = fields.Boolean(
        'Is Current User Working',compute='_compute_is_user_working',
        help="Technical field indicating whether the current user is working. ")

    def _compute_duration(self):
        self

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (x.timer_status=='running')):
                order.is_user_working = True
            else:
                order.is_user_working = False

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

    user_timer_status = fields.Char(
        string='Timer Status',
        compute='_user_timer_status',
        help='Current user is working on this Issue',
    )

    def _update_time_spent(self):
        """Total project time on all completed timesheets"""
        total = 0.0
        for timesheet in self.timesheet_ids.search([
            ('timer_status', '=', 'stopped'),
            ('project_id', '=', self.project_id.id),
        ]):
            total += timesheet.unit_amount
        return total

    def _user_timer_status(self):
        clocked_in_count = self.timesheet_ids.search_count([
            ('timer_status', '=', 'running'),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_count > 0:
            self.user_timer_status = 'Running'
            return

        paused_count = self.timesheet_ids.search_count([
            ('timer_status', '=', 'paused'),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if paused_count > 0:
            self.user_timer_status = 'Paused'
            return

        self.user_timer_status = 'Stopped'

    def _prevent_multiple_clocked_in(self):

        clocked_in_somewhere = self.timesheet_ids.search_count([
            ('timer_status', '=', 'running'),
            ('user_id', '=', self.env.uid),
        ])
        if clocked_in_somewhere:
            raise UserError(_(
                'You are already working and can\'t record multiple timesheets at once.\n '
                'Check the "My Timers" filter and Stop other timer(s).'
            ))

    def timer_start(self):

        self._prevent_multiple_clocked_in()

        self.write({'is_user_working': True,
            'timesheet_ids': [(0, 0, {
                'name': 'Work In Progress',
                'date_start': datetime.now(),
                'timer_status': 'running',
                'account_id': self.project_id.analytic_account_id.id,
                'company_id': self.env.user.company_id.id,
                'user_id': self.env.uid,
                'project_id': self.project_id.id,
                # 'to_invoice': factor,
            })]
        })

    def _get_timesheet(self, status):
        """Get currently running timesheet to Pause / Stop timer"""
        if not self.project_id:
            raise UserError(_(
                'Please specify a project before closing Timesheet.'
            ))

        timesheet = self.timesheet_ids.search([
            ('timer_status', '=', status),
            ('project_id', '=', self.project_id.id),
            ('user_id', '=', self.env.uid),
        ])
        if not timesheet:
            raise UserError(_(
                'You have no "%s" timesheet! % status'
            ))
        if len(timesheet) > 1:
            raise UserError(_(
                'Multiple %s timesheets found for this Issue/Task. '
                'Resolve any %s "Work In Progress" timesheet(s) manually.' % (status, status)
            ))
        return timesheet

    def _get_current_total_time(self, timesheet):
        """
        When Pausing / Stopping timer, get time of
        current session plus any prior sessions
        """
        end = datetime.now()
        start = fields.Datetime.from_string(timesheet.date_start)
        duration = (end - start).total_seconds() / 3600.0
        return timesheet.full_duration + duration

    def timer_pause(self):
        timesheet = self._get_timesheet(status='running')
        current_total_time = self._get_current_total_time(timesheet)
        timesheet.write({
            'timer_status': 'paused',
            'full_duration': current_total_time,
        })
        self._user_timer_status()

    def timer_resume(self):
        self._prevent_multiple_clocked_in()
        timesheet = self._get_timesheet(status='paused')
        timesheet.write({
            'timer_status': 'running',
            'date_start': fields.Datetime.now(),
        })

    def timer_stop(self):
        """
        Wizard to close timesheet, but allow the user to
        edit the work description and closing time.
        """
        self.write({'is_user_working': False})
        timesheet = self._get_timesheet(status='running')

        current_total_time = self._get_current_total_time(timesheet)
        timesheet.write({
            'timer_status': 'stopped',
            'full_duration': current_total_time,
        })

        wizard_form = self.env.ref('time_tracker_odoo.timesheet_timer_wizard', False)
        Timer = self.env['timesheet_timer.wizard']

        new = Timer.create({
            'completed_timesheets': current_total_time,
            'full_duration': current_total_time,
            'timesheet_id': timesheet.id,
            # 'to_invoice': timesheet.to_invoice.id,
        })
        # self.write({'is_user_working': False})
        return {
            'name': 'Record Issue Timesheet Log',
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet_timer.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
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
    timer_status = fields.Selection(selection=[
        ('stopped', 'Stopped'),
        ('paused', 'Paused'),
        ('running', 'Running'),
        ],
        string='Timer Status')

    full_duration = fields.Float(
        'Time',
        default=0.0,
        help='Total and undiscounted amount of time spent on timesheet')

