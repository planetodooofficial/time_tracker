
from odoo import api, models


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "hr.timesheet.time_control.mixin",'portal.mixin',
                'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.model
    def _relation_with_timesheet_line(self):
        return "project_id"

    @api.depends("allow_timesheets")
    def _compute_show_time_control(self):
        result = super()._compute_show_time_control()
        for project in self:
            # Never show button if timesheets are not allowed in project
            if not project.allow_timesheets:
                project.show_time_control = False
        return result

    def button_start_work(self):
        result = super().button_start_work()
        # When triggering from project is usually to start timer without task
        result["context"].update({
            "default_task_id": False,
        })
        return result

    def action_timesheet_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        # template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].search([('name', '=', 'Timesheet Report')])
        if template.lang:
            lang = template._render_template(template.lang, 'project.project', self.ids[0])
        ctx = {
            'default_model': 'project.project',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            # 'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            # 'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }