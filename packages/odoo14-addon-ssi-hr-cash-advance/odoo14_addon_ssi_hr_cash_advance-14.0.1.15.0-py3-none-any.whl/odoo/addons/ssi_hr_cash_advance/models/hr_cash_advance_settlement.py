# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class HrCashAdvanceSettlement(models.Model):
    _name = "hr.cash_advance_settlement"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_confirm",
        "mixin.transaction_pricelist",
        "mixin.many2one_configurator",
        "mixin.employee_document",
        "mixin.company_currency",
    ]
    _description = "Employee Cash Advance Settlement"

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "done"
    _approval_state = "confirm"
    _after_approved_method = "action_done"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False
    _automatically_insert_open_policy_fields = False
    _automatically_insert_open_button = False

    _statusbar_visible_label = "draft,confirm,done"
    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "done"

    # FIELD
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="hr.expense_type",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    pricelist_id = fields.Many2one(
        required=False,
    )
    allowed_product_ids = fields.Many2many(
        string="Allowed Product",
        comodel_name="product.product",
        related="type_id.allowed_product_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_product_category_ids = fields.Many2many(
        string="Allowed Product Category",
        comodel_name="product.category",
        related="type_id.allowed_product_category_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_product_usage_ids = fields.Many2many(
        string="Allowed Product Usage",
        comodel_name="product.usage_type",
        related="type_id.allowed_product_usage_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_pricelist_ids = fields.Many2many(
        string="Allowed Pricelists",
        comodel_name="product.pricelist",
        compute="_compute_allowed_pricelist_ids",
        store=False,
        compute_sudo=True,
    )

    @api.model
    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self._default_currency_id(),
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )

    @api.depends(
        "employee_id",
        "type_id",
    )
    def _compute_allowed_cash_advance_ids(self):
        CA = self.env["hr.cash_advance"]
        for record in self:
            result = []
            if record.employee_id and record.type_id:
                criteria = [
                    ("employee_id", "=", record.employee_id.id),
                    ("type_id", "=", record.type_id.id),
                    ("state", "=", "open"),
                ]
                result = CA.search(criteria).ids
            record.allowed_cash_advance_ids = result

    allowed_cash_advance_ids = fields.Many2many(
        string="Allowed Cash Advance",
        comodel_name="hr.cash_advance",
        compute="_compute_allowed_cash_advance_ids",
        store=False,
        compute_sudo=True,
    )
    cash_advance_id = fields.Many2one(
        string="# Cash Advance",
        comodel_name="hr.cash_advance",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    # Accounting Configuration
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    move_id = fields.Many2one(
        string="# Journal Entry",
        comodel_name="account.move",
        readonly=True,
        ondelete="set null",
        copy=False,
    )
    cash_advance_move_line_id = fields.Many2one(
        string="Cash Advance Move Line",
        comodel_name="account.move.line",
        readonly=True,
        ondelete="set null",
        copy=False,
    )
    line_ids = fields.One2many(
        string="Details",
        comodel_name="hr.cash_advance_settlement_line",
        inverse_name="cash_advance_settlement_id",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        copy=True,
    )

    @api.depends(
        "line_ids",
        "line_ids.price_subtotal",
    )
    def _compute_amount_total(self):
        for document in self:
            amount_total = 0.0
            for line in document.line_ids:
                amount_total += line.price_total
            document.amount_total = amount_total

    amount_total = fields.Monetary(
        string="Amount Total",
        compute="_compute_amount_total",
        store=True,
        currency_field="currency_id",
        compute_sudo=True,
    )

    @api.depends(
        "type_id",
        "employee_id",
    )
    def _compute_allowed_analytic_account_ids(self):
        for document in self:
            result = []
            if document.type_id:
                type_id = document.type_id
                if type_id.analytic_account_method == "fixed":
                    if type_id.analytic_account_ids:
                        result = type_id.analytic_account_ids.ids
                elif type_id.analytic_account_method == "python":
                    analytic_account_ids = document._evaluate_analytic_account()
                    if analytic_account_ids:
                        result = analytic_account_ids
            document.allowed_analytic_account_ids = result

    allowed_analytic_account_ids = fields.Many2many(
        string="Allowed Analytic Accounts",
        comodel_name="account.analytic.account",
        compute="_compute_allowed_analytic_account_ids",
        store=False,
        compute_sudo=True,
    )

    @api.depends("type_id", "currency_id", "employee_id")
    def _compute_allowed_pricelist_ids(self):
        for record in self:
            result = False
            if record.type_id and record.currency_id and record.employee_id:
                result = record._m2o_configurator_get_filter(
                    object_name="product.pricelist",
                    method_selection=record.type_id.pricelist_selection_method,
                    manual_recordset=record.type_id.pricelist_ids,
                    domain=record.type_id.pricelist_domain,
                    python_code=record.type_id.pricelist_python_code,
                )
                if result:
                    result = result.filtered(
                        lambda r: r.currency_id.id == record.currency_id.id
                    )
            record.allowed_pricelist_ids = result

    @api.model
    def _get_policy_field(self):
        res = super(HrCashAdvanceSettlement, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    def action_done(self):
        _super = super(HrCashAdvanceSettlement, self)
        _super.action_done()
        for document in self.sudo():
            document._create_accounting_entry()

    def _get_localdict(self):
        self.ensure_one()
        return {
            "env": self.env,
            "document": self,
        }

    def _evaluate_analytic_account(self):
        self.ensure_one()
        res = False
        localdict = self._get_localdict()
        try:
            safe_eval(self.type_id.python_code, localdict, mode="exec", nocopy=True)
            if "result" in localdict:
                res = localdict["result"]
        except Exception as error:
            msg_err = _("Error evaluating conditions.\n %s") % error
            raise UserError(msg_err)
        return res

    def _create_accounting_entry(self):
        self.ensure_one()
        move = self._create_account_move()
        header_line = self._create_header_line(move)
        for line in self.line_ids:
            line._create_expense_line(move)
        pair = header_line + self.cash_advance_id.cash_advance_move_line_id
        self.write(
            {
                "move_id": move.id,
                "cash_advance_move_line_id": header_line.id,
            }
        )
        move.action_post()
        pair.reconcile()

    def _create_account_move(self):
        self.ensure_one()
        AccountMove = self.env["account.move"].with_context(check_move_validity=False)
        return AccountMove.create(self._prepare_create_account_move_data())

    def _prepare_create_account_move_data(self):
        self.ensure_one()
        data = {
            "name": self.name,
            "journal_id": self.journal_id.id,
            "date": self.date,
        }
        return data

    def _create_header_line(self, move):
        self.ensure_one()
        AML = self.env["account.move.line"].with_context(check_move_validity=False)
        return AML.create(self._prepare_create_header_line_data(move))

    def _get_currency(self):
        self.ensure_one()
        result = self.company_currency_id
        return result

    def _prepare_create_header_line_data(self, move):
        self.ensure_one()
        currency = self._get_currency()
        amount, amount_currency = self._get_header_amount(currency)
        move_name = _("Employee cash advance settlement %s" % (self.name))
        account = self.cash_advance_id.cash_advance_account_id
        data = {
            "name": move_name,
            "move_id": move.id,
            "partner_id": self._get_partner_id(),
            "account_id": account.id,
            "debit": 0.0,
            "credit": amount,
            "currency_id": currency and currency.id or False,
            "amount_currency": amount_currency,
        }
        return data

    def _get_header_amount(self, currency):
        self.ensure_one()
        amount = amount_currency = 0.0
        move_date = self.date

        if currency:
            amount_currency = self.amount_total
            amount = currency.with_context(date=move_date).compute(
                amount_currency,
                self.company_id.currency_id,
            )
        else:
            amount = self.amount_total

        return amount, amount_currency

    def _get_partner_id(self):
        self.ensure_one()
        if not self.employee_id.address_home_id:
            err_msg = _("No home address defined for employee")
            raise UserError(err_msg)
        return self.employee_id.address_home_id.id

    def action_cancel(self, cancel_reason=False):
        _super = super(HrCashAdvanceSettlement, self)
        _super.action_cancel(cancel_reason=cancel_reason)
        for document in self.sudo():
            document._delete_accounting_entry()

    def _delete_accounting_entry(self):
        self.ensure_one()
        if not self.move_id:
            return True

        self.cash_advance_move_line_id.remove_move_reconcile()

        if self.move_id.state == "posted":
            self.move_id.button_draft()
            self.move_id.button_cancel()

        self.move_id.with_context(force_delete=True).unlink()

    @api.onchange(
        "type_id",
    )
    def onchange_journal_id(self):
        self.journal_id = False
        if self.type_id and self.type_id.cash_advance_settlement_journal_id:
            self.journal_id = self.type_id.cash_advance_settlement_journal_id

    @api.onchange(
        "type_id",
    )
    def onchange_line_usage_id(self):
        self.line_ids.usage_id = False
        if self.type_id:
            self.line_ids.usage_id = self.type_id.default_product_usage_id.id

    @api.onchange(
        "type_id",
    )
    def onchange_line_analytic_account_id(self):
        if self.type_id:
            self.line_ids.analytic_account_id = False

    @api.onchange(
        "employee_id",
        "type_id",
        "currency_id",
    )
    def onchange_pricelist_id(self):
        self.pricelist_id = False

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch

    def action_reload_cash_advance(self):
        for rec in self.sudo().filtered(lambda s: s.state == "draft"):
            rec.line_ids = False
            line_vals = []
            for line_id in rec.cash_advance_id.line_ids:
                line_vals.append(
                    (
                        0,
                        0,
                        {
                            "cash_advance_settlement_id": rec.id,
                            "currency_id": line_id.currency_id.id,
                            "pricelist_id": line_id.pricelist_id
                            and line_id.pricelist_id.id
                            or False,
                            "price_unit": line_id.price_unit,
                            "product_id": line_id.product_id.id,
                            "name": line_id.name,
                            "usage_id": line_id.usage_id
                            and line_id.usage_id.id
                            or False,
                            "uom_quantity": line_id.uom_quantity,
                            "uom_id": line_id.uom_id.id,
                            "account_id": line_id.account_id.id,
                            "analytic_account_id": line_id.analytic_account_id
                            and line_id.analytic_account_id.id
                            or False,
                            "date_expense": line_id.date_expense,
                        },
                    )
                )
            rec.line_ids = line_vals
