# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrExpenseTypeProduct(models.Model):
    _name = "hr.expense_type_product"
    _inherit = "hr.expense_type_product"

    require_expense_account = fields.Boolean(
        string="Require Expense Account", default=False
    )
