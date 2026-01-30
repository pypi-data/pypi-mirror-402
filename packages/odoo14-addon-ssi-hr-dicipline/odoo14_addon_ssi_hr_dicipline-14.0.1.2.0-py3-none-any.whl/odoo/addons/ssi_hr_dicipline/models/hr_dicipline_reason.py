# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDiciplineReason(models.Model):
    _name = "hr.dicipline_reason"
    _inherit = ["mixin.master_data"]
    _description = "Employee Dicipline Reason"

    name = fields.Char(
        string="Employee Dicipline Reason",
    )
