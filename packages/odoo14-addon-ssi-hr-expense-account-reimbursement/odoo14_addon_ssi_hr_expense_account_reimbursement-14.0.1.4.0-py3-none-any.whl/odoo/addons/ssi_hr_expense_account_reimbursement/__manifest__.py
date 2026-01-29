# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Employee Expense Account - Reimbursement Integration",
    "version": "14.0.1.4.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_hr_reimbursement",
        "ssi_hr_expense_account",
    ],
    "data": [
        "views/hr_reimbursement_views.xml",
        "views/employee_expense_account_view.xml",
    ],
    "demo": [],
}
