# Copyright 2019 OpenSynergy Indonesia
# Copyright 2020 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AmortizationSchedule(models.Model):
    _name = "account.amortization_schedule"
    _description = "Amortization Schedule"

    def _compute_amortization_state(self):
        for document in self:
            document.amortization_state = document.amortization_id.state

    @api.depends(
        "manual",
        "move_id",
    )
    def _compute_state(self):
        for record in self:
            state = "draft"

            if record.manual:
                state = "manual"

            if record.move_id:
                state = "post"

            record.state = state

    amortization_id = fields.Many2one(
        string="Amortization",
        comodel_name="account.amortization",
        ondelete="cascade",
    )
    date = fields.Date(
        string="Date",
        required=True,
    )
    amount = fields.Float(
        string="Amount",
        required=True,
    )
    move_line_id = fields.Many2one(
        string="Move Line",
        comodel_name="account.move.line",
        readonly=True,
        ondelete="restrict",
    )
    move_id = fields.Many2one(
        string="# Move",
        comodel_name="account.move",
        related="move_line_id.move_id",
        compute_sudo=True,
    )
    amortization_state = fields.Selection(
        string="Amortization State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        readonly=True,
        compute="_compute_amortization_state",
        store=False,
        compute_sudo=True,
    )
    manual = fields.Boolean(
        string="Manual",
        readonly=True,
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("manual", "Manually Controlled"),
            ("post", "Posted"),
        ],
        compute="_compute_state",
        store=True,
        compute_sudo=True,
    )

    def action_create_account_move(self):
        for document in self:
            document._create_account_move()
            document.write(
                {
                    "state": "post",
                }
            )
            document.amortization_id._compute_move_line()

    def action_remove_account_move(self):
        for document in self:
            document._remove_account_move()
            document.write(
                {
                    "state": "draft",
                }
            )

    def action_mark_as_manual(self):
        for record in self:
            record.write(
                {
                    "manual": True,
                }
            )

    def action_unmark_as_manual(self):
        for record in self:
            record.write(
                {
                    "manual": False,
                }
            )

    def _remove_account_move(self):
        self.ensure_one()

        if self.amortization_id.move_line_id:
            self._unreconcile_account_move()

        move = self.move_id
        self.write({"move_line_id": False})
        move.with_context(force_delete=True).unlink()

    def _unreconcile_account_move(self):
        self.ensure_one()
        self.move_line_id.remove_move_reconcile()

    def _create_account_move(self):
        self.ensure_one()
        obj_move = self.env["account.move"]
        obj_aml = self.env["account.move.line"]
        move = obj_move.create(self._prepare_account_move())
        aml = obj_aml.with_context(check_move_validity=False).create(
            self._prepare_amortization_aml(move)
        )
        self.write({"move_line_id": aml.id})
        obj_aml.with_context(check_move_validity=False).create(
            self._prepare_contra_amortization_aml(move)
        )
        move.action_post()

        if self.amortization_id.move_line_id:
            self._reconcile_account_move()
        return move

    def _reconcile_account_move(self):
        self.ensure_one()
        aml_to_be_reconcile = self.amortization_id.move_line_id
        aml_to_be_reconcile += self.move_line_id
        aml_to_be_reconcile.reconcile()

    def _prepare_account_move(self):
        self.ensure_one()
        amortization = self.amortization_id
        return {
            "name": "/",
            "journal_id": amortization.journal_id.id,
            "date": self.date,
            "ref": amortization.name,
        }

    def _prepare_amortization_aml(self, move):
        self.ensure_one()
        debit, credit = self._get_aml_amount()
        amortization = self.amortization_id
        partner_id = (
            amortization.move_line_id.partner_id
            and amortization.move_line_id.partner_id.id
            or False
        )
        analytic_id = (
            amortization.move_line_id.analytic_account_id
            and amortization.move_line_id.analytic_account_id.id
            or False
        )
        return {
            "move_id": move.id,
            "name": _("Amortization"),
            "account_id": amortization.account_id.id,
            "debit": debit,
            "credit": credit,
            "partner_id": partner_id,
            "analytic_account_id": analytic_id,
        }

    def _prepare_contra_amortization_aml(self, move):
        self.ensure_one()
        debit, credit = self._get_aml_amount(True)
        amortization = self.amortization_id
        analytic_id = amortization.analytic_id and amortization.analytic_id.id or False
        return {
            "move_id": move.id,
            "name": _("Amortization"),
            "account_id": amortization.contra_account_id.id,
            "debit": debit,
            "credit": credit,
            "analytic_account_id": analytic_id,
        }

    def _get_aml_amount(self, contra=False):
        self.ensure_one()
        amortization = self.amortization_id
        direction = amortization.type_id.direction
        debit = credit = 0.0
        if direction == "dr":
            credit = self.amount
        else:
            debit = self.amount

        if contra:
            debit, credit = credit, debit

        return debit, credit

    def cron_create_account_move(self):
        date_now = fields.Date.today()
        schedule_ids = self.search(
            [
                ("amortization_id.state", "=", "open"),
                ("date", "=", date_now),
                ("state", "=", "draft"),
            ]
        )
        if schedule_ids:
            for schedule in schedule_ids:
                schedule.action_create_account_move()
