# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.depends(
        "date_join",
    )
    def _compute_tax_period(self):
        for employee in self:
            joining_tax_period_id = False
            joining_tax_year_id = False

            if employee.date_join:
                obj_period = self.env["l10n_id.tax_period"]
                period = obj_period._find_period(employee.date_join)
                if period:
                    joining_tax_period_id = period
                    joining_tax_year_id = period.year_id

            employee.joining_tax_period_id = joining_tax_period_id
            employee.joining_tax_year_id = joining_tax_year_id

    joining_tax_period_id = fields.Many2one(
        string="Joining Tax Period",
        comodel_name="l10n_id.tax_period",
        compute="_compute_tax_period",
        store=True,
        compute_sudo=True,
    )
    joining_tax_year_id = fields.Many2one(
        string="Joining Tax Year",
        comodel_name="l10n_id.tax_year",
        compute="_compute_tax_period",
        store=True,
        compute_sudo=True,
    )
