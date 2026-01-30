# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import numpy_financial as npf
    import pandas as pd
except (ImportError, OSError) as err:  # pragma: no cover
    _logger.debug(err)


class Amortization(models.Model):
    _name = "account.amortization"
    _inherit = [
        "mixin.transaction_confirm",
        "mixin.transaction_open",
        "mixin.transaction_done",
        "mixin.transaction_cancel",
    ]
    _description = "Account Amortization"

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True

    # Attributes related to add element on form view automatically
    _automatically_insert_multiple_approval_page = True
    _automatically_insert_open_policy_fields = True
    _automatically_insert_open_button = True
    _automatically_insert_done_policy_fields = True
    _automatically_insert_done_button = True

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
    _header_button_order = [
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

    date = fields.Date(
        string="Date Transaction",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_start = fields.Date(
        string="Start Amortization",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    type_id = fields.Many2one(
        string="Amortization Type",
        comodel_name="account.amortization_type",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    source = fields.Selection(
        string="Source",
        selection=[
            ("move", "Journal Entry"),
            ("manual", "Manual"),
        ],
        default="move",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )

    @api.depends(
        "account_id",
    )
    def _compute_allowed_aml_ids(self):
        obj_aml = self.env["account.move.line"]
        for document in self:
            aml_ids = []
            if document.type_id and document.account_id:
                amortization_type = document.type_id
                criteria = [
                    ("account_id", "=", document.account_id.id),
                    ("matched_debit_ids", "=", False),
                    ("matched_credit_ids", "=", False),
                ]
                if amortization_type.direction == "dr":
                    criteria.append(("debit", ">", 0.0))
                else:
                    criteria.append(("credit", ">", 0.0))
                aml_ids = obj_aml.search(criteria).ids
            document.allowed_move_line_ids = [(6, 0, aml_ids)]

    allowed_move_line_ids = fields.Many2many(
        string="Allowed Move Lines",
        comodel_name="account.move.line",
        compute="_compute_allowed_aml_ids",
        compute_sudo=True,
    )

    move_line_id = fields.Many2one(
        string="Move Line",
        comodel_name="account.move.line",
        required=False,
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    account_id = fields.Many2one(
        string="Amortization Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    contra_account_id = fields.Many2one(
        string="Amortization Contra Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    analytic_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        domain=[
            ("type", "=", "general"),
        ],
        required=True,
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    period_number = fields.Integer(
        string="Period Number",
        default=1,
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    amount = fields.Float(
        string="Amount",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )

    @api.depends(
        "schedule_ids",
        "schedule_ids.state",
    )
    def _compute_move_line(self):
        for document in self:
            amortized_amount = 0.0
            amortized = False
            for line in document.schedule_ids.filtered(
                lambda r: r.state in ["post", "manual"]
            ):
                amortized_amount += line.amount

            residual = document.amount - amortized_amount

            if fields.Float.is_zero(residual, 0.02):
                amortized = True

            document.amount_residual = residual
            document.amortized = amortized

    amount_residual = fields.Float(
        string="Amount Residual",
        compute="_compute_move_line",
        store=True,
        compute_sudo=True,
    )
    amortized = fields.Boolean(
        string="Amortized",
        compute="_compute_move_line",
        store=True,
        compute_sudo=True,
    )
    schedule_ids = fields.One2many(
        string="Amortization Schedule",
        comodel_name="account.amortization_schedule",
        inverse_name="amortization_id",
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        required=True,
        readonly=True,
    )

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "open_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    def action_compute_amortization_schedule(self):
        for document in self:
            document._compute_amortization_schedule()

    def _compute_amortization_schedule(self):
        self.ensure_one()
        self.schedule_ids.unlink()
        amount = self._get_period_amount()
        obj_schedule = self.env["account.amortization_schedule"]
        pd_schedule = self._get_amortization_schedule()
        for period in range(0, self.period_number):
            if period == (self.period_number - 1):
                if self.amount != self.period_number * round(amount, 2):
                    amount = self.amount - (period * round(amount, 2))
            obj_schedule.create(
                {
                    "amortization_id": self.id,
                    "date": pd_schedule[period].strftime("%Y-%m-%d"),
                    "amount": amount,
                }
            )

    def _get_amortization_schedule(self):
        self.ensure_one()
        return pd.date_range(
            start=self.date_start,
            periods=self.period_number,
            freq="M",
        ).to_pydatetime()

    def _get_period_amount(self):
        self.ensure_one()
        return abs(npf.pmt(0.0, self.period_number, self.amount))

    @api.constrains("state")
    def _check_cancel(self):
        for record in self.sudo():
            error_message = """
            Document Type: %s
            Context: Cancel document
            Database ID: %s
            Problem: One or more amortization schedule already posted
            Solution: Cancel posted amortization schedule
            """ % (
                self._description.lower(),
                record.id,
            )
            if record.state == "cancel":
                criteria = [
                    ("amortization_id", "=", record.id),
                    ("state", "!=", "draft"),
                ]
                count_amortized_schedule = self.env[
                    "account.amortization_schedule"
                ].search_count(criteria)
                if count_amortized_schedule > 0:
                    raise ValidationError(_(error_message))

    @api.onchange(
        "type_id",
    )
    def onchange_account_id(self):
        self.account_id = False
        if self.type_id:
            self.account_id = self.type_id.account_id

    @api.onchange(
        "type_id",
    )
    def onchange_contra_account_id(self):
        self.contra_account_id = False
        if self.type_id:
            self.contra_account_id = self.type_id.contra_account_id

    @api.onchange(
        "type_id",
    )
    def onchange_journal_id(self):
        self.journal_id = False
        if self.type_id:
            self.journal_id = self.type_id.journal_id

    @api.onchange("move_line_id")
    def onchange_date(self):
        self.date = False

        if self.move_line_id:
            self.date = self.move_line_id.move_id.date

    @api.onchange("move_line_id")
    def onchange_amount(self):
        self.amount = 0.0

        if self.move_line_id:
            self.amount = abs(self.move_line_id.balance)

    @api.onchange(
        "source",
    )
    def onchange_move_line_id(self):
        self.move_line_id = False
