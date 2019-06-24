#################################################
from odoo import api, fields, models, tools, _
from odoo.addons.bus.models.bus import json_dump
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import json

class Challan(models.Model):

    _name = 'tax.challan'

    name = fields.Char(string='Challan Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        default=lambda self: self.env['res.company']._company_default_get())
    payroll_month = fields.Selection([
        ('01','Jan'),
        ('02','Feb'),
        ('03','Mar'),
        ('04','Apr'),
        ('05','May'),
        ('06','Jun'),
        ('07','Jul'),
        ('08','Aug'),
        ('09','Sep'),
        ('10','Oct'),
        ('11','Nov'),
        ('12','Dec')], 
        string='Payroll Month', 
        required=True) 
    payroll_year = fields.Selection([
        ('2018','2018'),
        ('2019','2019')], 
        default='2018', 
        string='Payroll Year', 
        required=True)
    cheque_no = fields.Char(string='Cheque No')
    cheque_date = fields.Date(string='Cheque Date')
    bank_name = fields.Char(string='Bank')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    line_ids = fields.One2many('tax.challan.line', 'challan_id', string='Challan Lines', readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(string='Challan No')
    submission_date = fields.Date(string='Submission Date')
    tds_amount_total = fields.Integer(string='TDS Total', readonly=True)

    @api.multi
    def confirm_challan_run(self):
        if not self.number or not self.submission_date:
            raise UserError(_('Challan no and submission date required to confirm!'))

        return self.write({'state': 'confirm'})

    @api.multi
    def draft_challan_run(self):
        return self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        if self.state in ('confirm'): 
            raise UserError(_('You cannot delete a challan which is not draft!'))

        return super(Challan, self).unlink()
        
    @api.onchange('payroll_month', 'payroll_year')
    def onchange_challan_date(self):
        
        if (not self.payroll_month) or (not self.payroll_year):
            return

        self.name = _('Challan of %s for %s/%s') % (self.company_id.name, self.payroll_month, self.payroll_year,)
        
        return

    @api.multi
    def challan_tds_calculation_run(self):

        #delete exists employee challans
        self.line_ids.unlink()

        #create new employee challans
        tds_amount_total = 0
        #employees = self.env['hr.employee'].search([]) #search([('company_id', '==', [self.company_id.id])])
        # note: employee.company_id.id, employee.id
        self.env.cr.execute("""SELECT emp.id FROM hr_employee emp 
                                LEFT JOIN hr_department dept 
                                ON dept.id = emp.department_id 
                                WHERE dept.company_id=%s
                                """ % (self.company_id.id,))
        employees = self.env.cr.dictfetchall()
        
        for employee in employees:
            #if employee['company_id'] == self.company_id.id:
            try:
                self.env.cr.execute("""SELECT monthly_tax_payable FROM hr_payslip 
                                        WHERE employee_id=%s AND
                                        EXTRACT(YEAR FROM date_from)=%s AND
                                        EXTRACT(MONTH FROM date_from)=%s
                                        """ % (employee['id'],self.payroll_year,self.payroll_month,))
                queryData = self.env.cr.dictfetchall()
                tds_amount = queryData[0]["monthly_tax_payable"]
                tds_amount_total += int(tds_amount)
            except Exception, e: 
                tds_amount = 0

            if tds_amount > 0:
                lines = [(0, 0, {'employee_id': employee['id'], 'tds_amount': tds_amount})]
                self.write({'line_ids': lines})

        self.tds_amount_total = tds_amount_total

        return True

    @api.onchange('tds_amount')
    def onchange_get_tds_amt_total(self):  
        
        tds_amount_total = 0
        for line in self.line_ids:
            tds_amount_total += line.tds_amount
        self.tds_amount_total = tds_amount_total

        return True

    @api.multi
    def run_sql(self,num,join=True):

        units = ['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine']
        teens = ['','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen', \
                'Seventeen','Eighteen','Nineteen']
        tens = ['','Ten','Twenty','Thirty','Forty','Fifty','Sixty','Seventy', \
                'Eighty','Ninety']
        thousands = ['','Thousand','Million','Billion','Trillion','Quadrillion', \
                    'Quintillion','Sextillion','Septillion','Octillion', \
                    'Nonillion','Decillion','Undecillion','Duodecillion', \
                    'Tredecillion','Quattuordecillion','Sexdecillion', \
                    'Septendecillion','Octodecillion','Novemdecillion', \
                    'Vigintillion']
        words = []
        if num==0: words.append('Zero')
        else:
            numStr = '%d'%num
            numStrLen = len(numStr)
            groups = (numStrLen+2)/3
            numStr = numStr.zfill(groups*3)
            for i in range(0,groups*3,3):
                h,t,u = int(numStr[i]),int(numStr[i+1]),int(numStr[i+2])
                g = groups-(i/3+1)
                if h>=1:
                    words.append(units[h])
                    words.append('Hundred')
                if t>1:
                    words.append(tens[t])
                    if u>=1: words.append(units[u])
                elif t==1:
                    if u>=1: words.append(teens[u])
                    else: words.append(tens[t])
                else:
                    if u>=1: words.append(units[u])
                if (g>=1) and ((h+t+u)>0): words.append(thousands[g])
        if join: return ' '.join(words)

        return words


class ChallanLine(models.Model):
    _name = 'tax.challan.line'

    challan_id = fields.Many2one('tax.challan', string='Challan', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    tds_amount = fields.Float(string='TDS', digits=dp.get_precision('Payroll'))

    # @api.onchange('tds_amount')
    # def _onchange_get_tds_amt_total(self):  
        
    #     challan = self.env['tax.challan'].browse(self.challan_id)
    #     tds_amount_total = 0
    #     for line in challan.line_ids:
    #           tds_amount_total += line.tds_amount
    #     self.challan_id.tds_amount_total = tds_amount_total
    #     #challan.write({'tds_amount_total':tds_amount_total})
    #return True


class Company(models.Model):
    
    _inherit = 'res.company'

    challan_code = fields.Char(string='Code')