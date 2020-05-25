
{
  "name"                 :  "Odoo Project Team Management",
  "category"             :  "Project",
  "version"              :  "13.0.1",
  "sequence"             :  1,
  "author"               :  "Planet-Odoo",
  "website"              :  "http://www.planet-odoo.com/",
  "description"          :  """Odoo Project Team Management""",
  "depends"              :  [
                             'project','hr',
                            ],
  "data"                 :  [
                             'security/project_security.xml',
                             'security/ir.model.access.csv',
                             'views/wk_team_view.xml',
                             'views/project_team_view.xml',
                            ],
  "demo"                 :  [
                             'data/data.xml',
                             'data/demo_data.xml',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  # "pre_init_hook"        :  "pre_init_check",
}