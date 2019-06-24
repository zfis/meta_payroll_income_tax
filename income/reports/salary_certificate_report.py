# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


'''
print_position = 0

class SalaryCertificateReport(models.AbstractModel):
    _name = 'report.income.salary_report_id'

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

        #get salary computation detail with accumulated     
        res_salary_data = []    
        res_salary_data.append({'data':[]})                    
        self.env.cr.execute("""SELECT 
                                payslipline.code,
                                MIN(category.code) cat_code,
                                MIN(payslipline.name) AS name,
                                SUM(payslipline.amount) AS amount
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN hr_salary_rule_category category ON category.id = payslipline.category_id
                                WHERE company.id IS NOT NULL AND
                                (payslip.state='done') AND
                                payslipline.employee_id=%s AND
                                payslip.fiscal_year='%s'
                                GROUP BY payslipline.code
                                ORDER BY MIN(payslipline.sequence)
                                """ % (emp.id,fiscal_year,))
        salaryData = self.env.cr.dictfetchall() 

        deduction_total = 0
        income_total = 0
        for salary in salaryData:  
            if salary["code"] == 'TDED':
                deduction_total = salary["amount"]
            if salary["code"] == 'GROSS':
                income_total = salary["amount"]
            if salary["cat_code"] not in ['DED','ODED','ALEMP','GDED','GROSS','NET','NTAX','PTAX','ITAX','AITAX']:                         
                res_salary_data[0]['data'].append({
                    'code': salary["code"],
                    'name': salary["name"],
                    'amount': int(salary["amount"])
                })

        #get challan_data   
        res_challan_data = []    
        res_challan_data.append({'data':[]})                    
        self.env.cr.execute("""SELECT 
                                c.number, 
                                c.submission_date, 
                                c.payroll_month, 
                                c_line.tds_amount
                                FROM tax_challan c
                                LEFT JOIN tax_challan_line c_line ON c.id=c_line.challan_id
                                WHERE c_line.employee_id=%s AND
                                c.payroll_year='%s'
                                ORDER BY c.payroll_month
                                """ % (emp.id,fiscal_year,))
        challanData = self.env.cr.dictfetchall() 

        challan_tds_total = 0
        for challan in challanData:  
            challan_tds_total += int(challan["tds_amount"])

            submission_date = ''
            if challan["submission_date"] is not None:
                submission_date = datetime.datetime.strptime(challan["submission_date"], '%Y-%m-%d').strftime('%d-%m-%Y')

            res_challan_data[0]['data'].append({
                'number': challan["number"],
                'submission_date': submission_date,
                'payroll_month': datetime.date(fiscal_year, int(challan["payroll_month"]), 1).strftime('%B'),
                'tds_amount': int(challan["tds_amount"])
            })

        res[0]['data'].append({
            'name': emp.name,
            'e_tin': emp.e_tin,
            'company': emp.company_id.name,
            'address': emp.address_home_temp,
            'designation': emp.job_id.name,
            'join_date' : datetime.datetime.strptime(emp.joining_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
            'income_year': income_year,
            'assessment_year': assesment_year,
            'salary_data': res_salary_data,
            'challan_data': res_challan_data,
            'deduction_total': int(deduction_total) * (-1),
            'challan_tds_total': challan_tds_total,
            'income_total': int(income_total)
        })

        return res

    @api.model
    def render_html(self, docids, data=None):
        
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('income.salary_report_id')
        active_ids = self.env.context.get('active_ids', [])

        docargs = {
            'doc_ids': active_ids,
            'doc_model': report.model,
            'employees': self._get_employees(data['form'], active_ids),
            'date': time.strftime("%d/%m/%Y")
        }

        return report_obj.render('income.salary_report_id', docargs)
'''