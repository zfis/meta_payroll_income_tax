# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models
from odoo.osv import expression
from odoo.exceptions import ValidationError

class Employee(models.Model):

    _inherit = 'hr.employee'

    def _get_default_country(self): 
        return 20

    @api.constrains('e_tin')
    def _check_e_tin(self):
        if (len(self.e_tin) != 12):
            raise ValidationError(_('Error! e-TIN Length should be 12.'))
            

    residency = fields.Selection([
        ('resident', 'Resident'),
        ('non-resident', 'Non-Resident')
    ], groups='hr.group_hr_user', required=True, store=True)

    e_tin = fields.Char('e-TIN', size=12, required=True, store=True)
    is_freedom_fighter = fields.Boolean('')
    is_disabled = fields.Boolean('')
    is_disabled_parent_or_legal_guardian = fields.Boolean('')
    employee_code = fields.Char('Employee Code', required=True, store=True)
    joining_date = fields.Date('Date of Joining', required=True, store=True)
    leaving_date = fields.Date('Last Working Day', store=True)
    work_location_type = fields.Char('Location Type')
    work_location_type_2 = fields.Char('--Location Type')
    sf_id = fields.Char('--SF ID')
    sf_id_2 = fields.Integer('SF ID')
    sf_id_3 = fields.Integer('--SF ID')
    address_home_temp = fields.Char('Home Address')
    country_id = fields.Many2one('res.country', string='Nationality (Country)', change_default=True, default=_get_default_country)
    emergency_name = fields.Char(string='Name', groups='hr.group_hr_user')
    emergency_phone = fields.Char(string='Phone Number', groups='hr.group_hr_user')