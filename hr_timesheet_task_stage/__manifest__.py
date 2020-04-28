
{
    'name': 'Task Log: Open/Close Task',
    'version': '12.0.1.1.0',
    'category': 'Operations/Timesheets',
    'website': 'www.planet-odoo.com',
    'author':
        'planet-odoo'
,
    'installable': True,
    'application': False,
    'summary': 'Open/Close task from corresponding Task Log entry',
    'depends': [
        'hr_timesheet',
        'project_stage_closed',
    ],
    'data': [
        'views/account_analytic_line.xml',
    ],
}
