
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class HrSalaryTrackerLoad(models.Model):
    
    _name = 'salary.tracker.load'
    _order = 'sequence asc'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    #copy=False, default=lambda self: self.env['res.company']._company_default_get())
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Details', required=True)
    sf_id_2 = fields.Integer(string='SF ID')
    sequence = fields.Integer(string='Sequence')
    year = fields.Char(string='Year')
    jul = fields.Integer(string='Jul')
    aug = fields.Integer(string='Aug')
    sep = fields.Integer(string='Sep')
    oct = fields.Integer(string='Oct')
    nov = fields.Integer(string='Nov')
    dec = fields.Integer(string='Dec')
    jan = fields.Integer(string='Jan')
    feb = fields.Integer(string='Feb')
    mar = fields.Integer(string='Mar')
    apr = fields.Integer(string='Apr')
    may = fields.Integer(string='May')
    jun = fields.Integer(string='Jun')
    state = fields.Char(string='State')


    def load_payroll_data(self):

        company_id = self.env['res.company']._company_default_get().id

        self.env.cr.execute("""SELECT
            MIN(company.id) AS company_id,
            MIN(employee.id) AS employee_id,
            MIN(employee.sf_id_2) AS sf_id_2,
            MIN(salaryrule.id) AS rule_id,
            MIN(payslip.state) AS state,
            MIN(payslipline.sequence) as sequence,
            MIN(payslip.fiscal_year) AS year,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=7 THEN payslipline.amount END) AS jul,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=8 THEN payslipline.amount END) AS aug,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=9 THEN payslipline.amount END) AS sep,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=10 THEN payslipline.amount END) AS oct,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=11 THEN payslipline.amount END) AS nov,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=12 THEN payslipline.amount END) AS dec,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=1 THEN payslipline.amount END) AS jan,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=2 THEN payslipline.amount END) AS feb,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=3 THEN payslipline.amount END) AS mar,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=4 THEN payslipline.amount END) AS apr,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=5 THEN payslipline.amount END) AS may,
            SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=6 THEN payslipline.amount END) AS jun
            FROM hr_payslip_line AS payslipline
            LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
            LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
            LEFT JOIN res_company company ON company.partner_id = employee.address_id
            LEFT JOIN hr_salary_rule salaryrule ON salaryrule.id = payslipline.salary_rule_id 
            WHERE company.id IS NOT NULL AND
            company.id=%s AND
            (payslip.state='done' OR payslip.state='draft') AND
            salaryrule.id IS NOT NULL
            GROUP BY employee.id, payslip.fiscal_year, payslipline.code
            ORDER BY employee.id, sequence""", 
            (company_id,))
    
        modelData = self.env.cr.dictfetchall()

        for data in modelData:
        
            searchData = self.env['salary.tracker.load'].search([('employee_id', '=', data["employee_id"]),('year', '=', str(data["year"])),('rule_id', '=', data["rule_id"])])

            if len(searchData) == 0:
                self.env['salary.tracker.load'].create({
                    'company_id': data["company_id"],
                    'employee_id': data["employee_id"],
                    'sf_id_2': data["sf_id_2"],
                    'rule_id': data["rule_id"],
                    'sequence': data["sequence"],
                    'year': data["year"],
                    'jul': data["jul"],
                    'aug': data["aug"],
                    'sep': data["sep"],
                    'oct': data["oct"],
                    'nov': data["nov"],
                    'dec': data["dec"],
                    'jan': data["jan"],
                    'feb': data["feb"],
                    'mar': data["mar"],
                    'apr': data["apr"],
                    'may': data["may"],
                    'jun': data["jun"],
                    'state': data["state"]
                    })
            else:
                salary_tracker = self.env['salary.tracker.load'].browse(searchData['id'])
                salary_tracker.write({
                    'company_id': data["company_id"],
                    'sf_id_2': data["sf_id_2"],
                    'sequence': data["sequence"],
                    'jul': data["jul"],
                    'aug': data["aug"],
                    'sep': data["sep"],
                    'oct': data["oct"],
                    'nov': data["nov"],
                    'dec': data["dec"],
                    'jan': data["jan"],
                    'feb': data["feb"],
                    'mar': data["mar"],
                    'apr': data["apr"],
                    'may': data["may"],
                    'jun': data["jun"],
                    'state': data["state"]
                    })
    

'''
class HrSalaryTracker(models.Model):

    _name = 'salary.tracker.report.new'
    _order = 'sequence asc'
    _auto = False

    company_id = fields.Char(string='Company Id')
    company_name = fields.Char(string='Company')
    employee_id = fields.Integer(string='Employee Id')
    employee_name = fields.Char(string='Name of Employee')
    sf_id_2 = fields.Integer('SF ID')
    rule_id = fields.Integer('Rule Id')
    details = fields.Char(string='Details')
    sequence = fields.Char(string='Sequence')
    year = fields.Char('Year')
    jul = fields.Integer(string='Jul')
    aug = fields.Integer(string='Aug')
    sep = fields.Integer(string='Sep')
    oct = fields.Integer(string='Oct')
    nov = fields.Integer(string='Nov')
    dec = fields.Integer(string='Dec')
    jan = fields.Integer(string='Jan')
    feb = fields.Integer(string='Feb')
    mar = fields.Integer(string='Mar')
    apr = fields.Integer(string='Apr')
    may = fields.Integer(string='May')
    jun = fields.Integer(string='Jun')
    state = fields.Char(string='State')


    def load_payroll_data(self):

        # get company
        #default=lambda self: self.env['res.company']._company_default_get())
        #company_id = self.env.user.company_id.id
        company_id = self.env['res.company']._company_default_get().id

        # drop view
        tools.drop_view_if_exists(self.env.cr, self._table)

        # create view
        #CONCAT(MIN(employee.name_related),' (',payslipline.employee_id, ')')
        #payslipline.employee_id AS employee_id,
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS
                                SELECT
                                row_number() over () as id, 
                                MIN(company.id) AS company_id,
                                MIN(company.name) AS company_name,
                                MIN(payslip.state) AS state,
                                MIN(employee.id) AS employee_id,
                                MIN(employee.name_related) AS employee_name,
                                MIN(employee.sf_id_2) AS sf_id_2,
                                MIN(salaryrule.name) AS details,
                                MIN(payslipline.sequence) as sequence,
                                MIN(payslip.fiscal_year) AS year,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=7 THEN payslipline.amount END) AS jul,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=8 THEN payslipline.amount END) AS aug,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=9 THEN payslipline.amount END) AS sep,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=10 THEN payslipline.amount END) AS oct,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=11 THEN payslipline.amount END) AS nov,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=12 THEN payslipline.amount END) AS dec,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=1 THEN payslipline.amount END) AS jan,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=2 THEN payslipline.amount END) AS feb,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=3 THEN payslipline.amount END) AS mar,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=4 THEN payslipline.amount END) AS apr,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=5 THEN payslipline.amount END) AS may,
                                SUM(CASE WHEN EXTRACT(MONTH FROM payslip.date_from)=6 THEN payslipline.amount END) AS jun
                                FROM hr_payslip_line AS payslipline
                                LEFT JOIN hr_employee employee ON employee.id = payslipline.employee_id
                                LEFT JOIN hr_payslip payslip ON payslip.id = payslipline.slip_id
                                LEFT JOIN res_company company ON company.partner_id = employee.address_id
                                LEFT JOIN hr_salary_rule salaryrule ON salaryrule.id = payslipline.salary_rule_id 
                                WHERE company.id IS NOT NULL AND
                                company.id=%s AND
                                (payslip.state='done' OR payslip.state='draft')
                                GROUP BY employee.id, payslip.fiscal_year, payslipline.code
                                """ % (self._table, company_id))

'''