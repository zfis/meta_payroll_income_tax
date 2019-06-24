# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import os, shutil

import logging
_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Can not import xls writer`.')


class PayrollTracker(models.TransientModel):

    _name = 'payroll.tracker'
    _description = 'Payroll Tracker'

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

    payroll_year = fields.Selection([
        ('2018','2018-2019'),
        ('2019','2019-2020')], 
        default='2018', 
        string='Payroll Year', 
        required=True)
 
    hr_field = fields.Many2many('hr.field', string="Employee Info", domain="[('report_name','=','payroll_tracker')]")

    @api.multi
    def print_report(self):      
        self.ensure_one()
        [data] = self.read()
        company = self.env['res.company']._company_default_get()
        data['company_id'] = company.id
        data['company_name'] =  company.name
        companies = self.env['res.company'].browse(data['company_id'])
        datas = {
            'ids': [],
            'model': 'res.company',
            'form': data,
        }
        return self.env['report'].get_action(companies, 'income.payroll_tracker_id', data=datas)

    @api.multi
    def export_excel(self):     
        
        payroll_year = int(self.payroll_year)
        if int(self.payroll_month) >= 1 and int(self.payroll_month) <= 6:
            payroll_year = int(self.payroll_year) + 1

        company_id = self.env['res.company']._company_default_get()   

        month_name = datetime.date(int(payroll_year), int(self.payroll_month), 1).strftime('%B')
        file_name = "Payroll Tracker - " + company_id.name + " - " + month_name + " " + str(payroll_year)

        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Salary Tracker")

        #set style
        style_head = xlwt.easyxf('font: bold on, height 280; align: horiz center;')
        style_subhead = xlwt.easyxf('font: bold on, height 200; align: horiz center;')
        style_font = xlwt.easyxf('font: bold on')
        style_number = xlwt.easyxf(num_format_str='#,##0')

        #set data
        self.env.cr.execute("""SELECT
                        code,
                        MIN(name) as name
                        FROM hr_salary_rule
                        WHERE company_id=%s
                        GROUP BY code 
                        ORDER BY MIN(sequence)
                        """ % (company_id.id,))
        rule_data = self.env.cr.dictfetchall()   

        sheet.write_merge(0, 1, 0, len(rule_data)+1, company_id.name, style_head)
        sub_head = "Payroll Tracker for " + self.payroll_month + "/" + str(payroll_year)
        sheet.write_merge(2, 2, 0, len(rule_data)+1, sub_head, style_subhead)

        i = 4
        sheet.write(i, 0, "Name of Employee", style_font)
        sheet.write(i, 1, "Status", style_font)

        j = 2
        add_query_1 = ""
        add_query_2 = ""
        for field in self.hr_field:  
            sheet.write(i, j, field['name'], style_font) 
            #add_query_1 += "MIN(" + field['key'] + ") AS " + field['key'] + ", "
            #add_query_2 += "employee." + field['key'] + " AS " + field['key'] + ", "
            j = j+1

        for rule in rule_data:  
            sheet.write(i, j, rule["name"], style_font)
            j = j+1

        try:
            self.env.cr.execute("""SELECT emp_id, MIN(emp_name) as emp_name, MIN(state) as state, json_object_agg(code,amount) AS json_data
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
                                    GROUP BY emp_id
                                    ORDER BY emp_name
                                    """ % (company_id.id, payroll_year, self.payroll_month,))
            payslip_data = self.env.cr.dictfetchall()   
        except Exception, e:
            raise UserError(_(str(e)))

        i = 5
        for payslip in payslip_data:     

            state = 'DF'
            if payslip["state"] == 'done':
                state = 'DN'            

            sheet.write(i, 0, payslip["emp_name"])
            sheet.write(i, 1, state)

            k = 2
            employee_data = self.env['hr.employee'].browse(int(payslip["emp_id"]))
            for field in self.hr_field:   
                #sheet.write(i, k, payslip[str(field['key'])]) 
                sheet.write(i, k, eval('employee_data.' + str(field['key'])))     
                k = k+1

            for rule in rule_data:  
                code = str(rule["code"])
                if code in payslip['json_data']:
                    sheet.write(i, k, payslip['json_data'][code], style_number)
                k = k+1

            i=i+1

        # j = 2
        # for rule in rule_data: 
        #     sheet.write(i, j, xlwt.Formula("SUM(A" + str() + ":B" + str(i-)))
        #     k = k+1

        #create dir
        folder = "/odoo/files/payroll_tracker/"
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

        list_data = self.env['ir.filesystem.directory'].search([('directory', '=', '/odoo/files/payroll_tracker/')])
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Downloads',
            'res_model': 'ir.filesystem.directory',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
            'res_id': list_data['id'],
        }


        '''
            self.env.cr.execute("""SELECT emp_id, MIN(emp_name) as emp_name, MIN(state) as state, %s json_object_agg(code,amount) AS json_data
                                    FROM ( 
                                    SELECT
                                    employee.id AS emp_id,
                                    employee.name_related AS emp_name,
                                    payslipline.code AS code,
                                    payslipline.name AS title,
                                    %s
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
                                    GROUP BY emp_id
                                    ORDER BY emp_name
                                    """ % (add_query_1, add_query_2, company_id.id, payroll_year, self.payroll_month,))
            payslip_data = self.env.cr.dictfetchall()   
        '''