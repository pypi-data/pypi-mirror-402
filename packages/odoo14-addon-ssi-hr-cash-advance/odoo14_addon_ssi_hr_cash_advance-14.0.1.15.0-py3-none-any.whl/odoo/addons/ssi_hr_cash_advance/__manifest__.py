# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Employee Cash Advance",
    "version": "14.0.1.15.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_hr_expense",
        "ssi_master_data_mixin",
        "ssi_transaction_confirm_mixin",
        "ssi_transaction_open_mixin",
        "ssi_transaction_done_mixin",
        "ssi_transaction_cancel_mixin",
        "ssi_transaction_pricelist_mixin",
        "ssi_employee_document_mixin",
        "ssi_product_line_account_mixin",
        "ssi_company_currency_mixin",
        "ssi_m2o_configurator_mixin",
        "base_duration",
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
        "data/approval_template_data.xml",
        "data/ir_actions_server_data.xml",
        "data/base_automation_data.xml",
        "data/account_journal_data.xml",
        "views/res_config_settings_views.xml",
        "views/hr_expense_type_views.xml",
        "views/hr_cash_advance_views.xml",
        "views/hr_cash_advance_views_settlement.xml",
    ],
    "demo": [
        "demo/account_account_demo.xml",
        "demo/account_journal_demo.xml",
        "demo/hr_expense_type_demo.xml",
    ],
}
