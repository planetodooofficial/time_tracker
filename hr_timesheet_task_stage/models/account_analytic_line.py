
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_task_closed = fields.Boolean(
        related='task_id.stage_id.closed',
    )

    def action_open_task(self):
        ProjectTaskType = self.env['project.task.type']

        for line in self.filtered('task_id.project_id'):
            if line.task_id.project_id:
                stage = ProjectTaskType.search([
                    ('project_ids', '=', line.task_id.project_id.id),
                    ('closed', '=', False)
                ], limit=1)
                if not stage:  # pragma: no cover
                    raise UserError(_(
                        'There isn\'t any stage with "Closed" unchecked.'
                        ' Please unmark any.'
                    ))
                line.task_id.write({
                    'stage_id': stage.id,
                })

    def action_close_task(self):
        ProjectTaskType = self.env['project.task.type']

        for line in self.filtered('task_id.project_id'):
            stage = ProjectTaskType.search([
                ('project_ids', '=', line.task_id.project_id.id),
                ('closed', '=', True)
            ], limit=1)
            if not stage:  # pragma: no cover
                raise UserError(_(
                    'There isn\'t any stage with "Closed" checked. Please'
                    ' mark any.'
                ))
            line.task_id.write({
                'stage_id': stage.id,
            })

    def action_toggle_task_stage(self):
        for line in self.filtered('task_id.project_id'):
            if line.is_task_closed:
                line.action_open_task()
            else:
                line.action_close_task()
