# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models
from odoo.osv import expression

class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'

    branch_name = fields.Char(string='Branch')
    routing_num = fields.Char(string='Routing Number')  
    branch_title = fields.Char('Branch Name')
    swift_code = fields.Char('Swift Code')