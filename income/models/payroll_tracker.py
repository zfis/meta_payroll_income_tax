import time
import calendar
import babel

from datetime import datetime, timedelta
from dateutil import relativedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp

class HrPayrollTracker(models.Model):

    _name = 'payroll.tracker.report'
    #_order = 'date asc'
    _auto = False

    company_id = fields.Char(string='Company Id', readonly=True, default=lambda self: self.env['res.company']._company_default_get())
    company_name = fields.Char(string='Company', readonly=True)
    employee_id = fields.Char(string='Employee Id', readonly=True)
    employee_name = fields.Char(string='Name of Employee', readonly=True)
    #designation = fields.Char(string='Designation', readonly=True)
    #joining_date = fields.Char(string='Date of Joining', readonly=True)
    date = fields.Char('MM/YYYY', required=True)
    basic_salary = fields.Integer(string='Basic Salary', readonly=True)
    house_rent_allowance = fields.Integer(string='HRA', readonly=True)
    conveynace_allowance = fields.Integer(string='Conv All.', readonly=True)
    medical_allowance = fields.Integer(string='Med All.', readonly=True)
    other_allowance = fields.Integer(string='Other All.', readonly=True)
    total_gross_pay = fields.Integer(string='Gross Pay', readonly=True)
    less_withholding_tax = fields.Integer(string='TDS', readonly=True)
    less_other_deductions = fields.Integer(string='TDS', readonly=True)
    total_net_pay = fields.Integer(string='Net Pay', readonly=True)
    state = fields.Char(string='State', readonly=True)

    @api.model_cr
    def init(self):
        self.loadPayrollData()
       
    @api.multi
    def loadPayrollData(self):
        
        # drop view 
        tools.drop_view_if_exists(self.env.cr, self._table)

        # create view
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS 
                                SELECT 
                                row_number() over () as id, 
                                MIN(company.id) AS company_id,
                                MIN(company.name) AS company_name,
                                MIN(payslip.state) AS state,
                                payslipline.employee_id AS employee_id,
                                CONCAT(MIN(employee.name_related),' (',payslipline.employee_id, ')') AS employee_name,
                                CONCAT(EXTRACT(MONTH FROM payslip.date_from),'/',EXTRACT(Year FROM payslip.date_from)) AS date,
                                SUM(CASE WHEN payslipline.code='BASIC' THEN payslipline.amount END) AS basic_salary,
                                SUM(CASE WHEN payslipline.code='HRA' THEN payslipline.amount END) AS house_rent_allowance,
                                SUM(CASE WHEN payslipline.code='CALW' THEN payslipline.amount END) AS conveynace_allowance,
                                SUM(CASE WHEN payslipline.code='MALW' THEN payslipline.amount END) AS medical_allowance,
                                SUM(CASE WHEN category.code='OALW' THEN payslipline.amount END) AS other_allowance,
                                SUM(CASE WHEN payslipline.code='GROSS' THEN payslipline.amount END) AS total_gross_pay,
                                SUM(CASE WHEN payslipline.code='RTAX' THEN payslipline.amount END) AS less_withholding_tax,
                                SUM(CASE WHEN payslipline.code='TDED' THEN payslipline.amount END) AS less_other_deductions,
                                SUM(CASE WHEN payslipline.code='NET' THEN payslipline.amount END) AS total_net_pay
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN hr_salary_rule_category category ON category.id = payslipline.category_id
                                WHERE company.id IS NOT NULL AND
                                (payslip.state='done' OR payslip.state='draft')
                                GROUP BY payslipline.employee_id, 
                                CONCAT(EXTRACT(MONTH FROM payslip.date_from),'/',EXTRACT(Year FROM payslip.date_from))
                                """ % (self._table))