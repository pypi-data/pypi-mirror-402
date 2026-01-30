# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "HR Employee",
    "version": "14.0.2.10.0",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia, OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_hr_employee_personal_from_work_address",
        "ssi_hr_employee_experience_from_work_address",
        "ssi_hr_employee_language_from_work_address",
        "ssi_master_data_mixin",
    ],
    "data": [
        "security/res_group_data.xml",
        "security/ir.model.access.csv",
        "menu.xml",
        "views/hr_employment_status_views.xml",
        "views/hr_job_grade_category_views.xml",
        "views/hr_job_grade_views.xml",
        "views/hr_job_family_grade_views.xml",
        "views/hr_job_family_views.xml",
        "views/hr_job_family_level_views.xml",
        "views/hr_job_views.xml",
        "views/job_description_views.xml",
        "views/employee_skill_views.xml",
        "views/employee_competency_views.xml",
        "views/hr_employee_views.xml",
    ],
    "demo": [
        "demo/hr_employment_status_demo.xml",
        "demo/hr_job_grade_category_demo.xml",
        "demo/hr_job_grade_demo.xml",
        "demo/employee_skill.xml",
        "demo/employee_competency.xml",
    ],
}
