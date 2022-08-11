from odoo import api, fields, models

class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    @api.model
    def _get_default_site_id(self):
        return self.env['jobsite'].sudo().search([('name', 'ilike', 'Inside Sales')])

    site_id = fields.Many2one(
        'jobsite', string='Job Site', index=True, tracking=10, default=_get_default_site_id,
        help="Linked site (optional). You can find a site by its Name.")