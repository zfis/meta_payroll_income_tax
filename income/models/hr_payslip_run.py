# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models
from odoo.osv import expression


class HrPayslipRun(models.Model):
    
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env['res.company']._company_default_get())
