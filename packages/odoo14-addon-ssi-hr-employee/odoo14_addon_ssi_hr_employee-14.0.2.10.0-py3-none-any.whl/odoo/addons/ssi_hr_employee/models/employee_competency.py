# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class EmployeeCompetency(models.Model):
    _name = "employee_competency"
    _inherit = ["mixin.master_data"]
    _description = "Employee Competency"
