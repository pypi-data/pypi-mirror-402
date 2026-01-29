# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class EmployeeBusinessTrip(models.Model):
    _name = "employee_business_trip"
    _description = "Employee Business Trip"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_confirm",
        "mixin.employee_document",
        "mixin.date_duration",
        "mixin.company_currency",
        "mixin.account_move",
        "mixin.account_move_single_line",
        "mixin.transaction_pricelist",
    ]

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True

    # Attributes related to add element on form view automatically
    _automatically_insert_multiple_approval_page = True
    _statusbar_visible_label = "draft,confirm,open,done"
    _policy_field_order = [
        "confirm_ok",
        "open_ok",
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
        "dom_open",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "open"

    # account.move.line
    _journal_id_field_name = "journal_id"
    _move_id_field_name = "move_id"
    _accounting_date_field_name = "date"
    _currency_id_field_name = "currency_id"
    _company_currency_id_field_name = "company_currency_id"

    _account_id_field_name = "payable_account_id"
    _partner_id_field_name = "employee_partner_id"
    _analytic_account_id_field_name = "analytic_account_id"
    _amount_currency_field_name = "amount_total"
    _date_field_name = "date"
    _label_field_name = "name"
    _date_due_field_name = "date_due"
    _need_date_due = True
    _normal_amount = "credit"

    # Tax computation
    _tax_lines_field_name = "tax_ids"
    _tax_on_self = False
    _tax_source_recordset_field_name = "per_diem_ids"
    _price_unit_field_name = "price_unit"
    _quantity_field_name = "uom_quantity"

    type_id = fields.Many2one(
        comodel_name="employee_business_trip_type",
        string="Type",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_due = fields.Date(
        string="Date Due",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    # Origin Destination
    origin_id = fields.Many2one(
        comodel_name="res.city",
        string="Origin",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_origin_ids = fields.Many2many(
        comodel_name="res.city",
        string="Allowed Origins",
        compute="_compute_allowed_origin_ids",
        store=False,
        compute_sudo=True,
    )
    destination_id = fields.Many2one(
        comodel_name="res.city",
        string="Destination",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_destination_ids = fields.Many2many(
        comodel_name="res.city",
        string="Allowed Destinations",
        compute="_compute_allowed_destination_ids",
        store=False,
        compute_sudo=True,
    )
    # Currency + additional
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")
    allowed_currency_ids = fields.Many2many(
        comodel_name="res.currency",
        string="Allowed Currencies",
        compute="_compute_allowed_currency_ids",
        store=False,
        compute_sudo=True,
    )
    # Pricelist + additional
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Pricelist",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        string="Allowed Pricelists",
        compute="_compute_allowed_pricelist_ids",
        store=False,
        compute_sudo=True,
    )
    # Accounting
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        required=False,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    payable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Payable Account",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    move_id = fields.Many2one(comodel_name="account.move", string="Move", readonly=True)
    payable_move_line_id = fields.Many2one(
        comodel_name="account.move.line", string="Payable Move Line", readonly=True
    )
    realized = fields.Boolean(
        related="payable_move_line_id.reconciled",
        string="Realized",
        store=True,
        compute_sudo=True,
    )
    # Per diem
    per_diem_ids = fields.One2many(
        comodel_name="employee_business_trip.per_diem",
        inverse_name="employee_business_trip_id",
        string="Per Diem",
    )
    # Product
    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Allowed Products",
        compute="_compute_allowed_product_ids",
        store=False,
        compute_sudo=True,
    )
    # Tax
    tax_ids = fields.One2many(
        comodel_name="employee_business_trip.tax",
        inverse_name="employee_business_trip_id",
        string="Taxes",
    )
    amount_untaxed = fields.Monetary(
        compute="_compute_amount",
        string="Untaxed Amount",
        # currency_field="company_currency_id",
        store=True,
    )
    amount_tax = fields.Monetary(
        compute="_compute_amount",
        string="Tax Amount",
        # currency_field="company_currency_id",
        store=True,
    )
    amount_total = fields.Monetary(
        compute="_compute_amount",
        string="Total Amount",
        # currency_field="company_currency_id",
        store=True,
    )
    amount_realized = fields.Monetary(
        compute="_compute_realized",
        string="Realized Amount",
        # currency_field="company_currency_id",
        store=True,
    )
    amount_residual = fields.Monetary(
        compute="_compute_realized",
        string="Residual Amount",
        # currency_field="company_currency_id",
        store=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("reject", "Reject"),
        ],
        string="Status",
        default="draft",
    )

    @api.model
    def _get_policy_field(self):
        res = super(EmployeeBusinessTrip, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "open_ok",
            "approve_ok",
            "reject_ok",
            "restart_approval_ok",
            "cancel_ok",
            "restart_ok",
            "done_ok",
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

    @api.onchange("type_id")
    def onchange_journal_id(self):
        self.journal_id = False
        if self.type_id:
            self.journal_id = self.type_id.journal_id.id

    @api.onchange("type_id")
    def onchange_payable_account_id(self):
        self.payable_account_id = False
        if self.type_id:
            self.payable_account_id = self.type_id.payable_account_id.id

    @api.depends("type_id")
    def _compute_allowed_origin_ids(self):
        for record in self:
            result = []
            if record.type_id:
                ttype = record.type_id
                if ttype.origin_selection_method == "manual":
                    result = ttype.origin_ids.ids
                elif ttype.origin_selection_method == "domain":
                    criteria = safe_eval(ttype.origin_domain, {})
                    result = self.env["res.city"].search(criteria).ids
                elif ttype.origin_selection_method == "code":
                    localdict = self._get_localdict()
                    try:
                        safe_eval(
                            ttype.origin_python_code,
                            localdict,
                            mode="exec",
                            nocopy=True,
                        )
                        result = localdict["result"]
                    except Exception as error:
                        raise UserError(_("Error evaluating conditions.\n %s") % error)

            record.allowed_origin_ids = result

    @api.depends("type_id")
    def _compute_allowed_destination_ids(self):
        for record in self:
            result = []
            if record.type_id:
                ttype = record.type_id
                if ttype.destination_selection_method == "manual":
                    result = ttype.destination_ids.ids
                elif ttype.destination_selection_method == "domain":
                    criteria = safe_eval(ttype.destination_domain, {})
                    result = self.env["res.city"].search(criteria).ids
                elif ttype.destination_selection_method == "code":
                    localdict = self._get_localdict()
                    try:
                        safe_eval(
                            ttype.destination_python_code,
                            localdict,
                            mode="exec",
                            nocopy=True,
                        )
                        result = localdict["result"]
                    except Exception as error:
                        raise UserError(_("Error evaluating conditions.\n %s") % error)

            record.allowed_destination_ids = result

    @api.depends("type_id")
    def _compute_allowed_product_ids(self):
        for record in self:
            result = []
            if record.type_id:
                ttype = record.type_id
                if ttype.product_selection_method == "manual":
                    result = ttype.product_ids.ids
                elif ttype.product_selection_method == "domain":
                    criteria = safe_eval(ttype.product_domain, {})
                    result = self.env["product.product"].search(criteria).ids
                elif ttype.product_selection_method == "code":
                    localdict = self._get_localdict()
                    try:
                        safe_eval(
                            ttype.product_python_code,
                            localdict,
                            mode="exec",
                            nocopy=True,
                        )
                        result = localdict["result"]
                    except Exception as error:
                        raise UserError(_("Error evaluating conditions.\n %s") % error)

            record.allowed_product_ids = result

    @api.depends("type_id", "allowed_currency_ids")
    def _compute_allowed_pricelist_ids(self):
        for record in self:
            result = []
            if record.type_id:
                ttype = record.type_id
                if ttype.pricelist_selection_method == "manual":
                    result = ttype.pricelist_ids.ids
                elif ttype.pricelist_selection_method == "domain":
                    criteria = safe_eval(ttype.pricelist_domain, {})
                    result = self.env["product.pricelist"].search(criteria)
                elif ttype.pricelist_selection_method == "code":
                    localdict = self._get_localdict()
                    try:
                        safe_eval(
                            ttype.pricelist_python_code,
                            localdict,
                            mode="exec",
                            nocopy=True,
                        )
                        result = localdict["result"]
                    except Exception as error:
                        raise UserError(_("Error evaluating conditions.\n %s") % error)

            record.allowed_pricelist_ids = result

    @api.depends("type_id")
    def _compute_allowed_currency_ids(self):
        for record in self:
            result = []
            if record.type_id:
                ttype = record.type_id
                if ttype.currency_selection_method == "manual":
                    result = ttype.currency_ids.ids
                elif ttype.currency_selection_method == "domain":
                    criteria = safe_eval(ttype.currency_domain, {})
                    result = self.env["res.currency"].search(criteria).ids
                elif ttype.currency_selection_method == "code":
                    localdict = self._get_localdict()
                    try:
                        safe_eval(
                            ttype.currency_python_code,
                            localdict,
                            mode="exec",
                            nocopy=True,
                        )
                        result = localdict["result"]
                    except Exception as error:
                        raise UserError(_("Error evaluating conditions.\n %s") % error)

            record.allowed_currency_ids = result

    @api.depends(
        "per_diem_ids", "per_diem_ids.price_subtotal", "tax_ids", "tax_ids.tax_amount"
    )
    def _compute_amount(self):
        for record in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0

            for per_diem in record.per_diem_ids:
                amount_untaxed += per_diem.price_subtotal

            for tax in record.tax_ids:
                amount_tax += tax.tax_amount

            amount_total = amount_untaxed + amount_tax

            record.amount_untaxed = amount_untaxed
            record.amount_tax = amount_tax
            record.amount_total = amount_total

    @api.depends(
        "payable_move_line_id",
        "payable_move_line_id.amount_residual_currency",
        "payable_move_line_id.reconciled",
    )
    def _compute_realized(self):
        for record in self:
            amount_realized = 0.0
            amount_residual = 0.0

            if record.payable_move_line_id:
                amount_residual = (
                    -1.0 * record.payable_move_line_id.amount_residual_currency
                )
                amount_realized = record.amount_total - amount_residual

            record.amount_realized = amount_realized
            record.amount_residual = amount_residual

    @ssi_decorator.pre_confirm_action()
    def _01_compute_tax(self):
        self.ensure_one()
        self._recompute_standard_tax()

    @ssi_decorator.post_open_action()
    def _10_create_accounting_entry(self):
        self.ensure_one()

        if not self.per_diem_ids:
            return True

        if self.move_id:
            return True

        self._create_standard_move()  # Mixin
        ml = self._create_standard_ml()  # Mixin
        self.write(
            {
                "payable_move_line_id": ml.id,
            }
        )

        for per_diem in self.per_diem_ids:
            per_diem._create_standard_ml()  # Mixin

        for tax in self.tax_ids:
            tax._create_standard_ml()  # Mixin

        self._post_standard_move()  # Mixin

    @ssi_decorator.post_open_action()
    def _10_skip_open(self):
        self.ensure_one()
        if not self.move_id:
            self.action_done()

    @ssi_decorator.post_cancel_action()
    def _delete_accounting_entry(self):
        self.ensure_one()
        self._delete_standard_move()  # Mixin

    def action_compute_tax(self):
        for record in self:
            record._recompute_standard_tax()

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch
