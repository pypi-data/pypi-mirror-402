# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HrEmploymentStatus(models.Model):
    _name = "hr.employment_status"
    _inherit = ["mixin.master_data"]
    _description = "Employment Status"

    name = fields.Char(
        string="Employment Status",
    )
