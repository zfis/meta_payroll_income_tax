# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import calendar
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json


class PayrollTrackerReport(models.AbstractModel):
    _name = 'report.income.payroll_tracker_id'

    def _get_companies(self, data):
        
        res = []
        res.append({'data':[]})
        company_id = data['company_id']
        company_name = data['company_name']
        payroll_month = int(data['payroll_month']) 
        payroll_year = int(data['payroll_year'])
        income_year = str(payroll_year) + "-" + str(payroll_year+1)
        assesment_year = str(payroll_year+1) + "-" + str(payroll_year+2)
            
        #get monthly employee payslip detail   
        res_rule_data = []    
        res_rule_data.append({'data':[]})     
        res_payslip_data = []    
        res_payslip_data.append({'data':[]})    
        res_payslip_summary_data = []   
        res_payslip_summary_data.append({'data':[]})  

        #get employee data       
        self.env.cr.execute("""SELECT
                                code,
                                MIN(name) as name
                                FROM hr_salary_rule
                                WHERE company_id=%s
                                GROUP BY code 
                                ORDER BY MIN(sequence)
                                """ % (company_id,))
        rule_data = self.env.cr.dictfetchall()       

        for rule in rule_data:  
            res_rule_data[0]['data'].append({
                'code': rule["code"],
                'title': rule["name"]
            })

        if payroll_month >= 1 and payroll_month <= 6:
            payroll_year = payroll_year + 1

        #get payslip data  
        #ref: https://postgresql.verite.pro/blog/2018/06/19/crosstab-pivot.html    
        self.env.cr.execute("""SELECT emp_name, MIN(state) as state, json_object_agg(code,amount) AS json_data
                                FROM ( 
                                SELECT
                                employee.id AS emp_id,
                                employee.name_related AS emp_name,
                                payslipline.code AS code,
                                payslipline.name AS title,
                                payslip.state AS state,
                                payslipline.total AS amount
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN hr_salary_rule_category category ON category.id = payslipline.category_id
                                WHERE company.id IS NOT NULL AND
                                company.id = %s AND
                                EXTRACT(YEAR FROM payslip.date_from)=%s AND
                                EXTRACT(MONTH FROM payslip.date_from)=%s
                                ORDER BY employee.id ASC, payslipline.sequence ASC
                                ) s
                                GROUP BY emp_name
                                ORDER BY emp_name
                                """ % (company_id,payroll_year,payroll_month,))
        payslip_data = self.env.cr.dictfetchall()     

        for payslip in payslip_data:     

            state = 'DF'
            if payslip["state"] == 'done':
                state = 'DN'     

            res_payslip_data[0]['data'].append({
                'emp_name': payslip["emp_name"],
                'state': state,
                'json_data': payslip["json_data"]
            })

        #get payslip total amount
        self.env.cr.execute("""SELECT
                                payslipline.code as code,
                                SUM(payslipline.total) AS total
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN hr_salary_rule_category category ON category.id = payslipline.category_id
                                WHERE company.id IS NOT NULL AND
                                company.id = %s AND
                                EXTRACT(YEAR FROM payslip.date_from)=%s AND
                                EXTRACT(MONTH FROM payslip.date_from)=%s
                                GROUP BY payslipline.code
                                ORDER BY MIN(payslipline.sequence)
                                """ % (company_id,payroll_year,payroll_month,))
        payslip_summary_data = self.env.cr.dictfetchall()

        for payslip_summary in payslip_summary_data:
            res_payslip_summary_data[0]['data'].append({
                'code': payslip_summary["code"],
                'total': payslip_summary["total"]
            })

        res[0]['data'].append({
            'income_year': income_year,
            'assessment_year': assesment_year,
            'payroll_month': datetime.date(payroll_year, payroll_month, 1).strftime('%B'),
            'payroll_year': payroll_year,
            'rule_data': res_rule_data,
            'payslip_data': res_payslip_data,
            'payslip_summary_data': res_payslip_summary_data,
            'company_name': company_name,
        })

        return res

    @api.model
    def render_html(self, docids, data=None):
        
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        Report = self.env['report']
        payroll_tracker_report = Report._get_report_from_name('income.payroll_tracker_id')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': payroll_tracker_report.model,
            'companies': self._get_companies(data['form']),
            'date': time.strftime("%d/%m/%Y")
        }

        return Report.render('income.payroll_tracker_id', docargs)
