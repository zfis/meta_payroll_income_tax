# -*- coding: utf-8 -*-

from odoo import models, api

class ArchivePayslipWiz(models.TransientModel):
    _name = 'archive.payslip.wizard'

    @api.multi
    def archive_payslip(self):
        
        payslip_ids = self.env['hr.payslip']. \
            browse(self._context.get('active_ids'))

        for payslip in payslip_ids:
            payslip.action_payslip_archive()
