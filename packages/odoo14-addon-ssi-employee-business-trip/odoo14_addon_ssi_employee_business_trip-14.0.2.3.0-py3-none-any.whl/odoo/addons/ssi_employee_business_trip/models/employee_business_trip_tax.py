# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EmployeeBusinessTripTax(models.Model):
    _name = "employee_business_trip.tax"
    _description = "Employee Business Trip - Tax"
    _inherit = ["mixin.tax_line"]

    # account.move.line
    _partner_id_field_name = "employee_partner_id"
    _analytic_account_id_field_name = "analytic_account_id"
    _label_field_name = "name"
    _amount_currency_field_name = "tax_amount"
    _normal_amount = "debit"

    employee_business_trip_id = fields.Many2one(
        comodel_name="employee_business_trip",
        string="Employee Business Trip",
        required=True,
        ondelete="cascade",
    )
    move_id = fields.Many2one(
        related="employee_business_trip_id.move_id", compute_sudo=True
    )
    currency_id = fields.Many2one(
        related="employee_business_trip_id.currency_id", compute_sudo=True
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
    # Additional
    account_move_line_id = fields.Many2one(
        string="Journal Item",
        comodel_name="account.move.line",
        copy=False,
    )
