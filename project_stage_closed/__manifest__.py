
{
    'name': "Project Task Stage Closed",
    'summary': "Make the Closed flag on Task Stages available without "
               "installing sale_service""",
    'author': 'Planet-odoo,'
,
    'website': "www.planet-odoo.com",
    'category': 'Project Management',
    'version': '13.0.1.0.0',
    'depends': [
        'project',
    ],
    'data': [
        'views/task_stage.xml',
    ],
}
