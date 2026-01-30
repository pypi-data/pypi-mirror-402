# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pph_1721a1_config = fields.One2many(
        string="Form 1721 A1 Config",
        comodel_name="l10n_id.bukti_potong_pph_1721_a1_config",
        inverse_name="company_id",
    )

    def _get_python_1721_config(self, field):
        self.ensure_one()
        result = False
        if self.pph_1721a1_config:
            config_id = self.pph_1721a1_config.filtered(
                lambda x: x.field_id.name == field
            )
            if config_id:
                result = config_id.python_code
        return result
