# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0-standalone.html).
# pylint: disable=locally-disabled, manifest-required-author
{
    "name": "Account Amortization",
    "version": "14.0.2.2.0",
    "category": "Accounting",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {
        "python": [
            "numpy-financial",
            "pandas",
        ],
    },
    "depends": [
        "ssi_financial_accounting",
        "ssi_master_data_mixin",
        "ssi_transaction_confirm_mixin",
        "ssi_transaction_open_mixin",
        "ssi_transaction_done_mixin",
        "ssi_transaction_cancel_mixin",
        "base_automation",
        "configuration_helper",
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_group_data.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/sequence_template_data.xml",
        "data/approval_template_data.xml",
        "data/ir_actions_server_data.xml",
        "data/base_automation_data.xml",
        "data/policy_template_data.xml",
        "views/res_config_settings_views.xml",
        "views/amortization_type_views.xml",
        "views/amortization_views.xml",
    ],
    "demo": [
        "demo/account_account_demo.xml",
        "demo/account_journal_demo.xml",
        "demo/amortization_type_demo.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
}
