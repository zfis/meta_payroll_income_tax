# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError

class ComputeTaxPayslipWiz(models.TransientModel):
    _name = 'computetax.payslip.wizard'

    @api.multi
    def computetax_payslip(self):
        
        payslip_ids = self.env['hr.payslip']. \
            browse(self._context.get('active_ids'))

        for payslip in payslip_ids:
            if payslip.state != 'draft':
                raise UserError(_("You can compute tax for payslips only for draft."))

        payslip_ids.compute_tax_sheet()
