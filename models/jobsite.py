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
    jobsite_id = fields.One2many('jobsite', 'godown_id', string='Jobsite')
    beta_id = fields.Integer()


class Jobsite(models.Model):
    _name = 'jobsite'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin']
    _description = "Jobsite"
    name = fields.Char(string='Site Name', required=True, translate=True, tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Jobsite Already Exists'),
    ]

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        return country

    siteteam = fields.Many2one(comodel_name='crm.team', string='Site Type')
    vl_date = fields.Date('VL Date', help="Visit Lead Due Date (VL Date)")
    godown_id = fields.Many2one('jobsite.godown')


    active = fields.Boolean(string='isActive', default=True, tracking=True)


    street = fields.Char(required=True)
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_get_default_country,
                                 invisible=True)
    stage_id = fields.Many2one("jobsite_stage", string="Stage")
    latitude = fields.Float(string='Geo Latitude', digits=(20, 14))
    longitude = fields.Float(string='Geo Longitude', digits=(20, 14))
    marker_color = fields.Char(string='Marker Color', default='red', required=True)

    @api.onchange('siteteam')
    def _get_domain(self):
        if self.siteteam:
            domain_users = [('id', 'in', self.siteteam.member_ids.ids)]
            return {'domain': {'user_id': domain_users}}

    user_id = fields.Many2one(
        'res.users', string='TD')

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

    def geo_localize(self, vals):
        country = self._get_default_country()
        if 'street2' in vals:
            address_line = vals['street'] + ", " + str(vals['street2'])
        else:
            address_line = vals['street']

        result = self._geo_localize(
            street=address_line,
            zip=vals['zip'],
            city=vals['city'],
            state=False if vals['state_id'] is None else self.env['res.country.state'].search(
                [('id', '=', vals['state_id'])], limit=1).name,
            country=country.name
        )

        if result:
            return result
        return False

    @api.model
    def sendJobsiteToBeta(self, vals):
        if not self.env['ir.config_parameter'].sudo().get_param('ym_configs.save_jobsite'):
            return

        _logger.info("sendJobsiteToBeta: " + str(vals))
        if vals['street2']:
            addr = str(vals['street'] + " " + vals['street2'])
        else:
            addr = str(vals['street'])

        godown_id_cal = vals['godown_id'] if 'godown_id' in vals else self.godown_id.id
        user_id_cal = vals['user_id'] if 'user_id' in vals else self.user_id.id
        siteteam_cal = vals['siteteam'] if 'siteteam' in vals else self.siteteam.id
        stage_id_cal = vals['stage_id'] if 'stage_id' in vals else self.stage_id.id
        site_name_cal = vals['name'] if 'name' in vals else self.name

        try:
            if godown_id_cal:
                godown_name = self.env['jobsite.godown'].search([('id','=',godown_id_cal)]).name
            else:
                godown_name = False

            data = {
                "site_name": site_name_cal,
                "site_address": addr,
                "latitude": str(vals['latitude']),
                "longitude": str(vals['longitude']),
                "city": str(vals['city']),
                "pincode": str(vals['zip']),
                "td_email": str(self.env['res.users'].search([('id', 'ilike', user_id_cal)], limit=1).email),
                "site_type": str(self.env['crm.team'].search([('id', 'ilike', siteteam_cal)], limit=1).name),
                "site_stage": str(self.env['jobsite_stage'].search([('id', 'ilike',stage_id_cal )], limit=1).name),
                "branch_name": str(godown_name)
            }
            request_url = self.env['ir.config_parameter'].sudo().get_param('ym_configs.jobsite_endpoint')
            headers = {
                'Content-type': 'application/json',
            }
            _logger.info("request url: " + request_url + " data: " + json.dumps(data))
            requests.post(request_url, data=json.dumps(data), headers=headers, verify=False)
        except Exception:
            _logger.error(traceback.format_exc())

    def _setLatitudeLogitude(self, vals, is_update=False):
        if is_update:
            vals['street'] = vals['street'] if 'street' in vals else self.street
            vals['street2'] = vals['street2'] if 'street2' in vals else self.street2
            vals['zip'] = vals['zip'] if 'zip' in vals else self.zip
            vals['city'] = vals['city'] if 'city' in vals else self.city
            vals['state_id'] = vals['state_id'] if 'state_id' in vals else self.state_id.id

        result = self.geo_localize(vals)
        if result:
            vals['latitude'] = result[0]
            vals['longitude'] = result[1]
        return vals

    @api.model_create_multi
    def create(self, vals):
        for i in range(len(vals)):
            _logger.info("Create: " + str(vals[i]))
            vals[i] = self._setLatitudeLogitude(vals[i])
            self.sendJobsiteToBeta(vals[i])
        return super(Jobsite, self).create(vals)

    def write(self, vals):
        _logger.info("Write: " + str(vals))
        data = self._setLatitudeLogitude(vals, True)
        if 'street' in vals or 'street2' in vals or 'zip' in vals or 'city' in vals or 'state_id' in vals:
            vals['latitude'] = data['latitude']
            vals['longitude'] = data['longitude']
        self.sendJobsiteToBeta(vals)
        return super(Jobsite, self).write(vals)

    @api.onchange('zip')
    def sendToBeta(self):
        if (self.zip != False):
            nearest_godown = self._get_nearest_godown(self.zip)
            godown_names = [entry['godown_name'] for entry in nearest_godown]
            self.godown_id = self.env['jobsite.godown'].sudo().search([('name', '=', godown_names[0])])

    def _get_nearest_godown(self, pincode):
        endpoint = self.env['ir.config_parameter'].sudo().get_param('ym_configs.nearest_godown_endpoint') + str(pincode)
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
