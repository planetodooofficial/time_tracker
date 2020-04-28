from odoo import api, models,_
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "hr.timesheet.time_control.mixin"]

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
        if self.user_id.id==user.id:
            result["context"].update({
                "default_project_id": self.project_id.id,
            })
        else:
            raise UserError(_("This Task is assigned to different user")
            )
        return result
