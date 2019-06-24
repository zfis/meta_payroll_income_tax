# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrField(models.Model):
    _name = 'hr.field'
    _order = 'sequence'


    def _get_fields(self):
        
        self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='hr_employee' AND data_type!='boolean'")
        query_data = self.env.cr.dictfetchall()

        lst = []
        for obj in query_data:
            key = obj['column_name']

            self.env.cr.execute("""SELECT field_description FROM ir_model_fields WHERE model='hr.employee' AND name=%s """, (obj['column_name'],))
            query_data = self.env.cr.dictfetchall()

            if len(query_data) > 0:

                if key[-3:] == '_id':
                    lst.append((key + '.name', query_data[0]['field_description']))
                elif key[-4:] != '_ids' and key[-4:] != '_uid': #key[-3:] != '_id' and
                    lst.append((key, query_data[0]['field_description']))
                
        #lst.append(('department_id.name', 'Department'))
        #lst.append(('job_id.name', 'Job Title'))
        
        def sortSecond(val): 
            return val[1]  

        lst.sort(key=sortSecond)

        return lst


    def _get_reports(self):      
        lst = []
        lst.append(('payslip', 'Payslip'))
        lst.append(('tax_card', 'Income Tax Card'))
        lst.append(('payroll_tracker', 'Payroll Tracker'))
        return lst


    @api.onchange('key')
    def on_change_key(self):

        if self.key:
            self.env.cr.execute("""SELECT field_description FROM ir_model_fields WHERE model='hr.employee' AND name=%s """, (self.key.split(".")[0],))
            query_data = self.env.cr.dictfetchall()
            
            if len(query_data) > 0:
                self.name = query_data[0]['field_description']
        
        self.company_id = self.env['res.company']._company_default_get().id

       
    key = fields.Selection(_get_fields, string='Field', required=True)
    name = fields.Char('Label', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    report_name = fields.Selection(_get_reports, string='Apply to', required=True)
    sequence = fields.Integer(required=True, index=True, default=1, string='Sequence')