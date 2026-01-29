# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EmployeeExpenseAccountType(models.Model):
    _name = "employee_expense_account_type"
    _description = "Employee Expense Account Type"
    _inherit = "mixin.master_data"

    account_ids = fields.Many2many(
        string="Accounts",
        comodel_name="account.account",
        relation="rel_employee_expense_account_type_2_account",
        column1="type_id",
        column2="account_id",
    )
