# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.addons.bus.models.bus import json_dump
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import calendar
import time
from datetime import datetime
from datetime import date
import json
import re
import traceback, sys


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    fiscal_year = fields.Selection([('2018','2018-2019'),('2019','2019-2020')], default='2018', string='Fiscal Year', required=True) 
    basic_total = fields.Float("Basic Gross", readonly=True)
    income_total = fields.Float("Income Gross", readonly=True)
    hr_exemption = fields.Float("HR Exemption", readonly=True)
    med_exemption = fields.Float("Med. Exemption", readonly=True)
    conv_exemption = fields.Float("Conv. Exemption", readonly=True)
    exemption_total = fields.Float("Total Exemption", readonly=True)
    taxable_income_total = fields.Float("Total Taxable Income", readonly=True)
    tax_liability_total = fields.Float("Tax Liability", readonly=True)
    tax_rebate_total = fields.Float("Investment Rebate", readonly=True)
    tax_payable_total = fields.Float("Tax Payable", readonly=True)
    tax_paid_total = fields.Float("Tax Paid", readonly=True)
    remain_tax_payable = fields.Float("Remaining Tax Payable", readonly=True)
    remain_month = fields.Integer("Remaining Months", readonly=True)
    partial_month = fields.Integer("Partial Months", readonly=True)
    monthly_tax_payable = fields.Float("Current Month Tax", readonly=True)
    max_allowable_investment_limit = fields.Float("Max Allow Inv Limit", readonly=True)
    employee_code = fields.Char(related='employee_id.employee_code', store=True)
    sf_id_2 = fields.Integer("SF ID", compute='get_sf_id_data')
    sf_id = fields.Integer("SF ID")
    work_location_type = fields.Char("Location Type", compute='get_location_type_data')
    work_location_type_2 = fields.Char("Location Type")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env['res.company']._company_default_get())

    @api.multi
    def get_sf_id_data(self):
        for item in self:
            item.sf_id_2 = item.employee_id.sf_id_2
            item.write({
                'sf_id':item.employee_id.sf_id_2,
            })

    @api.multi
    def get_location_type_data(self):
        for item in self:
            item.work_location_type = item.employee_id.work_location_type
            item.write({
                'work_location_type_2':item.employee_id.work_location_type,
            })

    @api.onchange('date_start', 'date_end')
    def onchange_payslip_batch_date(self):
        
        if (not self.date_start) or (not self.date_end):
            return

        date_from = self.date_start

        # Set end of month
        end_year = date_from.split('-')[0]
        end_month = date_from.split('-')[1]
        last_day = calendar.monthrange(int(end_year), int(end_month))[1]
        end_date_to = str(end_year) + "-" + str(end_month) + "-" + str(last_day)
        self.date_end = end_date_to

        return

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


    # Final Goal = Getting Monthly Tax Payable

    # Initialize
    globalContractId = 0
    globalStructId = 0
    globalPartialMonth = 12
    globalLeaveStatus = False
    globalMaxAllowInvestmentLimit = 0
    global_tax_remain_month = 0
    global_contract_data = []

    globalFindProvidendFund = False
    globalTaxDateTo = 0
    globalLiabilitySlabRecord = [0, 0, 0, 0, 0, 0]
    globalRebateSlabRecord = [0, 0, 0]

    ##
    global_basic_with_alw_total = 0
    ##
    global_category_wise_ecpf_total = 0
    global_category_wise_basic_total = 0
    global_category_wise_pbasic_total = 0
    global_category_wise_alw_total = 0
    global_category_wise_oalw_total = 0
    global_category_wise_comp_total = 0
    global_category_wise_ncalw_total = 0
    global_category_wise_psal_total = 0
    global_category_wise_aitax_total = 0
    global_category_wise_balw_total = 0
    ##
    global_rulewise_phra_total = 0
    global_rulewise_pmal_total = 0
    global_rulewise_pcal_total = 0
    ##
    global_allowance_hra_total = 0
    global_allowance_malw_total = 0
    global_allowance_calw_total = 0
    ##
    global_category_done_itax_total = 0
    global_category_done_ptax_total = 0
   
    def get_tax_year_range(self):
        taxStartYear = self.fiscal_year
        taxYearRange = taxStartYear + "-" + str(int(taxStartYear) + 1)
        return taxYearRange
   
    def get_tax_date_from(self):
        dateFrom = self.fiscal_year + "-07-01"
        return dateFrom
    
    def get_tax_date_to(self):
        dateTo = str(int(self.fiscal_year) + 1) + "-06-30"
        if self.globalFindProvidendFund == True:
            dateTo = self.globalTaxDateTo  
        return dateTo

    def get_tax_remain_month(self):

        query = "SELECT payslip.date_from, COUNT(payslip.id) counter FROM hr_payslip payslip LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id WHERE payslip.employee_id=%s AND payslip.date_from BETWEEN %s AND %s AND code='GROSS' AND (payslip.state='done' OR payslip.state='draft') GROUP BY payslip.date_from ORDER BY payslip.date_from ASC"
        params = (
            self.employee_id.id,
            self.get_tax_date_from(),
            self.get_tax_date_to(),
        )
        self.env.cr.execute(query, params)
        data = self.env.cr.dictfetchall()

        self.globalPartialMonth = 12

        if (len(data) > 0):
            remainMonth = 12 - len(data)
        else:
            remainMonth = 12

        startMonth = '07'
        if (len(data) > 0):
            startMonth = data[0]["date_from"].split('-')[1]

        #check employee partial month 
        if (startMonth != '07'):

            arrFirstHalfMonth = ['01', '02', '03', '04', '05', '06']

            if startMonth in arrFirstHalfMonth:
                remainMonth = 7 - int(startMonth) - len(data) #6 - len(data)
                self.globalPartialMonth = 7 - int(startMonth)
            else:
                remainMonth = 19 - int(startMonth) - len(data) #18 - len(data)
                self.globalPartialMonth = 19 - int(startMonth)

        #check employee leave month 
        query = "SELECT leaving_date FROM hr_employee WHERE id=%s"
        params = (self.employee_id.id, )
        self.env.cr.execute(query, params)
        employeeData = self.env.cr.dictfetchall()
        leaving_date = employeeData[0]['leaving_date'] or ""

        self.globalLeaveStatus = False
        if leaving_date and len(data) > 0:            
            leave_year = int(leaving_date.split('-')[0])  
            leave_month = int(leaving_date.split('-')[1])                   
            payslip_year = int(data[len(data)-1]["date_from"].split('-')[0])
            payslip_month = int(data[len(data)-1]["date_from"].split('-')[1])

            if(leave_year == payslip_year and leave_month == payslip_month):   

                remainMonth = 0
                self.globalPartialMonth = len(data)
                self.globalLeaveStatus = True

        return remainMonth

    def get_basic_salary(self):

        salaryData = self.global_contract_data

        basicSalary = 0

        if (len(salaryData) > 0):

            basicSalary = salaryData[0]['wage']

            self.globalStructId = salaryData[0]['struct_id']
            self.globalContractId = salaryData[0]['id']

        return basicSalary

    def get_employee_basicwithalw_total(self):
        
        self.env.cr.execute("""SELECT SUM(payslipLine.amount) total
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done' OR payslip.state='draft')      
            AND payslip.employee_id=%s 
            AND payslip.id=%s 
            AND (categoryRule.code='BASIC' OR categoryRule.code='ALW' OR categoryRule.code='ECPF' OR categoryRule.code='NCALW')""", 
            (self.employee_id.id, self.id))

        data = self.env.cr.dictfetchall()

        basicWithAlwMonthlyTotal = 0
        if (len(data) > 0):
            basicWithAlwMonthlyTotal = data[0]["total"] or 0

        return basicWithAlwMonthlyTotal
    
    
    def get_categorywise_total(self, categoryCode):
        
        self.env.cr.execute("""SELECT SUM(payslipLine.total) total 
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done' OR payslip.state='draft') 
            AND payslip.date_from BETWEEN %s AND %s 
            AND payslip.employee_id=%s 
            AND categoryRule.code=%s
            GROUP BY categoryRule.code""", 
            (self.get_tax_date_from(), self.get_tax_date_to(), self.employee_id.id, categoryCode))

        categorywiseData = self.env.cr.dictfetchall()

        categorywiseTotal = 0
        if (len(categorywiseData) > 0):
            categorywiseTotal = categorywiseData[0]["total"] or 0

        return categorywiseTotal

   
    def get_categorywise_done_total(self, categoryCode):
        
        self.env.cr.execute("""SELECT SUM(payslipLine.total) total 
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done') 
            AND payslip.date_from BETWEEN %s AND %s 
            AND payslip.employee_id=%s 
            AND categoryRule.code=%s
            GROUP BY categoryRule.code""", 
            (self.get_tax_date_from(), self.get_tax_date_to(), self.employee_id.id, categoryCode))

        categorywiseData = self.env.cr.dictfetchall()

        categorywiseTotal = 0
        if (len(categorywiseData) > 0):
            categorywiseTotal = categorywiseData[0]["total"] or 0

        return categorywiseTotal

    
    def get_rulewise_total(self, ruleCode):
        
        self.env.cr.execute("""SELECT SUM(payslipLine.total) total 
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            WHERE (payslip.state='done' OR payslip.state='draft')      
            AND payslip.date_from BETWEEN %s AND %s 
            AND payslip.employee_id=%s 
            AND payslipLine.code=%s
            GROUP BY payslipLine.code""", 
            (self.get_tax_date_from(), self.get_tax_date_to(), self.employee_id.id, ruleCode))

        rulewiseData = self.env.cr.dictfetchall()

        rulewiseTotal = 0
        if len(rulewiseData) > 0:
            rulewiseTotal = rulewiseData[0]["total"]

        return rulewiseTotal

    
    def get_categorywise_annual_total(self, code):
    
        self.env.cr.execute("""SELECT SUM(payslipLine.amount) total
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            LEFT JOIN hr_salary_rule_category categoryRule ON categoryRule.id=payslipLine.category_id 
            WHERE (payslip.state='done' OR payslip.state='draft')      
            AND payslip.employee_id=%s 
            AND payslip.id=%s 
            AND categoryRule.code=%s""", 
            (self.employee_id.id, self.id, code))

        data = self.env.cr.dictfetchall()

        categorywiseAnnualTotal = self.global_category_wise_ecpf_total # previous stored amount
        if data[0]["total"] is not None and len(data) > 0:
            categorywiseAnnualTotal += (data[0]["total"] * self.global_tax_remain_month)

        return categorywiseAnnualTotal

    
    def get_yearly_basic_total(self):
        
        basicSalaryTotal = self.global_category_wise_basic_total + ( 
            self.get_basic_salary() * self.global_tax_remain_month)

        # Add previous basic salary total
        basicSalaryTotal += self.global_category_wise_pbasic_total

        return basicSalaryTotal


    def get_yearly_income_total(self):

        #add this function later here: get_categorywise_annual_total()

        prevGrossPaid = self.global_category_wise_basic_total + self.global_category_wise_alw_total + self.global_category_wise_oalw_total + self.global_category_wise_comp_total + self.global_category_wise_ecpf_total + self.global_category_wise_ncalw_total + self.global_category_wise_balw_total
        yearlyIncomeTotal = prevGrossPaid + (self.global_basic_with_alw_total * self.global_tax_remain_month)

        # Add previous yearly salary total
        yearlyIncomeTotal += self.global_category_wise_psal_total

        return yearlyIncomeTotal

   
    def get_allowance_total(self, allowanceCode):

        self.env.cr.execute("""SELECT SUM(payslipLine.amount) total, MIN(payslipLine.rate) rate
            FROM hr_payslip payslip 
            LEFT JOIN hr_payslip_line payslipLine ON payslipLine.slip_id=payslip.id 
            WHERE (payslip.state='done' OR payslip.state='draft')      
            AND payslip.employee_id=%s 
            AND payslip.id=%s 
            AND payslipLine.code=%s""", 
            (self.employee_id.id, self.id, allowanceCode))

        data = self.env.cr.dictfetchall()

        allowance = 0
        if len(data) > 0:
            allowance = data[0]["total"] or 0

        allowanceTotal = self.get_rulewise_total(allowanceCode) + (
            allowance * self.global_tax_remain_month)

        return allowanceTotal

    
    def get_tax_rule_data(self):

        query = "SELECT * FROM income_tax WHERE income_tax_year=%s"
        params = (self.get_tax_year_range(), )
        self.env.cr.execute(query, params)
        taxRuleData = self.env.cr.dictfetchall()[0]

        if (len(taxRuleData) <= 0):
            raise UserError(_('No income tax rule data found.'))

        return taxRuleData

   
    def get_house_rent_exemption_amt(self):

        taxRuleData = self.get_tax_rule_data()

        ratioOfBasicAmount = self.get_yearly_basic_total() * (taxRuleData["house_rent_exemption"] / 100.00)

        houseRentAllowanceTotal = self.global_allowance_hra_total

        houseRentExemptionFixedAmt = taxRuleData["house_rent_exemption_fix"] * self.globalPartialMonth

        if (ratioOfBasicAmount < houseRentAllowanceTotal):
            houseRentExemptionAmt = ratioOfBasicAmount
        else:
            houseRentExemptionAmt = houseRentAllowanceTotal

        if (houseRentExemptionFixedAmt < houseRentExemptionAmt):
            houseRentExemptionAmt = houseRentExemptionFixedAmt

        # Add previous house rent allowance
        houseRentExemptionAmt += self.global_rulewise_phra_total

        return houseRentExemptionAmt

   
    def get_medical_exemption_amt(self):

        taxRuleData = self.get_tax_rule_data()

        ratioOfBasicAmount = self.get_yearly_basic_total() * (
            taxRuleData["medical_exemption"] / 100.00)

        medicalAllowanceTotal = self.global_allowance_malw_total

        medicalExemptionFixedAmt = taxRuleData["medical_exemption_fix"]

        if (ratioOfBasicAmount < medicalAllowanceTotal):
            medicalExemptionAmt = ratioOfBasicAmount
        else:
            medicalExemptionAmt = medicalAllowanceTotal

        if (medicalExemptionFixedAmt < medicalExemptionAmt):
            medicalExemptionAmt = medicalExemptionFixedAmt

        # Add previous medical allowance
        medicalExemptionAmt += self.global_rulewise_pmal_total

        return medicalExemptionAmt


    def get_conveyance_exemption_amt(self):

        taxRuleData = self.get_tax_rule_data()

        conveyanceExemptionFixedAmt = taxRuleData["conveyance_exemption"] 

        conveynaceAllowanceTotal = self.global_allowance_calw_total

        if (conveynaceAllowanceTotal < conveyanceExemptionFixedAmt):
            conveyanceExemptionAmt = conveynaceAllowanceTotal
        else:
            conveyanceExemptionAmt = conveyanceExemptionFixedAmt

        # Add previous conveyance allowance
        conveyanceExemptionAmt += self.global_rulewise_pcal_total

        return conveyanceExemptionAmt

    
    def get_tax_exemption_total(self):

        taxExemptionTotal = self.get_house_rent_exemption_amt(
        ) + self.get_medical_exemption_amt(
        ) + self.get_conveyance_exemption_amt()

        return taxExemptionTotal

    
    def get_taxable_income_total(self):

        taxableIncomeTotal = self.get_yearly_income_total(
        ) - self.get_tax_exemption_total()

        # Add bonus tax amount
        # contractData = self.global_contract_data
        
        # if (len(contractData) > 0):      
        #     if (contractData[0]['allow_tax_for_bonuse'] == True):
        #         taxableIncomeTotal += contractData[0]['bonus_amount']

        return taxableIncomeTotal

    
    def get_tax_liability_total(self, findTaxCardReport=False, tempTotalTaxableIncome = 0):   

        query = "SELECT gender,birthday, is_disabled, is_freedom_fighter, is_disabled_parent_or_legal_guardian, residency FROM hr_employee WHERE id=%s"
        params = (self.employee_id.id, )
        self.env.cr.execute(query, params)
        employeeData = self.env.cr.dictfetchall()[0]

        if (len(employeeData) <= 0):
            raise UserError(_('No employee data found.'))

        taxRuleData = self.get_tax_rule_data()

        birthdayVals = employeeData['birthday'].split('-')
        today = date.today()
        age = today.year - int(birthdayVals[0]) - (
            (today.month, today.day) <
            (int(birthdayVals[1]), int(birthdayVals[2])))

        slab1CalAmount = 0

        if (employeeData['gender'] == 'female' or age >= 65):
            slab1CalAmount = taxRuleData["slab_1_female_or_senior"]

        if (employeeData['is_disabled'] == True):
            slab1CalAmount = taxRuleData["slab_1_disabled"]

        if (employeeData['is_freedom_fighter'] == True):
            slab1CalAmount = taxRuleData["slab_1_freedom_fighter"]

        if (employeeData['is_disabled_parent_or_legal_guardian'] == True):
            slab1CalAmount += taxRuleData[
                "slab_1_disabled_parent_or_legal_guardian"]

        if (taxRuleData["slab_1"] > slab1CalAmount):
            slab1CalAmount = taxRuleData["slab_1"]

        ###############

        if findTaxCardReport == False:
            taxableIncomeTotal = self.get_taxable_income_total()
        else:
            taxableIncomeTotal = tempTotalTaxableIncome

        remainTaxableIncomeTotal = taxableIncomeTotal 

        taxLiabilityTotal = 0
        count = 0
        countStatus = False
        pauseSlabRatio = taxRuleData["tax_rate_first_slab"]

        if (remainTaxableIncomeTotal >= slab1CalAmount):
            remainTaxableIncomeTotal -= slab1CalAmount    
            taxLiabilityTotal += slab1CalAmount * (
                taxRuleData["tax_rate_first_slab"] / 100.00)
            pauseSlabRatio = taxRuleData["tax_rate_second_slab"]
            self.globalLiabilitySlabRecord[count] = slab1CalAmount
            countStatus = True

            if (remainTaxableIncomeTotal >= taxRuleData["slab_2"]):
                remainTaxableIncomeTotal -= taxRuleData["slab_2"]
                taxLiabilityTotal += taxRuleData["slab_2"] * (
                    taxRuleData["tax_rate_second_slab"] / 100.00)
                pauseSlabRatio = taxRuleData["tax_rate_third_slab"]
                count += 1
                self.globalLiabilitySlabRecord[count] = taxRuleData["slab_2"]

                if (remainTaxableIncomeTotal >= taxRuleData["slab_3"]):
                    remainTaxableIncomeTotal -= taxRuleData["slab_3"]
                    taxLiabilityTotal += taxRuleData["slab_3"] * (
                        taxRuleData["tax_rate_third_slab"] / 100.00)
                    pauseSlabRatio = taxRuleData["tax_rate_fourth_slab"]
                    count += 1
                    self.globalLiabilitySlabRecord[count] = taxRuleData["slab_3"]

                    if (remainTaxableIncomeTotal >= taxRuleData["slab_4"]):
                        remainTaxableIncomeTotal -= taxRuleData["slab_4"]
                        taxLiabilityTotal += taxRuleData["slab_4"] * (
                            taxRuleData["tax_rate_fourth_slab"] / 100.00)
                        pauseSlabRatio = taxRuleData["tax_rate_fifth_slab"]
                        count += 1
                        self.globalLiabilitySlabRecord[count] = taxRuleData["slab_4"]

                        if (remainTaxableIncomeTotal >= taxRuleData["slab_5"]):
                            remainTaxableIncomeTotal -= taxRuleData["slab_5"]
                            taxLiabilityTotal += taxRuleData["slab_5"] * (
                                taxRuleData["tax_rate_fifth_slab"] / 100.00)
                            pauseSlabRatio = taxRuleData["tax_rate_sixth_slab"]
                            count += 1
                            self.globalLiabilitySlabRecord[count] = taxRuleData["slab_5"]

        # Calculate rest money
        if (remainTaxableIncomeTotal > 0):
            taxLiabilityTotal += remainTaxableIncomeTotal * (
                pauseSlabRatio / 100.00)
            if countStatus == True:
                count += 1
            self.globalLiabilitySlabRecord[count] = remainTaxableIncomeTotal

        if (employeeData['residency'] == 'non-resident'):
            taxLiabilityTotal = taxableIncomeTotal * (taxRuleData["tax_rate_non_resident"] / 100.00)
            self.globalLiabilitySlabRecord = [taxLiabilityTotal, 0, 0, 0, 0, 0]

        return taxLiabilityTotal

    
    def get_tax_rebate_total(self, findTaxCardReport=False, tempMaxAllowInvestmentLimit = 0):

        taxRuleData = self.get_tax_rule_data()
        taxableIncomeTotal = self.get_taxable_income_total()

        # Get Contribution Fund
        #fundTotal = self.get_categorywise_annual_total('ECPF') 

        # Default rebate balue    
        #remainTaxableIncomeTotal = (taxableIncomeTotal - fundTotal) * (
        #    taxRuleData["tax_rebate_investment_ratio"] / 100.00)
        remainTaxableIncomeTotal = taxableIncomeTotal * (taxRuleData["tax_rebate_investment_ratio"] / 100.00)

        # Change tax liability based on allowing max investment rebate by contracts
        contractData = self.global_contract_data

        if len(contractData) > 0 and contractData[0]['allow_manual_investment_rebate'] == True:
            if contractData[0]['manual_investment_amount'] < remainTaxableIncomeTotal:
                remainTaxableIncomeTotal = contractData[0]['manual_investment_amount']

        if findTaxCardReport == True:
            remainTaxableIncomeTotal = tempMaxAllowInvestmentLimit

        self.globalMaxAllowInvestmentLimit = remainTaxableIncomeTotal

        taxRebateTotal = 0
        '''
        count = 0
        countStatus = False
        pauseSlabRatio = taxRuleData["tax_rebate_rate_slab_one"]

        if (remainTaxableIncomeTotal >= taxRuleData["tax_rebate_slab_one"]):
            remainTaxableIncomeTotal -= taxRuleData["tax_rebate_slab_one"]
            taxRebateTotal += taxRuleData["tax_rebate_slab_one"] * (
                taxRuleData["tax_rebate_rate_slab_one"] / 100.00)
            pauseSlabRatio = taxRuleData["tax_rebate_rate_slab_two"]
            self.globalRebateSlabRecord[count] = taxRuleData["tax_rebate_slab_one"]
            countStatus = True

            if (remainTaxableIncomeTotal >=
                    taxRuleData["tax_rebate_slab_two"]):
                remainTaxableIncomeTotal -= taxRuleData["tax_rebate_slab_two"]
                taxRebateTotal += taxRuleData["tax_rebate_slab_two"] * (
                    taxRuleData["tax_rebate_rate_slab_two"] / 100.00)
                pauseSlabRatio = taxRuleData["tax_rebate_rate_slab_three"]
                count += 1
                self.globalRebateSlabRecord[count] = taxRuleData["tax_rebate_slab_two"]

        # Calculate rest money
        if (remainTaxableIncomeTotal > 0):
            taxRebateTotal += remainTaxableIncomeTotal * (pauseSlabRatio / 100.00)
            if countStatus == True:
                count += 1
            self.globalRebateSlabRecord[count] = remainTaxableIncomeTotal
        '''

        # New Tax Rule Impact
        if taxableIncomeTotal > 0:
            if taxableIncomeTotal <= taxRuleData["taxable_income_limit"]:
                taxRebateTotal = remainTaxableIncomeTotal * (taxRuleData["tax_rebate_lower_rate"] / 100.00)
            else:
                taxRebateTotal = remainTaxableIncomeTotal * (taxRuleData["tax_rebate_higher_rate"] / 100.00)

        return taxRebateTotal

    
    def get_taxpayabletotal_by_misc_conditions(self):
        
        query = "SELECT gender,birthday, is_disabled, is_freedom_fighter, is_disabled_parent_or_legal_guardian FROM hr_employee WHERE id=%s"
        params = (self.employee_id.id, )
        self.env.cr.execute(query, params)
        employeeData = self.env.cr.dictfetchall()[0]

        birthdayVals = employeeData['birthday'].split('-')
        today = date.today()
        age = today.year - int(birthdayVals[0]) - (
            (today.month, today.day) <
            (int(birthdayVals[1]), int(birthdayVals[2])))

        taxRuleData = self.get_tax_rule_data()
        totalTaxableIncome = self.get_taxable_income_total()
        taxPayableTotal = -1
        slabCalAmount = 0
        slabCond = False

        if ((employeeData['gender'] == 'female' or age >= 65) and totalTaxableIncome < taxRuleData["slab_1_female_or_senior"]):
            taxPayableTotal = 0
            slabCalAmount = taxRuleData["slab_1_female_or_senior"]
            slabCond = True

        if (employeeData['is_disabled'] == True and totalTaxableIncome < taxRuleData["slab_1_disabled"]):
            taxPayableTotal = 0
            slabCalAmount = taxRuleData["slab_1_disabled"]
            slabCond = True

        if (employeeData['is_freedom_fighter'] == True and totalTaxableIncome < taxRuleData["slab_1_freedom_fighter"]):
            taxPayableTotal = 0
            slabCalAmount = taxRuleData["slab_1_freedom_fighter"]
            slabCond = True

        if (employeeData['is_disabled_parent_or_legal_guardian'] == True and (slabCalAmount + taxRuleData["slab_1_disabled_parent_or_legal_guardian"])):
            taxPayableTotal = 0
            slabCond = True

        if (slabCond == False and totalTaxableIncome < taxRuleData["slab_1"]):
            taxPayableTotal = 0

        return taxPayableTotal

    
    def get_tax_payable_total(self):

        taxPayableTotal = self.get_tax_liability_total(
        ) - self.get_tax_rebate_total()
   
        checkTaxPayableTotal = self.get_taxpayabletotal_by_misc_conditions()
        taxRuleData = self.get_tax_rule_data()

        if (checkTaxPayableTotal == -1 and taxPayableTotal < taxRuleData["min_tax_amount"]):
            taxPayableTotal = 5000
        elif checkTaxPayableTotal != -1:
            taxPayableTotal = checkTaxPayableTotal

        return taxPayableTotal

  
    def get_tax_paid_total(self):

        # (income tax paid + advance income tax paid)
        paidTaxTotal = self.global_category_done_itax_total + self.global_category_wise_aitax_total      

        # (previous income tax paid)
        paidTaxTotal +=  self.global_category_done_ptax_total

        # New code to test
        if (paidTaxTotal < 0):
            paidTaxTotal = paidTaxTotal * (-1)

        return paidTaxTotal

    
    def get_remain_tax_payable_total(self):

        remainTaxPayableTotal = self.get_tax_payable_total(
        ) - self.get_tax_paid_total()

        if remainTaxPayableTotal < 0:
            remainTaxPayableTotal = 0

        # if globalLeaveStatus == True:
        #     remainTaxPayableTotal = 0

        return remainTaxPayableTotal


    def tax_calculate_action(self):

        try:
        
            self.globalContractId = 0
            self.globalStructId = 0
            self.globalPartialMonth = 12
            self.globalLeaveStatus = False
            self.globalMaxAllowInvestmentLimit = 0  
            self.globalFindProvidendFund = False

            # Start checking contract data is found or not
            query = "SELECT * FROM hr_contract WHERE employee_id=%s ORDER BY date_start DESC"
            params = (self.employee_id.id,)
            self.env.cr.execute(query, params)
            contractData = self.env.cr.dictfetchall()
            self.global_contract_data = contractData
            if len(contractData) <= 0:
                raise UserError("No contract found created for " + self.employee_id.name)

            #global
            self.global_tax_remain_month = self.get_tax_remain_month()
            self.global_basic_with_alw_total = self.get_employee_basicwithalw_total()
            #global
            self.global_category_wise_ecpf_total = self.get_categorywise_total('ECPF')
            self.global_category_wise_basic_total = self.get_categorywise_total('BASIC')
            self.global_category_wise_pbasic_total = self.get_categorywise_total('PBASIC')
            self.global_category_wise_alw_total = self.get_categorywise_total('ALW')
            self.global_category_wise_oalw_total = self.get_categorywise_total('OALW')
            self.global_category_wise_comp_total = self.get_categorywise_total('COMP')
            self.global_category_wise_ncalw_total = self.get_categorywise_total('NCALW')
            self.global_category_wise_psal_total = self.get_categorywise_total('PSAL')
            self.global_category_wise_aitax_total = self.get_categorywise_total('AITAX')
            self.global_category_wise_balw_total = self.get_categorywise_total('BALW')
            #global
            self.global_rulewise_phra_total = self.get_rulewise_total('PHRA')
            self.global_rulewise_pmal_total = self.get_rulewise_total('PMAL')
            self.global_rulewise_pcal_total = self.get_rulewise_total('PCAL')
            #global
            self.global_allowance_hra_total = self.get_allowance_total('HRA')
            self.global_allowance_malw_total = self.get_allowance_total('MALW')
            self.global_allowance_calw_total = self.get_allowance_total('CALW')
            #global
            self.global_category_done_itax_total = self.get_categorywise_done_total('ITAX')
            self.global_category_done_ptax_total = self.get_categorywise_done_total('PTAX')

            #get monthly tax
            taxRuleData = self.get_tax_rule_data()
            remain_tax_payable = 0
            if (self.get_taxable_income_total() < taxRuleData["slab_1"]):
                monthlyTaxPayable = 0          
            else:
                remain_tax_payable = self.get_remain_tax_payable_total()
                monthlyTaxPayable = round(float(remain_tax_payable) / (self.global_tax_remain_month + 1))

            #update monthly income tax
            query = "UPDATE hr_payslip_input SET amount=%s WHERE payslip_id=%s AND code='RTAX'"
            params = (
                monthlyTaxPayable,
                self.id,
            )
            self.env.cr.execute(query, params)

            #basic_total             
            basic_total = self.get_yearly_basic_total()   

            #income_total
            income_total = self.get_yearly_income_total()

            #hr_exemption
            hr_exemption = self.get_house_rent_exemption_amt()

            #med_exemption
            med_exemption = self.get_medical_exemption_amt()

            #conv_exemption
            conv_exemption = self.get_conveyance_exemption_amt()

            #exemption_total
            exemption_total = self.get_tax_exemption_total()

            #taxable_income_total
            taxable_income_total = self.get_taxable_income_total()

            #tax_liability_total
            tax_liability_total = self.get_tax_liability_total()

            #tax_rebate_total
            tax_rebate_total = self.get_tax_rebate_total()

            #tax_payable_total
            tax_payable_total = self.get_tax_payable_total()

            #tax_paid_total
            tax_paid_total = self.get_tax_paid_total()

            #remain_tax_payable
            remain_tax_payable = remain_tax_payable

            #remain_month
            remain_month = self.global_tax_remain_month

            #partial_month
            partial_month = self.globalPartialMonth

            #update records
            self.env.cr.execute("""UPDATE hr_payslip 
                SET basic_total=%s,
                income_total=%s,
                hr_exemption=%s,
                med_exemption=%s,
                conv_exemption=%s,
                exemption_total=%s,
                taxable_income_total=%s,
                tax_liability_total=%s,
                tax_rebate_total=%s,
                tax_payable_total=%s,
                tax_paid_total=%s,
                remain_tax_payable=%s,
                remain_month=%s,
                partial_month=%s,
                monthly_tax_payable=%s,
                max_allowable_investment_limit=%s
                WHERE id=%s
                """ % (basic_total, 
                income_total, 
                hr_exemption, 
                med_exemption, 
                conv_exemption, 
                exemption_total, 
                taxable_income_total, 
                tax_liability_total, 
                tax_rebate_total, 
                tax_payable_total, 
                tax_paid_total, 
                remain_tax_payable, 
                remain_month + 1, 
                partial_month,
                monthlyTaxPayable,
                self.globalMaxAllowInvestmentLimit,
                self.id,))
                            
            return

        except Exception:

            # printData = str(e) \
            #         + ' Slip Id: ' + str(self.id) \
            #         + ', Employee Id: ' + str(self.employee_id.id) \
            #         + ', Company Id: ' + str(employee.company_id.id) \
            #         + ', Struct Id: ' + str(self.globalStructId) \
            #         + ', Contract Id: ' + str(self.globalContractId) 

            # raise UserError(_(printData))

            #traceback.print_tb(err.__traceback__)
            traceback.format_exc()



# class HrPayslipEmployees(models.TransientModel):

#     _inherit = 'hr.payslip.employees'

#     @api.multi
#     def compute_sheet(self):



