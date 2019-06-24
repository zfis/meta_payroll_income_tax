# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError



''''
print_position = 0

class TaxCardReport(models.AbstractModel):
    _name = 'report.income.tax_card_id'

    def get_payslip_month_record(self, payroll_month):

        temp = ''
        if payroll_month != 7:
            if payroll_month >=7 and payroll_month <= 12:
                for x in range(7, payroll_month):
                    temp += str(x) + ','
                temp = temp.rstrip(',')
            else:
                for x in range(1, payroll_month):
                    temp += str(x) + ','
                temp += '7,8,9,10,11,12'

        payslip_month_record = '{' + temp + '}' 
    
        return payslip_month_record

    
    def get_res_salary_data(self, payroll_month, employee_id, fiscal_year):
  
        res_salary_data = []    
        res_salary_data.append({'data':[]})  
        payslip_month_record = self.get_payslip_month_record(payroll_month)

        self.env.cr.execute("""SELECT 
                                payslipline.code,
                                MIN(category.code) cat_code,
                                MIN(payslipline.name) AS name,
                                MAX(payslip.hr_exemption) AS hr_exemption,
                                MAX(payslip.med_exemption) AS med_exemption,
                                MAX(payslip.conv_exemption) AS conv_exemption,
                                MIN(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=%s THEN  payslip.remain_month END) AS remain_month,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=%s THEN payslipline.amount END) AS amount,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=ANY('%s'::int[]) THEN payslipline.amount END) AS ytd_amount
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN hr_salary_rule_category category ON category.id = payslipline.category_id
                                WHERE company.id IS NOT NULL AND
                                (payslip.state='done' OR payslip.state='draft') AND
                                payslipline.employee_id=%s AND
                                payslip.fiscal_year='%s'
                                GROUP BY payslipline.code
                                ORDER BY MIN(payslipline.sequence)
                                """ % (payroll_month, payroll_month, payslip_month_record, employee_id, fiscal_year,))
        salaryData = self.env.cr.dictfetchall() 

        amount_total = 0
        ytd_amount_total = 0
        annual_amount_total = 0
        exempt_amount_total  = 0
        taxable_amount_total = 0

        for salary in salaryData:  

            #dependency
            if salary["cat_code"] not in ['DED','ODED','ALEMP','GDED','GROSS','NET','NTAX','PTAX','ITAX','AITAX']:     

                try: 
                    amount = int(salary["amount"])
                except: 
                    amount = 0

                try: 
                    ytd_amount = int(salary["ytd_amount"])
                except: 
                    ytd_amount = 0

                try: 
                    remain_month = int(salary["remain_month"])
                except: 
                    remain_month = 0

                annual_amount = 0
                if salary["cat_code"] in ['BASIC','ALW','ECPF','NCALW']:
                    annual_amount =  ytd_amount + (amount * remain_month)
                else:
                    annual_amount = ytd_amount + amount

                exempt_amount = 0
                if salary["code"] == 'HRA':
                    exempt_amount = salary["hr_exemption"]
                elif salary["code"] == 'MALW':
                    exempt_amount = salary["med_exemption"]
                elif salary["code"] == 'CALW':
                    exempt_amount = salary["conv_exemption"]

                amount_total += amount
                ytd_amount_total += ytd_amount
                annual_amount_total += annual_amount
                exempt_amount_total += exempt_amount
                
                if (annual_amount - exempt_amount) < 0:
                    taxable_amount = 0
                else:
                    taxable_amount = annual_amount - exempt_amount

                taxable_amount_total += taxable_amount

                res_salary_data[0]['data'].append({
                    'name': salary["name"],
                    'amount': amount,
                    'ytd_amount': ytd_amount,
                    'annual_amount': annual_amount,
                    'exempt_amount': exempt_amount,
                    'taxable_amount': taxable_amount
                })
        
        res_salary_data[0]['data'].append({
            'name': 'Total Taxable Income',
            'amount': amount_total,
            'ytd_amount': ytd_amount_total,
            'annual_amount': annual_amount_total,
            'exempt_amount': exempt_amount_total,
            'taxable_amount': taxable_amount_total
        })

        return res_salary_data
    
    @api.multi
    def get_tax_rule_data(self, income_year):

        query = "SELECT * FROM income_tax WHERE income_tax_year=%s"
        params = (income_year, )
        self.env.cr.execute(query, params)
        taxRuleData = self.env.cr.dictfetchall()[0]

        if (len(taxRuleData) <= 0):
            raise UserError(_('No income tax rule data found.'))

        return taxRuleData

    def get_employees(self, data, docids):

        res = []
        res.append({'data':[]})
        #Employee = self.env['hr.employee']   
        payroll_month = int(data['payroll_month'])
        fiscal_year = int(data['payroll_year'])  #.split('-')[0]    
        income_year = str(fiscal_year) + "-" + str(fiscal_year+1)
        assesment_year = str(fiscal_year+1) + "-" + str(fiscal_year+2)

        if payroll_month in [1,2,3,4,5,6]:
            taxDateTo = str(int(fiscal_year) + 1) + "-" + str(payroll_month) + "-28"
        else:
            taxDateTo = str(int(fiscal_year)) + "-" + str(payroll_month) + "-28"

        #for emp in Employee.browse(data['emp']):  
        global print_position
        print_position = print_position + 1
        #print(print_position-1)
        #print(docids[print_position-1])  
        #print("")
        emp = self.env['hr.employee'].browse(docids[print_position-1])   
        if len(docids) == print_position:
            print_position = 0

        self.env.cr.execute("""SELECT *
                            FROM hr_payslip 
                            WHERE employee_id=%s
                            AND EXTRACT(MONTH FROM date_from)=%s
                            """ % (emp.id, payroll_month))
        payslip_data = self.env.cr.dictfetchall() 

        
        current_year = int(fiscal_year)
        if int(payroll_month) >= 1 and int(payroll_month) <= 6:
            current_year = int(fiscal_year) + 1

        if len(payslip_data) == 0:  
            payslip_data = None
            res_salary_data = []    
            tax_liability_slab_record = [0, 0, 0, 0, 0, 0]  
            tax_rebate_slab_record = [0, 0, 0] 
            #######
            res[0]['data'].append({
                'name': emp.name,
                'id': emp.id,  
                'company': emp.company_id.name,  
                'gender': emp.gender.capitalize() if emp.gender else "",
                'dob': datetime.datetime.strptime(emp.birthday, '%Y-%m-%d').strftime('%d-%b-%y') if emp.birthday else "",
                'sf_id_2': emp.sf_id_2,
                'e_tin': emp.e_tin,
                'residency': emp.residency.capitalize(),                      
                'fiscal_year': fiscal_year,
                'current_year': current_year,
                'income_year': income_year,
                'assessment_year': assesment_year,
                'payroll_month': datetime.date(fiscal_year, payroll_month, 1).strftime('%B'),
                'salary_data': res_salary_data,
                'payslip_data': payslip_data,
                'tax_rule_data': self.get_tax_rule_data(income_year),
                'tax_liability_slab_record': tax_liability_slab_record,
                'tax_rebate_slab_record': tax_rebate_slab_record,
                'providendFund': 0,
                ###
                'taxable_income_total': 0,
                'tax_liability_total': 0,
                'max_allowable_investment_limit': 0,
                'tax_rebate_total': 0,
                'tax_payable_total': 0,
                'tax_paid_total': 0,
                'remain_tax_payable': 0,
                'remain_month': 0,
                'monthly_tax_payable':0
            })
        else:
            payslip_data = payslip_data[0]
            max_allowable_investment_limit = int(payslip_data['max_allowable_investment_limit'] or 0)
            taxable_income_total = int(payslip_data['taxable_income_total'] or 0)
            res_salary_data = self.get_res_salary_data(payroll_month, emp.id, fiscal_year)  
            tax_liability_slab_record = HrPayslip.get_tax_liability_total_additional(self.env['hr.payslip'].browse(payslip_data['id']), taxable_income_total)
            tax_rebate_slab_record, providendFund = HrPayslip.get_tax_rebate_total_additional(self.env['hr.payslip'].browse(payslip_data['id']), max_allowable_investment_limit, taxDateTo)
            #######
            res[0]['data'].append({
                'name': emp.name,
                'id': emp.id,  
                'company': emp.company_id.name,  
                'gender': emp.gender.capitalize(),
                'dob': datetime.datetime.strptime(emp.birthday, '%Y-%m-%d').strftime('%d-%b-%y'),
                'sf_id_2': emp.sf_id_2,
                'e_tin': emp.e_tin,
                'residency': emp.residency.capitalize(),                      
                'fiscal_year': fiscal_year,
                'current_year': current_year,
                'income_year': income_year,
                'assessment_year': assesment_year,
                'payroll_month': datetime.date(fiscal_year, payroll_month, 1).strftime('%B'),
                'salary_data': res_salary_data,
                'payslip_data': payslip_data,
                'tax_rule_data': self.get_tax_rule_data(income_year),
                'tax_liability_slab_record': tax_liability_slab_record,
                'tax_rebate_slab_record': tax_rebate_slab_record,
                'providendFund': providendFund,
                ###
                'taxable_income_total': int(payslip_data['taxable_income_total'] or 0),
                'tax_liability_total': int(payslip_data['tax_liability_total'] or 0),
                'max_allowable_investment_limit':  int(payslip_data['max_allowable_investment_limit'] or 0),
                'tax_rebate_total':  int(payslip_data['tax_rebate_total'] or 0),
                'tax_payable_total':  int(payslip_data['tax_payable_total'] or 0),
                'tax_paid_total':  int(payslip_data['tax_paid_total'] or 0),
                'remain_tax_payable': int(payslip_data['remain_tax_payable'] or 0),
                'remain_month': int(payslip_data['remain_month'] or 0),
                'monthly_tax_payable': int(payslip_data['monthly_tax_payable'] or 0)
            })
            
        return res

    @api.model
    def render_html(self, docids, data=None):
        
        if not data.get('form'):
                raise UserError(_("Form content is missing, this report cannot be printed."))

        print(docids)

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('income.tax_card_id')
        active_ids = self.env.context.get('active_ids', [])

        docargs = {
            'doc_ids': active_ids,
            'doc_model': report.model,
            'employees': self.get_employees(data['form'], active_ids),
            'date': time.strftime("%d/%m/%Y"),
        }
        
        return report_obj.render('income.tax_card_id', docargs)
        
'''

