# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models
from odoo.osv import expression

class Contract(models.Model):
    
    _inherit = 'hr.contract'

    wage = fields.Float('Basic Salary', digits=(16, 2), required=True)
    x_grosssalary = fields.Float('Gross Salary', digits=(16, 2), required=True)
    allow_optimize_salary = fields.Boolean('Optimize Salary for Maximum Tax Benefits') 
    house_rent_alw = fields.Float('HRA', digits=(16, 2))
    conveyance_alw = fields.Float('Conv All', digits=(16, 2))
    medical_alw = fields.Float('Med All', digits=(16, 2))
    allow_partial_salary = fields.Boolean('Allow Parital Salary')
    partial_salary_date = fields.Date('Partial Salary Date')
    partial_salary_rate = fields.Float('Partial Salary Rate (%)')
    allow_manual_investment_rebate = fields.Boolean('Allow Manual Investment Rebate')
    manual_investment_amount = fields.Float('Manual Investment Amount')
    allow_tax_for_bonuse = fields.Boolean('Spread Tax on Bonus')
    bonus_amount = fields.Float('Bonus Amount')

    special_alw = fields.Float('Special Allowance')
    dearness_alw = fields.Float('Dearness Allowance')
    mobile_alw = fields.Float('Mobile Allowance')
    employee_code = fields.Char(related='employee_id.employee_code')
    sf_id_2 = fields.Integer(related='employee_id.sf_id_2')
    work_location_type = fields.Char(related='employee_id.work_location_type')

    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get())

    @api.onchange('employee_id')
    def _onchange_employee_id(self):    
        super(Contract, self)._onchange_employee_id()
        if self.employee_id:
            self.company_id = self.employee_id.company_id

    @api.onchange('allow_optimize_salary')
    def _onchange_allow_optimize_salary(self):
        if (self.allow_optimize_salary == True):
            
            gross = self.x_grosssalary
            wage = 0
            hralw = 0
            malw = 0
            calw = 0

            #calw
            if(gross >= 2500):
                calw = 2500

            #wage
            wage = (gross - calw) / 1.6

            #hralw     
            hralw = wage * .5   
            if(hralw > 25000):
                hralw = 25000
                wage = (gross - calw - hralw) / 1.1

            #malw
            malw = wage * .1
            if(malw > 10000):
                malw = 10000

            #set all values
            wage = round(gross - (hralw + calw + malw))
            self.house_rent_alw = round(hralw)
            self.conveyance_alw = round(calw)
            self.medical_alw = round(malw)

            gross_copy = wage + round(hralw) + round(calw) + round(malw)
            diff = gross_copy - gross
            self.wage = wage - diff

        # else:           
        #     self.wage = 0
        #     self.house_rent_alw = 0
        #     self.conveyance_alw = 0
        #     self.medical_alw = 0