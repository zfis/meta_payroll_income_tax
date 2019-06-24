# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models
from odoo.osv import expression


class HrPayslipLine(models.Model):

    _inherit = 'hr.payslip.line'

    sf_id_2 = fields.Integer("SF ID", compute='get_sf_id_data')
    sf_id = fields.Integer("SF ID")
    work_location_type = fields.Char("Location Type", compute='get_location_type_data')
    work_location_type_2 = fields.Char("Location Type")
    date_from = fields.Date(related='slip_id.date_from', store=True)
    date_to = fields.Date(related='slip_id.date_to', store=True)

    @api.multi
    def get_sf_id_data(self):
        for item in self:
            item.sf_id_2 = item.employee_id.sf_id_2
            item.write({
                'sf_id':item.employee_id.sf_id_2,
            })

    @api.multi
    def get_location_type_data(self):
        for item in self:
            item.work_location_type = item.employee_id.work_location_type
            item.write({
                'work_location_type_2':item.employee_id.work_location_type,
            })