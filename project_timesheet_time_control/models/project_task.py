from odoo import api, models,_,fields
from datetime import datetime
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "hr.timesheet.time_control.mixin"]

    task_timer = fields.Boolean(string='Timer', default=False)
    is_user_working = fields.Boolean(
        'Is Current User Working',compute='_compute_is_user_working',
        help="Technical field indicating whether the current user is working. ")
    duration = fields.Float(
        'Real Duration', compute='_compute_duration', store=True)
    # task_timer = fields.Boolean()

    @api.model
    def _relation_with_timesheet_line(self):
        return "task_id"

    @api.depends("project_id.allow_timesheets", "timesheet_ids.employee_id",
                 "timesheet_ids.unit_amount")
    def _compute_show_time_control(self):
        result = super()._compute_show_time_control()
        for task in self:
            # Never show button if timesheets are not allowed in project
            if not task.project_id.allow_timesheets:
                task.show_time_control = False
        return result

    def button_start_work(self):
        user=self.env.user
        result = super().button_start_work()
        self.write({'task_timer': True})
        if self.task_timer:
            self.write({'is_user_working': True})
            if self.user_id.id==user.id:
                result["context"].update({
                    "default_project_id": self.project_id.id,
                })
            else:
                raise UserError(_("This Task is assigned to different user")
                )
            return result

    def _compute_duration(self):
        self

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.task_timer:
                order.is_user_working = True
            else:
                order.is_user_working = False

    @api.model
    @api.constrains('task_timer')
    def toggle_start(self):
        if self.task_timer is True:
            self.write({'is_user_working': True})
            time_line = self.env['account.analytic.line']
            # for time_sheet in self:
            #     time_line.create({
            #         'name': self.env.user.name + ': ' + time_sheet.name,
            #         'task_id': time_sheet.id,
            #         'user_id': self.env.user.id,
            #         'project_id': time_sheet.project_id.id,
            #         'date_start': datetime.now(),
            #     })
        else:
            self.write({'is_user_working': False})
            time_line_obj = self.env['account.analytic.line']
            domain = [('task_id', 'in', self.ids), ('date_end', '=', False)]
            # for time_line in time_line_obj.search(domain):
            #     time_line.write({'date_end': fields.Datetime.now()})
            #     if time_line.date_end:
            #         diff = fields.Datetime.from_string(time_line.date_end) - fields.Datetime.from_string(
            #             time_line.date_start)
            #         time_line.timer_duration = round(diff.total_seconds() / 60.0, 2)
            #         time_line.unit_amount = round(diff.total_seconds() / (60.0 * 60.0), 2)
            #     else:
            #         time_line.unit_amount = 0.0
            #         time_line.timer_duration = 0.0
