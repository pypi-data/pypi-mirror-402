# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AmortizationType(models.Model):
    _name = "account.amortization_type"
    _inherit = ["mixin.master_data"]
    _description = "Amortization Type"

    name = fields.Char(
        string="Amortization Type",
    )
    direction = fields.Selection(
        string="Direction",
        selection=[
            ("dr", "Debit"),
            ("cr", "Credit"),
        ],
        default="dr",
        required=True,
    )
    journal_id = fields.Many2one(
        string="Default Journal",
        comodel_name="account.journal",
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
    )
    contra_account_id = fields.Many2one(
        string="Contra Account",
        comodel_name="account.account",
    )
