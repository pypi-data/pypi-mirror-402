# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Employee Expense Account",
    "version": "14.0.1.4.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_financial_accounting",
        "ssi_master_data_mixin",
        "ssi_transaction_confirm_mixin",
        "ssi_transaction_open_mixin",
        "ssi_transaction_done_mixin",
        "ssi_transaction_cancel_mixin",
        "ssi_transaction_terminate_mixin",
        "ssi_duration_mixin",
        "ssi_hr_expense",
        "ssi_company_currency_mixin",
        "ssi_employee_document_mixin",
        "base_automation",
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_group_data.xml",
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/ir_sequence_data.xml",
        "data/sequence_template_data.xml",
        "data/policy_template_data.xml",
        "data/ir_actions_server_data.xml",
        "data/base_automation_data.xml",
        "data/approval_template_data.xml",
        "views/employee_expense_account_view.xml",
        "views/employee_expense_account_type_view.xml",
        "views/hr_expense_type_product_views.xml",
        "views/hr_expense_type_product_category_views.xml",
    ],
    "demo": [],
}
