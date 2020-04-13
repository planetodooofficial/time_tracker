{
    'name': 'Time Track',
    'version': '13.0.1.0.0',
    'summary': 'Time Track',
    'description': """odoo Time Track""",
    'author': 'Planet Odoo',
    'website': 'http://www.planet-odoo.com/',
    'depends': ['base','project','hr_timesheet'],
    'data': [
            'security/ir.model.access.csv',
            'view/timesheet_wizard_view.xml',
            'view/ticket_start_stop_view.xml',

                  ],
    'images': [],


    'installable': True,
    'application': False,
}