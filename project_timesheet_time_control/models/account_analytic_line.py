from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _order = 'date_time desc'

    date_time = fields.Datetime(
        default=fields.Datetime.now,
        copy=False,
    )
    show_time_control = fields.Selection(
        selection=[("resume", "Resume"), ("stop", "Stop")],
        compute="_compute_show_time_control",
        help="Indicate which time control button to show, if any.",
    )
    notes=fields.Text("Extra Notes")

    # current_time=fields.Many2one('hr.timesheet.switch', "Current Time")
    running_time=fields.Float('Running Time',compute='_compute_running_timer_duration')

    @api.depends("date_time")
    def _compute_running_timer_duration(self):
        """Compute duration of running timer when stopped."""
        for one in self:
            curr_id = self.env['hr.timesheet.switch'].search([('running_timer_ids', '=', one.id)])
            one.running_time = one._duration(curr_id.date_time, one.date_time)


    @api.model
    def _eval_date(self, vals):
        if vals.get('date_time'):
            return dict(vals, date=fields.Date.to_date(vals['date_time']))
        return vals

    @api.model
    def _running_domain(self):
        """Domain to find running timesheet lines."""
        return [
            ("date_time", "!=", False),
            ("employee_id", "in", self.env.user.employee_ids.ids),
            ("project_id.allow_timesheets", "=", True),
            ("unit_amount", "=", 0),
        ]

    @api.model
    def _duration(self, start, end):
        """Compute float duration between start and end."""
        try:
            return (end - start).total_seconds() / 3600
        except TypeError:
            return 0

    @api.depends("employee_id", "unit_amount")
    def _compute_show_time_control(self):
        """Decide when to show time controls."""
        for one in self:
            if one.employee_id not in self.env.user.employee_ids:
                one.show_time_control = False
            elif one.unit_amount or not one.date_time:
                one.show_time_control = "resume"
            else:
                one.show_time_control = "stop"

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(list(map(self._eval_date, vals_list)))

    def write(self, vals):
        return super().write(self._eval_date(vals))

    def button_resume_work(self):
        """Create a new record starting now, with a running timer."""
        return {
            "name": _("Resume work"),
            "res_model": "hr.timesheet.switch",
            "target": "new",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
        }

    def button_end_work(self):
        end = fields.Datetime.to_datetime(
            self.env.context.get("stop_dt", datetime.now()))
        for line in self:
            if line.unit_amount:
                raise UserError(
                    _("Cannot stop timer %d because it is not running. "
                      "Refresh the page and check again.") %
                    line.id
                )
            line.unit_amount = line._duration(line.date_time, end)
            view = self.env.ref('project_timesheet_time_control.timesheet_wizard_form_view')
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_time_id': self.id,
            })
            return {
                'name': _('Add Notes?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.task.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }
        return True


class TaskWizard(models.TransientModel):

    _name = 'project.task.wizard'

    note=fields.Text("Task Description")
    # task_id=fields.Many2one('project.task','Task')
    time_id=fields.Many2one('account.analytic.line','Timesheet id')

    def set_activity(self):
        if self.time_id:
            values = {'notes': self.note,}
            self.time_id.write({'notes': self.note})

    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}