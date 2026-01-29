# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HrCashAdvanceLine(models.Model):
    _name = "hr.cash_advance_line"
    _inherit = [
        "mixin.product_line_account",
    ]
    _description = "Employee Cash Advance Line"

    cash_advance_id = fields.Many2one(
        string="# Employee Cash Advance",
        comodel_name="hr.cash_advance",
        required=True,
        ondelete="cascade",
    )
    pricelist_id = fields.Many2one(
        related="cash_advance_id.pricelist_id",
        store=True,
        compute_sudo=True,
    )
    type_id = fields.Many2one(
        string="Type", related="cash_advance_id.type_id", compute_sudo=True
    )
    product_id = fields.Many2one(
        required=True,
    )
    date_expense = fields.Date(
        string="Date Expense",
    )

    @api.onchange(
        "allowed_pricelist_ids",
        "currency_id",
    )
    def onchange_pricelist_id(self):
        pass

    @api.onchange(
        "product_id",
    )
    def onchange_line_usage_id(self):
        self.usage_id = False
        if self.product_id:
            self.usage_id = self.type_id.default_product_usage_id.id
