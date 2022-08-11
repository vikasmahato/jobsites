# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'JobSite',
    'version': '2.0',
    'category': 'Sales/CRM',
    'summary': 'A pool of new opportunities',
    'sequence': -100,
    'description': """
        It is an entity of location type which generates new leads.
    """,
    'depends': ['mail', 'crm', 'web_google_maps'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/jobsite_list.xml',
        'views/jobsite_iwm.xml',
        'views/jobsite.xml',
        'views/jobsite_lead.xml',
        'views/jobsite_map.xml',
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {},
}
