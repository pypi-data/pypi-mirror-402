# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HrCashAdvanceSettlementLine(models.Model):
    _name = "hr.cash_advance_settlement_line"
    _inherit = [
        "mixin.product_line_account",
    ]
    _description = "Employee Cash Advance Settlement Line"

    cash_advance_settlement_id = fields.Many2one(
        string="# Employee Cash Advance Settlement",
        comodel_name="hr.cash_advance_settlement",
        required=True,
        ondelete="cascade",
    )
    pricelist_id = fields.Many2one(
        related="cash_advance_settlement_id.pricelist_id",
        store=True,
        compute_sudo=True,
    )
    type_id = fields.Many2one(
        string="Type",
        related="cash_advance_settlement_id.type_id",
        compute_sudo=True,
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

    def _create_expense_line(self, move):
        self.ensure_one()
        AML = self.env["account.move.line"].with_context(check_move_validity=False)
        return AML.create(self._prepare_create_expense_line_data(move))

    def _prepare_create_expense_line_data(self, move):
        self.ensure_one()
        currency = self.cash_advance_settlement_id._get_currency()
        amount, amount_currency = self._get_amount(currency)
        move_name = self.name
        account = self.account_id
        data = {
            "name": move_name,
            "move_id": move.id,
            "partner_id": self.cash_advance_settlement_id._get_partner_id(),
            "account_id": account.id,
            "debit": amount,
            "credit": 0.0,
            "currency_id": currency and currency.id or False,
            "amount_currency": amount_currency,
            "product_id": self.product_id.id,
            "price_unit": self.price_unit,
            "product_uom_id": self.uom_id.id,
            "quantity": self.quantity,
        }
        return data

    def _get_amount(self, currency):
        self.ensure_one()
        amount = amount_currency = 0.0
        move_date = self.cash_advance_settlement_id.date

        if currency:
            amount_currency = self.price_subtotal
            amount = currency.with_context(date=move_date).compute(
                amount_currency,
                self.cash_advance_settlement_id.company_id.currency_id,
            )
        else:
            amount = self.price_subtotal

        return amount, amount_currency

    @api.onchange(
        "product_id",
    )
    def onchange_line_usage_id(self):
        self.usage_id = False
        if self.product_id:
            self.usage_id = self.type_id.default_product_usage_id.id
