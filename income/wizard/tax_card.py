# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import datetime
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def get_tax_liability_total_additional(self, totalTaxableIncome):
        self.globalLiabilitySlabRecord = [0, 0, 0, 0, 0, 0]    
        super(HrPayslip, self).get_tax_liability_total(True, totalTaxableIncome)
        return self.globalLiabilitySlabRecord

    @api.multi
    def get_tax_rebate_total_additional(self, maxAllowInvestmentLimit, taxDateTo):
        self.globalRebateSlabRecord = [0, 0, 0]
        super(HrPayslip, self).get_tax_rebate_total(True, maxAllowInvestmentLimit)
        self.globalFindProvidendFund = True
        self.globalTaxDateTo = taxDateTo
        providendFund = super(HrPayslip, self).get_categorywise_annual_total('ECPF')
        return self.globalRebateSlabRecord, providendFund


class TaxCard(models.TransientModel):
    
    _name = 'tax.card'
    _description = 'Tax Card'

    employee_id = fields.Many2one('hr.employee', string='Employee')  
    fiscal_year = fields.Char("Fiscal Year")
    current_year = fields.Char("Current Year")
    income_year = fields.Char("Income Year")
    assessment_year = fields.Char("Assesment Year")

    payroll_month = fields.Char()
    salary_data = fields.Text()
    payslip_data_len = fields.Integer()
    tax_rule_data = fields.Text()
    tax_liability_slab_record = fields.Text()
    tax_rebate_slab_record = fields.Text()
    providendFund = fields.Integer()
    hr_field_data = fields.Text()

    taxable_income_total = fields.Integer()
    tax_liability_total = fields.Integer()
    max_allowable_investment_limit = fields.Integer()
    tax_rebate_total = fields.Integer()
    tax_payable_total = fields.Integer()
    tax_paid_total = fields.Integer()
    remain_tax_payable = fields.Integer()
    remain_month = fields.Integer()
    monthly_tax_payable = fields.Integer()

    ytd_income_tax = fields.Integer()
    ytd_advance_income_tax= fields.Integer()
    current_advance_income_tax = fields.Integer()

    def get_converted_val(self, employee_id, val):

        employees = self.env['hr.employee'].browse([employee_id])

        return_val = ""
        for emp in employees: 
            try:
                return_val = eval('emp.' + val)
            except Exception:
                return_val = ""

        return return_val


class TaxCardData(models.TransientModel):

    _name = 'tax.card.data'
    _description = 'Tax Card Wizard'

    payroll_month = fields.Selection([
        ('07','July'),
        ('08','August'),
        ('09','September'),
        ('10','October'),
        ('11','November'),
        ('12','December'),
        ('01','January'),
        ('02','February'),
        ('03','March'),
        ('04','April'),
        ('05','May'),
        ('06','June')], 
        default='07', 
        string='Payroll Month', 
        required=True) 

    payroll_year = fields.Selection([('2018','2018-2019'),('2019','2019-2020')], default='2018', string='Payroll Year', required=True)
    emp = fields.Many2many('hr.employee', 'summary_emp_rel', 'sum_id', 'emp_id', string='Employee(s)')


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

                res_salary_data.append({
                    'name': salary["name"],
                    'amount': amount,
                    'ytd_amount': ytd_amount,
                    'annual_amount': annual_amount,
                    'exempt_amount': exempt_amount,
                    'taxable_amount': taxable_amount
                })
        
        res_salary_data.append({
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


    def get_categorywise_total(self, employee_id, categoryCode, fiscal_year, payroll_month):

        payslip_month_record = self.get_payslip_month_record(payroll_month)

        self.env.cr.execute("""SELECT 
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=ANY(%s::int[]) THEN payslipline.total END) AS total
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done' OR payslip.state='draft') 
            AND payslip.employee_id=%s 
            AND categoryRule.code=%s
            AND payslip.fiscal_year='%s'
            GROUP BY categoryRule.code""", 
            (payslip_month_record, employee_id, categoryCode, fiscal_year))

        categorywiseData = self.env.cr.dictfetchall()

        categorywiseTotal = 0
        if (len(categorywiseData) > 0):
            categorywiseTotal = categorywiseData[0]["total"] or 0

        return categorywiseTotal

    
    def get_categorywise_monthly_total(self, employee_id, categoryCode, fiscal_year, payroll_month):

        self.env.cr.execute("""SELECT SUM(payslipLine.total) total 
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done' OR payslip.state='draft') 
            AND payslip.employee_id=%s 
            AND categoryRule.code=%s
            AND payslip.fiscal_year='%s'
            AND EXTRACT(MONTH FROM payslip.date_from)='%s'
            GROUP BY categoryRule.code""", 
            (employee_id, categoryCode, fiscal_year, payroll_month))

        categorywiseData = self.env.cr.dictfetchall()

        categorywiseTotal = 0
        if (len(categorywiseData) > 0):
            categorywiseTotal = categorywiseData[0]["total"] or 0

        return categorywiseTotal


    @api.multi
    def print_report(self):
        
        [data] = self.read()
        data['emp'] = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(data['emp'])

        payroll_month = int(self.payroll_month)
        fiscal_year = int(self.payroll_year) 
        income_year = str(fiscal_year) + "-" + str(fiscal_year+1)
        assesment_year = str(fiscal_year+1) + "-" + str(fiscal_year+2)

        if payroll_month in [1,2,3,4,5,6]:
            taxDateTo = str(int(fiscal_year) + 1) + "-" + str(payroll_month) + "-28"
        else:
            taxDateTo = str(int(fiscal_year)) + "-" + str(payroll_month) + "-28"

        self.env.cr.execute(""" TRUNCATE TABLE tax_card; """)
        for emp in employees: 

            current_year = int(fiscal_year)
            if int(payroll_month) >= 1 and int(payroll_month) <= 6:
                current_year = int(fiscal_year) + 1

            self.env.cr.execute("""SELECT *
                            FROM hr_payslip 
                            WHERE employee_id=%s
                            AND EXTRACT(MONTH FROM date_from)=%s
                            AND (state='done' OR state='draft') 
                            """ % (emp.id, payroll_month))
            payslip_data = self.env.cr.dictfetchall() 
       
            company = self.env['res.company']._company_default_get()
            self.env.cr.execute("""SELECT * FROM hr_field 
                                    WHERE report_name='tax_card' 
                                    AND company_id=%s
                                    ORDER by sequence
                                    """,(company.id,))
            hr_field_data = self.env.cr.dictfetchall()

            if len(payslip_data) == 0:  
                res_salary_data = []    
                tax_liability_slab_record = [0, 0, 0, 0, 0, 0]  
                tax_rebate_slab_record = [0, 0, 0] 

                self.env['tax.card'].create({
                    'employee_id': emp.id,  
                    'fiscal_year': fiscal_year,
                    'current_year': current_year,
                    'income_year': income_year,
                    'assessment_year': assesment_year,                 
                    'payroll_month': datetime.date(fiscal_year, payroll_month, 1).strftime('%B'),
                    'salary_data': json.dumps(res_salary_data),
                    'payslip_data_len': len(payslip_data),
                    'tax_rule_data': json.dumps(self.get_tax_rule_data(income_year)),
                    'tax_liability_slab_record': tax_liability_slab_record,
                    'tax_rebate_slab_record': tax_rebate_slab_record,
                    'providendFund': 0,
                    'taxable_income_total': 0,
                    'tax_liability_total': 0,
                    'max_allowable_investment_limit': 0,
                    'tax_rebate_total': 0,
                    'tax_payable_total': 0,
                    'tax_paid_total': 0,
                    'remain_tax_payable': 0,
                    'remain_month': 0,
                    'monthly_tax_payable':0,
                    'ytd_income_tax': 0,
                    'ytd_advance_income_tax': 0,
                    'current_advance_income_tax': 0,
                    'hr_field_data': json.dumps(hr_field_data),
                })

            else:
                payslip_data = payslip_data[0]
                max_allowable_investment_limit = int(payslip_data['max_allowable_investment_limit'] or 0)
                taxable_income_total = int(payslip_data['taxable_income_total'] or 0)
                res_salary_data = self.get_res_salary_data(payroll_month, emp.id, fiscal_year)  
                tax_liability_slab_record = HrPayslip.get_tax_liability_total_additional(self.env['hr.payslip'].browse(payslip_data['id']), taxable_income_total)
                tax_rebate_slab_record, providendFund = HrPayslip.get_tax_rebate_total_additional(self.env['hr.payslip'].browse(payslip_data['id']), max_allowable_investment_limit, taxDateTo)

                self.env['tax.card'].create({
                    'employee_id': emp.id,  
                    'fiscal_year': fiscal_year,
                    'current_year': current_year,
                    'income_year': income_year,
                    'assessment_year': assesment_year, 
                    'payroll_month': datetime.date(fiscal_year, payroll_month, 1).strftime('%B'),
                    'salary_data': json.dumps(res_salary_data),
                    'payslip_data_len': len(payslip_data),
                    'tax_rule_data': json.dumps(self.get_tax_rule_data(income_year)),
                    'tax_liability_slab_record': tax_liability_slab_record,
                    'tax_rebate_slab_record': tax_rebate_slab_record,
                    'providendFund': providendFund,
                    'taxable_income_total': int(payslip_data['taxable_income_total'] or 0),
                    'tax_liability_total': int(payslip_data['tax_liability_total'] or 0),
                    'max_allowable_investment_limit':  int(payslip_data['max_allowable_investment_limit'] or 0),
                    'tax_rebate_total':  int(payslip_data['tax_rebate_total'] or 0),
                    'tax_payable_total':  int(payslip_data['tax_payable_total'] or 0),
                    'tax_paid_total':  int(payslip_data['tax_paid_total'] or 0),
                    'remain_tax_payable': int(payslip_data['remain_tax_payable'] or 0),
                    'remain_month': int(payslip_data['remain_month'] or 0),
                    'monthly_tax_payable': int(payslip_data['monthly_tax_payable'] or 0),
                    'ytd_income_tax': self.get_categorywise_total(emp.id, 'ITAX', fiscal_year, payroll_month) * (-1),
                    'ytd_advance_income_tax': self.get_categorywise_total(emp.id, 'AITAX', fiscal_year, payroll_month) * (-1),
                    'current_advance_income_tax': self.get_categorywise_monthly_total(emp.id, 'AITAX', fiscal_year, payroll_month) * (-1),
                    'hr_field_data': json.dumps(hr_field_data),
                })


        docids = self.env['tax.card'].search([])
        
        if len(docids) > 0:
            return self.env['report'].get_action(docids, 'income.tax_card_id')
        else:
            raise UserError("No Record Found")  
