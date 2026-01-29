# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class HrCashAdvance(models.Model):
    _name = "hr.cash_advance"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_confirm",
        "mixin.transaction_pricelist",
        "mixin.many2one_configurator",
        "mixin.employee_document",
        "mixin.company_currency",
    ]
    _description = "Employee Cash Advance"

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False
    _automatically_insert_open_policy_fields = False
    _automatically_insert_open_button = False

    _statusbar_visible_label = "draft,confirm,open,done"
    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "open_ok",
        "done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "action_done",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_open",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "open"

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
    duration_id = fields.Many2one(
        string="Duration",
        comodel_name="base.duration",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    date_due = fields.Date(
        string="Date Due",
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
    cash_advance_account_id = fields.Many2one(
        string="Cash Advance Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    payable_account_id = fields.Many2one(
        string="Payable Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )

    line_ids = fields.One2many(
        string="Details",
        comodel_name="hr.cash_advance_line",
        inverse_name="cash_advance_id",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        copy=True,
    )

    # Accounting Entry
    payable_move_line_id = fields.Many2one(
        string="Payable Move Line",
        comodel_name="account.move.line",
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
    move_id = fields.Many2one(
        string="# Journal Entry",
        comodel_name="account.move",
        readonly=True,
        ondelete="set null",
        copy=False,
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
    )

    @api.depends(
        "payable_move_line_id",
        "payable_move_line_id.matched_debit_ids",
        "payable_move_line_id.matched_credit_ids",
    )
    def _compute_realized(self):
        for record in self:
            result = False
            if record.payable_move_line_id.reconciled:
                result = True
            record.realized = result

    realized = fields.Boolean(
        string="Realized",
        compute="_compute_realized",
        store=True,
        compute_sudo=True,
    )

    @api.depends(
        "cash_advance_move_line_id",
        "cash_advance_move_line_id.matched_debit_ids",
        "cash_advance_move_line_id.matched_credit_ids",
    )
    def _compute_settled(self):
        for record in self:
            result = False
            if record.cash_advance_move_line_id.reconciled:
                result = True
            record.settled = result

    settled = fields.Boolean(
        string="Settled",
        compute="_compute_settled",
        store=True,
        compute_sudo=True,
    )

    @api.depends(
        "payable_move_line_id",
        "payable_move_line_id.reconciled",
        "payable_move_line_id.amount_residual",
        "payable_move_line_id.amount_residual_currency",
    )
    def _compute_amount_realized(self):
        for document in self:
            result = 0.0
            if document.payable_move_line_id:
                move_line = document.payable_move_line_id
                result = move_line.amount_residual_currency * -1.0
            document.amount_unrealized = result

    amount_unrealized = fields.Monetary(
        string="Amount Unrealized",
        compute="_compute_amount_realized",
        store=True,
        currency_field="currency_id",
        compute_sudo=True,
    )

    @api.depends(
        "cash_advance_move_line_id",
        "cash_advance_move_line_id.reconciled",
        "cash_advance_move_line_id.amount_residual",
        "cash_advance_move_line_id.amount_residual_currency",
    )
    def _compute_amount_settled(self):
        for document in self:
            result = 0.0
            if document.cash_advance_move_line_id:
                move_line = document.cash_advance_move_line_id
                result = move_line.amount_residual_currency
            document.amount_unsettled = result

    amount_unsettled = fields.Monetary(
        string="Amount Unsettled",
        compute="_compute_amount_settled",
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
        res = super(HrCashAdvance, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "open_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

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

    @api.onchange(
        "type_id",
    )
    def onchange_journal_id(self):
        self.journal_id = False
        if self.type_id and self.type_id.cash_advance_journal_id:
            self.journal_id = self.type_id.cash_advance_journal_id

    @api.onchange(
        "type_id",
    )
    def onchange_cash_advance_account_id(self):
        self.cash_advance_account_id = False
        if self.type_id and self.type_id.cash_advance_account_id:
            self.cash_advance_account_id = self.type_id.cash_advance_account_id

    @api.onchange(
        "type_id",
    )
    def onchange_payable_account_id(self):
        self.payable_account_id = False
        if self.type_id and self.type_id.cash_advance_payable_account_id:
            self.payable_account_id = self.type_id.cash_advance_payable_account_id

    def action_open(self):
        _super = super(HrCashAdvance, self)
        _super.action_open()
        for document in self.sudo():
            document._create_accounting_entry()

    def action_cancel(self, cancel_reason=False):
        _super = super(HrCashAdvance, self)
        _super.action_cancel(cancel_reason=cancel_reason)
        for document in self.sudo():
            document._delete_accounting_entry()

    def action_recompute_realization(self):
        for record in self.sudo():
            record._recompute_realization()

    def _recompute_realization(self):
        self.ensure_one()

        if self.state == "open" and self.realized and self.settled:
            self.action_done()
        elif self.state == "done" and (not self.realized or not self.settled):
            self.action_open()

    def _delete_accounting_entry(self):
        self.ensure_one()
        if not self.move_id:
            return True

        if self.move_id.state == "posted":
            self.move_id.button_draft()
            self.move_id.button_cancel()

        self.move_id.with_context(force_delete=True).unlink()

    def _create_accounting_entry(self):
        self.ensure_one()
        if self.move_id:
            return True

        move = self._create_account_move()
        payable_line = self._create_payable_line(move)
        cash_advance_line = self._create_cash_advance_line(move)
        self.write(
            {
                "move_id": move.id,
                "payable_move_line_id": payable_line.id,
                "cash_advance_move_line_id": cash_advance_line.id,
            }
        )
        move.action_post()

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

    def _create_payable_line(self, move):
        self.ensure_one()
        AML = self.env["account.move.line"].with_context(check_move_validity=False)
        return AML.create(self._prepare_create_payable_line_data(move))

    def _create_cash_advance_line(self, move):
        self.ensure_one()
        AML = self.env["account.move.line"].with_context(check_move_validity=False)
        return AML.create(self._prepare_create_cash_advance_line_data(move))

    def _prepare_create_payable_line_data(self, move):
        self.ensure_one()
        currency = self._get_currency()
        amount, amount_currency = self._get_cash_advance_amount(currency)
        move_name = _("Employee cash advance %s" % (self.name))
        data = {
            "name": move_name,
            "move_id": move.id,
            "partner_id": self._get_partner_id(),
            "account_id": self.payable_account_id.id,
            "debit": 0.0,
            "credit": amount,
            "currency_id": currency and currency.id or False,
            "amount_currency": amount_currency,
        }
        return data

    def _prepare_create_cash_advance_line_data(self, move):
        self.ensure_one()
        currency = self._get_currency()
        amount, amount_currency = self._get_cash_advance_amount(currency)
        move_name = _("Employee cash advance %s" % (self.name))
        data = {
            "name": move_name,
            "move_id": move.id,
            "partner_id": self._get_partner_id(),
            "account_id": self.cash_advance_account_id.id,
            "debit": amount,
            "credit": 0.0,
            "currency_id": currency and currency.id or False,
            "amount_currency": amount_currency,
            "date_maturity": self.date_due,
        }
        return data

    def _get_currency(self):
        self.ensure_one()
        result = self.currency_id
        return result

    def _get_cash_advance_amount(self, currency):
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

    @api.onchange(
        "duration_id",
        "date",
    )
    def onchange_date_due(self):
        if self.duration_id:
            self.date_due = self.duration_id.get_duration(self.date)

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
