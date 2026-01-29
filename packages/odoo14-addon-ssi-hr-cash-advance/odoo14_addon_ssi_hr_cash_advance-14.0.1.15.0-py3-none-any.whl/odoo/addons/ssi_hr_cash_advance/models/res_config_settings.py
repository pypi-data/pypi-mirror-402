# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _name = "res.config.settings"
    _inherit = [
        "res.config.settings",
    ]

    module_ssi_hr_cash_advance_related_attachment = fields.Boolean(
        "Employee Cash Advance - Related Attachment",
    )
    module_ssi_hr_cash_advance_custom_information = fields.Boolean(
        "Employee Cash Advance - Custom Information",
    )
    module_ssi_hr_cash_advance_status_check = fields.Boolean(
        "Employee Cash Advance - Status Check",
    )
    module_ssi_hr_cash_advance_state_change_constrains = fields.Boolean(
        "Employee Cash Advance - State Change Constrains",
    )
    module_ssi_hr_cash_advance_qrcode = fields.Boolean(
        "Employee Cash Advance - QR Code",
    )
    module_ssi_hr_cash_advance_settlement_related_attachment = fields.Boolean(
        "Employee Cash Advance Settlement - Related Attachment",
    )
    module_ssi_hr_cash_advance_settlement_custom_information = fields.Boolean(
        "Employee Cash Advance Settlement - Custom Information",
    )
    module_ssi_hr_cash_advance_settlement_status_check = fields.Boolean(
        "Employee Cash Advance Settlement - Status Check",
    )
    module_ssi_hr_cash_advance_settlement_state_change_constrains = fields.Boolean(
        "Employee Cash Advance Settlement - State Change Constrains",
    )
    module_ssi_hr_cash_advance_settlement_qrcode = fields.Boolean(
        "Employee Cash Advance Settlement - QR Code",
    )
