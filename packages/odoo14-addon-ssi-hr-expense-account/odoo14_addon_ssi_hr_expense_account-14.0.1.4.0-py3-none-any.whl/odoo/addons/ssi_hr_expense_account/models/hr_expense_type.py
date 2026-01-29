# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrExpenseType(models.Model):
    _inherit = "hr.expense_type"

    def _get_require_expense_products(self):
        Product = self.env["product.product"]
        for record in self:
            categ_ids = (
                record.mapped("product_category_ids")
                .filtered(lambda x: x.require_expense_account)
                .mapped("categ_id")
            )
            all_products = Product.search([("categ_id", "in", categ_ids.ids)])
            all_products |= (
                record.mapped("product_ids")
                .filtered(lambda x: x.require_expense_account)
                .mapped("product_id")
            )
            return all_products
