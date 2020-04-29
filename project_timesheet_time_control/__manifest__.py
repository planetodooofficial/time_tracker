{
    'name': 'Project timesheet time control',
    'version': '13.1.0',
    'category': 'Project',
    'author': 'Planet-odoo',
    'depends': [
        'hr_timesheet_task_stage',
        'hr_timesheet_task_domain',
        'web_ir_actions_act_multi',
        'web_ir_actions_act_view_reload',
    ],
    'data': [
        'views/account_analytic_line_view.xml',
        'views/project_project_view.xml',
        'views/project_task_view.xml',
        'views/report_project_timesheet.xml',
        'wizards/hr_timesheet_switch_view.xml',
    ],
    'installable': True,
    'post_init_hook': 'post_init_hook',
}
