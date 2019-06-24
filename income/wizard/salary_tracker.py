# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import os

import StringIO
import base64

import logging
_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Can not import xls writer`.')

class SalaryTracker(models.TransientModel):

    _name = 'salary.tracker'

    _description = 'Salary Tracker'

    payroll_year = fields.Selection([
        ('2018','2018-2019'),
        ('2019','2019-2020')], 
        default='2018', 
        string='Payroll Year', 
        required=True)
			
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)


    @api.multi
    def export_excel(self):     

        company_id = self.env['res.company']._company_default_get()  

        self.env.cr.execute("""SELECT
                                row_number() over () as id, 
                                MIN(company.id) AS company_id,
                                MIN(company.name) AS company_name,
                                MIN(payslip.state) AS state,
                                payslipline.employee_id AS employee_id,
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
                                employee.id=%s AND
                                payslip.fiscal_year='%s' AND
                                (payslip.state='done' OR payslip.state='draft')
                                GROUP BY payslipline.employee_id, payslip.fiscal_year, payslipline.code
                                ORDER BY MIN(payslipline.sequence)
                                """ % (company_id.id, self.employee_id.id, self.payroll_year))
        salary_data = self.env.cr.dictfetchall()   

        file_name = "Salary Tracker - " + self.employee_id.name + " - " + self.payroll_year

        #initialize - resource: https://pypi.org/project/xlwt/
        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Salary Tracker")

        #set style
        style_head = xlwt.easyxf('font: bold on, height 280; align: horiz center;')
        style_subhead = xlwt.easyxf('font: bold on, height 200; align: horiz center;')
        style_font = xlwt.easyxf('font: bold on')
        style_number = xlwt.easyxf(num_format_str='#,##0')
        #style_date = xlwt.easyxf(num_format_str='D-MMM-YY')

        #set data
       
        sheet.write_merge(0, 1, 0, 14, company_id.name, style_head) #top_row, bottom_row, left_column, right_column,
        sub_head = "Salary Tracker for " + self.employee_id.name + " (SF ID: " + str(self.employee_id.sf_id_2) + ")"
        sheet.write_merge(2, 2, 0, 14, sub_head, style_subhead)

        i = 4
        sheet.write(i, 0, "Details", style_font)
        sheet.write(i, 1, "Year", style_font)
        sheet.write(i, 2, "Jul", style_font)
        sheet.write(i, 3, "Aug", style_font)
        sheet.write(i, 4, "Sep", style_font)
        sheet.write(i, 5, "Oct", style_font)
        sheet.write(i, 6, "Nov", style_font)
        sheet.write(i, 7, "Dec", style_font)
        sheet.write(i, 8, "Jan", style_font)
        sheet.write(i, 9, "Feb", style_font)
        sheet.write(i, 10, "Mar", style_font)
        sheet.write(i, 11, "Apr", style_font)
        sheet.write(i, 12, "May", style_font)
        sheet.write(i, 13, "Jun", style_font)

        i = 5
        for row in salary_data:   
            sheet.write(i, 0, row["details"])
            sheet.write(i, 1, row["year"])
            sheet.write(i, 2, row["jul"], style_number)
            sheet.write(i, 3, row["aug"], style_number)
            sheet.write(i, 4, row["sep"], style_number)
            sheet.write(i, 5, row["oct"], style_number)
            sheet.write(i, 6, row["nov"], style_number)
            sheet.write(i, 7, row["dec"], style_number)
            sheet.write(i, 8, row["jan"], style_number)
            sheet.write(i, 9, row["feb"], style_number)
            sheet.write(i, 10, row["mar"], style_number)
            sheet.write(i, 11, row["apr"], style_number)
            sheet.write(i, 12, row["may"], style_number)
            sheet.write(i, 13, row["jun"], style_number)
            i=i+1


        #create dir
        folder = "/odoo/files/salary_tracker/"
        if not os.path.exists(folder):
            os.makedirs(folder)

        #remove files
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                #elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)
            
        #output
        file_name_with_path = folder + file_name + ".xls"
        workbook.save(file_name_with_path)

        list_data = self.env['ir.filesystem.directory'].search([('directory', '=', '/odoo/files/salary_tracker/')])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Downloads',
            'res_model': 'ir.filesystem.directory',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
            'res_id': list_data['id'],
        }
