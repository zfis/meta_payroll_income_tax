from odoo import api, fields, models, tools, _
from odoo.addons.bus.models.bus import json_dump
import json


class IncomeTax(models.Model):

    _name = 'income.tax'

    income_tax_year = field_name = fields.Char(string='Income Tax year')
    assessment_year = field_name = fields.Char(string='Assessment Year')
    min_tax_amount = field_name = fields.Float(string='Min Tax Amount')

    house_rent_exemption = fields.Integer(string='House Rent Exemption')
    house_rent_exemption_fix = fields.Float(string='House Rent Exemption Fix')
    medical_exemption = fields.Integer(string='Medical Exemption')
    medical_exemption_fix = fields.Float(string='Medical Exemption Fix')
    conveyance_exemption = fields.Float(string='Conveyance Exmption')

    slab_1 = fields.Float(string='On the First')
    slab_1_female_or_senior = fields.Float(string='Female/Senior')
    slab_1_disabled = fields.Float(string='Disabled')
    slab_1_freedom_fighter = fields.Float(string='Freedom Fighter')
    slab_1_disabled_parent_or_legal_guardian = fields.Float(string='Disable Parent/Legal Gurdian')

    slab_2 = fields.Float(string='On the Next')
    slab_3 = fields.Float(string='On the Next')
    slab_4 = fields.Float(string='On the Next')
    slab_5 = fields.Float(string='On the Next')
    slab_6 = fields.Float(string='On the Balance')

    tax_rate_first_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_second_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_third_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_fourth_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_fifth_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_sixth_slab = fields.Integer(string='Tk., Tax rate (%)')
    tax_rate_non_resident = fields.Integer(string='Tax rate for Non Resident (%)')

    tax_rebate_investment_ratio = fields.Integer(string='Max Investment Ratio (%)')
    tax_rebate_investment_fix = fields.Float(string='Max Investment Fix')

    tax_rebate_slab_one = fields.Integer(string='Tax Rebate First Slab')
    tax_rebate_slab_two = fields.Integer(string='Tax Rebate Two Slab')
    tax_rebate_slab_three = fields.Integer(string='Tax Rebate Three Slab')

    tax_rebate_rate_slab_one = fields.Float(string='%')
    tax_rebate_rate_slab_two = fields.Float(string='%')
    tax_rebate_rate_slab_three = fields.Float(string='%')

    taxable_income_limit = fields.Integer(string='Tax Rebate Income Limit')
    tax_rebate_lower_rate = fields.Integer(string='%')
    tax_rebate_higher_rate = fields.Integer(string='%')