# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=locally-disabled, manifest-required-author
{
    "name": "Indonesia's Taxform - PPh 21 Computation On Payslip",
    "version": "14.0.1.1.0",
    "category": "localization",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_l10n_id_taxform_pph_21",
        "ssi_hr_payroll",
    ],
    "data": [
        "views/hr_employee_views.xml",
        "views/hr_payslip_views.xml",
    ],
}
