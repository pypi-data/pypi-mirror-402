# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EmployeeBusinessTripPerDiem(models.Model):
    _name = "employee_business_trip.per_diem"
    _description = "Employee Business Trip - Per Diem"
    _inherit = ["mixin.product_line_account", "mixin.account_move_single_line"]

    # Accounting Entry Mixin
    _move_id_field_name = "move_id"
    _account_id_field_name = "account_id"
    _partner_id_field_name = "employee_partner_id"
    _analytic_account_id_field_name = "analytic_account_id"
    _currency_id_field_name = "currency_id"
    _company_currency_id_field_name = "company_currency_id"
    _amount_currency_field_name = "price_subtotal"
    _company_id_field_name = "company_id"
    _date_field_name = "date"
    _label_field_name = "name"
    _product_id_field_name = "product_id"
    _uom_id_field_name = "uom_id"
    _quantity_field_name = "uom_quantity"
    _price_unit_field_name = "price_unit"
    _normal_amount = "debit"

    employee_business_trip_id = fields.Many2one(
        comodel_name="employee_business_trip",
        string="Employee Business Trip",
        required=True,
        ondelete="cascade",
    )

    # Additional
    sequence = fields.Integer(string="Sequence")

    # Related to header
    # Needed for convinience

    move_id = fields.Many2one(
        related="employee_business_trip_id.move_id",
        compute_sudo=True,
    )
    currency_id = fields.Many2one(
        related="employee_business_trip_id.currency_id",
        compute_sudo=True,
    )
    company_id = fields.Many2one(
        related="employee_business_trip_id.company_id", compute_sudo=True
    )
    company_currency_id = fields.Many2one(
        related="employee_business_trip_id.company_currency_id",
        compute_sudo=True,
    )
    employee_partner_id = fields.Many2one(
        related="employee_business_trip_id.employee_partner_id",
        compute_sudo=True,
    )
    date = fields.Date(
        related="employee_business_trip_id.date_start", compute_sudo=True
    )
    pricelist_id = fields.Many2one(
        related="employee_business_trip_id.pricelist_id", compute_sudo=True
    )
