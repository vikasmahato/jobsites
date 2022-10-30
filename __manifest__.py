# -*- coding: utf-8 -*-

{
    'name': 'JobSite',
    'version': '4.0',
    'category': 'Sales/CRM',
    'summary': 'It is an entity of location type which generates new leads.',
    'description': """
        It is an entity of location type which generates new leads.
    """,
    'author': "Ajay",
    'website': "https://www.youngman.co.in/",
    'sequence': -100,

    'depends': ['mail', 'crm', 'web_google_maps'],

    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/jobsite.xml',
        'views/jobsite_map.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}
