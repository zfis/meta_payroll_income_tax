# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import datetime
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json


class SalaryCertificate(models.TransientModel):
    
    _name = 'salary.certificate'
    _description = 'Salary Certificate'

    employee_id = fields.Many2one('hr.employee', string='Employee')  
    income_year = fields.Char("Income Year")
    assessment_year = fields.Char("Assesment Year")

    deduction_total = fields.Integer("Deduction Total")
    challan_tds_total = fields.Integer("Challan TDS Total")
    income_total = fields.Integer("Income Total")

    salary_data = fields.Text("Salary Data")
    challan_data = fields.Text("Challan Data")


class SalaryCertificateData(models.TransientModel):

    _name = 'salary.certificate.data'
    _description = 'Salary Certificate Wizard'

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

        self.env.cr.execute(""" TRUNCATE TABLE salary_certificate; """)
        for emp in employees: 

            #get salary computation detail with accumulated   
            res_salary_data = []                 
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
                    res_salary_data.append({
                        "code": salary["code"],
                        "name": salary["name"],
                        "amount": int(salary["amount"])
                    })

            #get challan_data   
            res_challan_data = []                    
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

                res_challan_data.append({
                    'number': challan["number"],
                    'submission_date': submission_date,
                    'payroll_month': datetime.date(fiscal_year, int(challan["payroll_month"]), 1).strftime('%B'),
                    'tds_amount': int(challan["tds_amount"])
                })

            self.env['salary.certificate'].create({
                'employee_id': emp.id,   
                'income_year': income_year,
                'assessment_year': assesment_year,
                'salary_data': json.dumps(res_salary_data),
                'challan_data': json.dumps(res_challan_data),
                'deduction_total': int(deduction_total) * (-1),
                'challan_tds_total': challan_tds_total,
                'income_total': int(income_total)
            })

        docids = self.env['salary.certificate'].search([])
        
        if len(docids) > 0:
            return self.env['report'].get_action(docids, 'income.salary_report_id')
        else:
            raise UserError("No Record Found")  