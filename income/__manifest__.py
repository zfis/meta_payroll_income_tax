{
    'name': 'Payroll with Income Tax for Bangladesh',
    'category': 'Human Resources',
    'sequence': 1,
    'version': '10.0.1',
    'summary': 'Full payroll solution with Income Tax.',
    'description': """

Tax Payable System
=======================

* Configure Income Tax Rules
* Calculate Tax Exemption
* Calculate Tax Liablity
* Calculate Tax Rebate
* Calculate Employee Tax
* Generate Employee Payslip with Tax
* Genearate Multi Payslip with Employee Tax
* Generate Employee Challan Submit
* Report on Company Payroll Tracker
* Report on Employee Salary Tracker
* Report on Employee Investment Allowance Declaration
* Report on Employee Income Tax Deduction Certificate
* Report on Employee Income Tax Card
* Report on Employee Challan

""",
    'author': 'Metamorphosis',
    'website': 'https://metamorphosis.com.bd',
    'depends': [
        'base', 
        'hr', 
        'hr_payroll', 
        'hr_contract', 
        'hr_recruitment',
        'report', 
        'website',
    ],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',

        'views/income_tax_view.xml',
        'views/tax_challan_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_payslip_line_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/hr_field_view.xml',
        'views/res_bank_view.xml',
        'views/salary_tracker_view.xml',
        'views/payroll_tracker_view.xml',
        'views/website_view.xml',

        'wizard/investment_alw_view.xml',
        'wizard/salary_certificate_view.xml',
        'wizard/payroll_tracker_view.xml',
        'wizard/salary_tracker_view.xml',
        'wizard/tax_card_view.xml',
        'wizard/archive_payslip_view.xml',
        'wizard/computetax_payslip_view.xml',

        'reports/reports.xml',
        'reports/investment_alw_template.xml',
        'reports/salary_certificate_template.xml',
        'reports/payroll_tracker_template.xml',
        'reports/tax_challan_template.xml',
        'reports/tax_card_template.xml',
        'reports/payslip_template.xml',
    ],
    'qweb':  ['static/src/xml/qweb.xml'],
    "images": ["static/description/cover.png"],
    'icon': "/income/static/description/icon.png",  
    'external_dependencies': {'python': ['xlwt']},
    'demo': [],
    'installable': True,
    'price': 2999,
    'currency': 'EUR',
    'auto_install': False,
    'application': True,
    "license": "OPL-1",
}
