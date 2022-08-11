import traceback

from odoo import api, fields, models, _
import requests
import logging
import json
_logger = logging.getLogger(__name__)

class JobsiteStage(models.Model):
    _name = 'jobsite_stage'
    name = fields.Char(string="Name")


class JobsiteGodown(models.Model):
    _name = 'jobsite.godown'
    name = fields.Char(string="Name")
    state_code = fields.Integer(string="State Code")
    address = fields.Char(string="Godown Address")
    jobsite_id = fields.Many2one('jobsite', string='Jobsite')
    beta_id = fields.Integer()


class Jobsite(models.Model):
    _name = 'jobsite'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin']
    _description = "Jobsite"
    name = fields.Char(string='Site Name', required=True, translate=True, tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Jobsite Already Exists'),
    ]

    siteteam = fields.Many2one(comodel_name='crm.team', string='Team')
    vl_date = fields.Date('VL Date', help="Visit Lead Due Date (VL Date)")
    godown_ids = fields.Many2many('jobsite.godown')
    status = fields.Selection([
        ('Virgin', 'Virgin'),
        ('Active', 'Active'),
        ('Closed', 'Closed'),
    ], string="Status",
        required=True, default='Virgin')
    note = fields.Text(string='Description')
    active = fields.Boolean(string='isActive', default=True, tracking=True)

    status = fields.Selection([
        ('0', 'ACTIVE'),
        ('1', 'CLOSED'),
        ('2', 'VIRGIN'),
    ], string='Status')

    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    stage_id = fields.Many2one("jobsite_stage", string="Stage")
    latitude = fields.Float(string='Geo Latitude', digits=(20, 14))
    longitude = fields.Float(string='Geo Longitude', digits=(20, 14))
    marker_color = fields.Char(string='Marker Color', default='red', required=True)
    user_id = fields.Many2one(
        'res.users', string='Salesperson', default=lambda self: self.env.user, index=True, tracking=True)

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result

    def geo_localize(self):
        for lead in self.with_context(lang='en_US'):
            result = self._geo_localize(
                street=lead.street,
                zip=lead.zip,
                city=lead.city,
                state=lead.state_id.name,
                country=lead.country_id.name,
            )

            if result:
                lead.write(
                    {
                        'latitude': result[0],
                        'longitude': result[1],
                    }
                )

        return True

    @api.onchange('zip')
    def sendToBeta(self):
        if (self.zip != False):
            nearest_godown = self._get_nearest_godown(self.zip)
            godown_names = [entry['godown_name'] for entry in nearest_godown]
            self.godown_ids = self.env['jobsite.godown'].sudo().search([('name', 'in', godown_names)])

    def _get_nearest_godown(self, pincode):
        endpoint = "https://youngmanbeta.com/nearestGodown?pincode=" + str(pincode)
        try:
            response = requests.get(endpoint, verify=False)
            return response.json()
        except requests.HTTPError:
            error_msg = _("Could not fetch nearest Godown. Remote server returned status ???")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
        except Exception as e:
            error_msg = _("Some error occurred while fetching nearest Godown")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
        finally:
            traceback.format_exc()



    # def _send_nearest_godown(self, id):
    #     endpoint = "https://youngmanbeta.com/nearestGodown?pincode=" + str(id)
    #     try:
    #         response = requests.get(endpoint, verify=False)
    #     except requests.HTTPError:
    #         error_msg = _("Could not fetch nearest Godown. Remote server returned status ???")
    #         raise self.env['res.config.settings'].get_config_warning(error_msg)
    #     except Exception as e:
    #         error_msg = _("Some error occurred while fetching nearest Godown")
    #         raise self.env['res.config.settings'].get_config_warning(error_msg)
    #     finally:
    #         traceback.format_exc()

# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     marker_color = fields.Char(
#         string='Marker Color', default='red', required=True)
