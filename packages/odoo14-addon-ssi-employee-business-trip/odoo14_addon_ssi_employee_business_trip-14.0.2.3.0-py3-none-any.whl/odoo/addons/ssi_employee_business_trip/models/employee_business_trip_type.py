# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EmployeeBusinessTripType(models.Model):
    _name = "employee_business_trip_type"
    _description = "Employee Business Trip Type"
    _inherit = ["mixin.master_data"]

    # Accounting
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal", required=True
    )
    payable_account_id = fields.Many2one(
        comodel_name="account.account", string="Payable Account", required=True
    )
    # Per diem
    product_selection_method = fields.Selection(
        default="domain",
        selection=[("manual", "Manual"), ("domain", "Domain"), ("code", "Python Code")],
        string="Product Selection Method",
        required=True,
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="rel_employee_business_trip_type_2_product",
        column1="type_id",
        column2="product_id",
        string="Products",
    )
    product_domain = fields.Text(default="[]", string="Product Domain")
    product_python_code = fields.Text(
        default="result = []", string="Product Python Code"
    )
    # Currency
    currency_selection_method = fields.Selection(
        default="domain",
        selection=[("manual", "Manual"), ("domain", "Domain"), ("code", "Python Code")],
        string="Currency Selection Method",
        required=True,
    )
    currency_ids = fields.Many2many(
        comodel_name="res.currency",
        relation="rel_employee_business_trip_type_2_currency",
        column1="type_id",
        column2="currency_id",
        string="Currencies",
    )
    currency_domain = fields.Text(default="[]", string="Currency Domain")
    currency_python_code = fields.Text(
        default="result = []", string="Currency Python Code"
    )
    # Pricelist
    pricelist_selection_method = fields.Selection(
        default="domain",
        selection=[("manual", "Manual"), ("domain", "Domain"), ("code", "Python Code")],
        string="Pricelist Selection Method",
        required=True,
    )
    pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        relation="rel_employee_business_trip_type_2_pricelist",
        column1="type_id",
        column2="pricelist_id",
        string="Pricelists",
    )
    pricelist_domain = fields.Text(default="[]", string="Pricelist Domain")
    pricelist_python_code = fields.Text(
        default="result = []", string="Pricelist Python Code"
    )
    # Origin
    origin_selection_method = fields.Selection(
        default="domain",
        selection=[("manual", "Manual"), ("domain", "Domain"), ("code", "Python Code")],
        string="Origin Selection Method",
        required=True,
    )
    origin_ids = fields.Many2many(
        comodel_name="res.city",
        relation="rel_employee_business_trip_type_2_origin",
        column1="type_id",
        column2="origin_id",
        string="Origins",
    )
    origin_domain = fields.Text(default="[]", string="Origin Domain")
    origin_python_code = fields.Text(default="result = []", string="Origin Python Code")
    # Destination
    destination_selection_method = fields.Selection(
        default="domain",
        selection=[("manual", "Manual"), ("domain", "Domain"), ("code", "Python Code")],
        string="Destination Selection Method",
        required=True,
    )
    destination_ids = fields.Many2many(
        comodel_name="res.city",
        relation="rel_employee_business_trip_type_2_destination",
        column1="type_id",
        column2="destination_id",
        string="Destinations",
    )
    destination_domain = fields.Text(default="[]", string="Destination Domain")
    destination_python_code = fields.Text(
        default="result = []", string="Destination Python Code"
    )
