
from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    closed = fields.Boolean(
        help="Tasks in this stage are considered closed.",
        default=False,
    )
