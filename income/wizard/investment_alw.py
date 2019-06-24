# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# http://inkalpatel.blogspot.com/2017/09/open-wizard-on-click-menu.html

class InvestmentAllowanceDeclaration(models.TransientModel):
    
    _name = 'investment.alw'
    _description = 'Investment Allowance Declaration'

    employee_id = fields.Many2one('hr.employee', string='Employee')  
    income_year = fields.Char("Income Year")
    assessment_year = fields.Char("Assesment Year")
    max_invesetment_rebate = fields.Integer("Max Investment Rebate")


class InvestmentAllowanceDataDeclaration(models.TransientModel):

    _name = 'investment.alw.data'
    _description = 'Investment Allowance Declaration Wizard'

    fiscal_year = fields.Selection([('2018','2018-2019'),('2019','2019-2020')], default='2018', string='Payroll Year', required=True) 
    emp = fields.Many2many('hr.employee', 'summary_emp_rel', 'sum_id', 'emp_id', string='Employee(s)')
    
    @api.multi
    def print_report(self):

        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(data['emp'])
        
        fiscal_year = int(self.fiscal_year)
        income_year = str(fiscal_year) + "-" + str(fiscal_year+1)
        assesment_year = str(fiscal_year+1) + "-" + str(fiscal_year+2)

        self.env.cr.execute(""" TRUNCATE TABLE investment_alw; """)
        for emp in employees: 
    
            #get tax rebate                             
            self.env.cr.execute("""SELECT * FROM income_tax 
                                    WHERE income_tax_year='%s'
                                    """ % (income_year,))
            taxRuleData = self.env.cr.dictfetchall()[0]

            if (len(taxRuleData) <= 0):
                raise UserError(_('No income tax year data found.'))

            self.env.cr.execute("""SELECT max_allowable_investment_limit, taxable_income_total FROM hr_payslip 
                                    WHERE employee_id=%s
                                    AND fiscal_year='%s'
                                    ORDER BY date_from DESC
                                    """ % (emp.id,fiscal_year,))
            payrollData = self.env.cr.dictfetchall() 

            max_invesetment_rebate = 0
            if len(payrollData) > 0 and payrollData[0]["taxable_income_total"] != None:
                    #max_invesetment_rebate = payrollData[0]["max_allowable_investment_limit"]
                    max_invesetment_rebate = payrollData[0]["taxable_income_total"] * (taxRuleData["tax_rebate_investment_ratio"] / 100.00)
   
            self.env['investment.alw'].create({
                'employee_id': emp.id,   
                'income_year': income_year,
                'assessment_year': assesment_year,
                'max_invesetment_rebate': int(max_invesetment_rebate)
            })

        docids = self.env['investment.alw'].search([])

        if len(docids) > 0:
            return self.env['report'].get_action(docids, 'income.report_id')
        else:
            raise UserError("No Record Found")  