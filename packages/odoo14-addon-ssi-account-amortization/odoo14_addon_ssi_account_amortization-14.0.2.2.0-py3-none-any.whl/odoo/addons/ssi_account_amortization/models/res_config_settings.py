# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _name = "res.config.settings"
    _inherit = [
        "res.config.settings",
        "abstract.config.settings",
    ]

    module_ssi_account_amortization_related_attachment = fields.Boolean(
        "Amortization - Related Attachment",
    )
    module_ssi_account_amortization_custom_information = fields.Boolean(
        "Amortization - Custom Information",
    )
    module_ssi_account_amortization_status_check = fields.Boolean(
        "Amortization - Status Check",
    )
    module_ssi_account_amortization_state_change_constrains = fields.Boolean(
        "Amortization - State Change Constrains",
    )
    module_ssi_account_amortization_qrcode = fields.Boolean(
        "Amortization - QR Code",
    )
