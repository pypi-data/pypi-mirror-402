# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HrJobGradeCategory(models.Model):
    _name = "hr.job_grade_category"
    _inherit = ["mixin.master_data"]
    _description = "Job Grade Category"

    name = fields.Char(
        string="Job Grade Category",
    )
