# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


'''
print_position = 0

class InvestmentAllowanceDeclarationReport(models.AbstractModel):
    _name = 'report.income.report_id'


    def _get_employees(self, data, docids):
        
        res = []
        res.append({'data':[]})    
        fiscal_year = int(data['income_year'])
        income_year = str(fiscal_year) + "-" + str(fiscal_year+1)
        assesment_year = str(fiscal_year+1) + "-" + str(fiscal_year+2)
        
        global print_position
        print_position = print_position + 1
        emp = self.env['hr.employee'].browse(docids[print_position-1])   
        if len(docids) == print_position:
            print_position = 0
            
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
                                """ % (emp.id,data['income_year'],))
        payrollData = self.env.cr.dictfetchall() 

        max_invesetment_rebate = 0
        if (payrollData) > 0 and payrollData[0]["taxable_income_total"] != None:
            #max_invesetment_rebate = payrollData[0]["max_allowable_investment_limit"]
            max_invesetment_rebate = payrollData[0]["taxable_income_total"] * (taxRuleData["tax_rebate_investment_ratio"] / 100.00)

        res[0]['data'].append({
            'name': emp.name,
            'e_tin' : emp.e_tin,
            'address': emp.address_home_temp,
            'designation': emp.job_id.name,
            'company': emp.company_id.name,
            'company_street': emp.company_id.street,
            'company_street2': emp.company_id.street2,
            'company_city': emp.company_id.city if emp.company_id.city else "" + " " + emp.company_id.zip if emp.company_id.zip else "",      
            'company_country': emp.company_id.country_id.name,    
            'income_year': income_year,
            'assessment_year': assesment_year,
            'max_invesetment_rebate': int(max_invesetment_rebate)
        })

        return res



    @api.model
    def render_html(self, docids, data=None):
        
        # if not data.get('form'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))

        # report_obj = self.env['report']
        # report = report_obj._get_report_from_name('income.report_id')
        # active_ids = self.env.context.get('active_ids', [])

        # docargs = {
        #     'doc_ids': active_ids,
        #     'doc_model': report.model,
        #     'employees': self._get_employees(data['form'], active_ids),
        #     'date': time.strftime("%d/%m/%Y")
        # }

        # return report_obj.render('income.report_id', docargs)

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('income.report_id')
        active_ids = self.env.context.get('active_ids', [])

        print(docids)

        docargs = {
            'doc_ids': active_ids,
            'doc_model': report.model,
            'docs': docids
        }

        return report_obj.render('income.report_id', docargs)
    '''