# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EmployeeExpenseAccount(models.Model):
    _name = "employee_expense_account"
    _description = "Employee Expense Account"
    _inherit = [
        "mixin.date_duration",
        "mixin.employee_document",
        "mixin.company_currency",
        "mixin.transaction_confirm",
        "mixin.transaction_open",
        "mixin.transaction_done",
        "mixin.transaction_cancel",
        "mixin.transaction_terminate",
    ]

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_multiple_approval_page = True
    _automatically_insert_done_button = False
    _automatically_insert_done_policy_fields = False

    # Date Duration
    _date_start_readonly = True
    _date_end_readonly = True
    _date_start_states_list = ["draft"]
    _date_start_states_readonly = ["draft"]
    _date_end_states_list = ["draft"]
    _date_end_states_readonly = ["draft"]

    _statusbar_visible_label = "draft,confirm,open,done"
    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "open_ok",
        "done_ok",
        "manual_number_ok",
    ]
    __header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "action_done",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_open",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "open"

    type_id = fields.Many2one(
        comodel_name="employee_expense_account_type",
        string="Type",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    amount_limit = fields.Monetary(
        string="Limit",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    amount_realized = fields.Monetary(
        string="Realized",
        compute="_compute_amount",
        store=True,
        compute_sudo=True,
    )
    amount_residual = fields.Monetary(
        string="Residual",
        compute="_compute_amount",
        store=True,
        compute_sudo=True,
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("terminate", "Terminate"),
            ("reject", "Rejected"),
        ],
    )

    @api.model
    def _get_policy_field(self):
        res = super(EmployeeExpenseAccount, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "open_ok",
            "done_ok",
            "cancel_ok",
            "terminate_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    def _get_expense_fields(self):
        return []

    @api.depends(
        "employee_id",
        "date_start",
        "date_end",
        "amount_limit",
    )
    @api.depends("employee_id", "date_start", "date_end")
    def _compute_amount(self):
        for record in self:
            amount_realized = 0.0
            amount_residual = 0.0

            if not record.type_id:
                continue

            for expense_field in record._get_expense_fields():
                if expense_field:
                    amount_realized += getattr(record, expense_field)

            amount_residual = record.amount_limit - amount_realized
            record.amount_realized = amount_realized
            record.amount_residual = amount_residual

    @api.constrains("employee_id", "date_start", "date_end")
    def constrains_expense_duration_overlap(self):
        for record in self.sudo():
            check = self.search(
                [
                    ("id", "<>", record.id),
                    ("employee_id", "=", record.employee_id.id),
                    ("type_id", "=", record.type_id.id),
                    ("date_start", "<=", record.date_end),
                    ("date_end", ">=", record.date_start),
                    ("state", "=", "open"),
                ]
            )
            if check:
                error_message = _(
                    """
                    Employee: %s
                    Type: %s
                    Problem: Date start and date end can't overlap
                    Solution: Change date start and date end
                    """
                    % (record.employee_id.name, record.type_id.name)
                )
                raise UserError(error_message)

    @api.constrains("amount_limit")
    def constrains_amount_limit(self):
        for record in self.sudo():
            if record.amount_limit <= 0:
                strWarning = _("Amount Limit must be greater than '0'")
                raise UserError(strWarning)
