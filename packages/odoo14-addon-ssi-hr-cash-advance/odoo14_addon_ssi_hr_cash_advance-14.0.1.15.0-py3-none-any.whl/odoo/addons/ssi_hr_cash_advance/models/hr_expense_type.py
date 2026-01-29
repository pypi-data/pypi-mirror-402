# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrExpenseType(models.Model):
    _name = "hr.expense_type"
    _inherit = "hr.expense_type"

    cash_advance_journal_id = fields.Many2one(
        string="Cash Advance Journal",
        comodel_name="account.journal",
    )
    cash_advance_account_id = fields.Many2one(
        string="Cash Advance Account",
        comodel_name="account.account",
    )
    cash_advance_payable_account_id = fields.Many2one(
        string="Cash Advance Payable Account",
        comodel_name="account.account",
    )
    cash_advance_settlement_journal_id = fields.Many2one(
        string="Cash Advance Settlement Journal",
        comodel_name="account.journal",
    )
