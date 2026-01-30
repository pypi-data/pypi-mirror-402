# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class l10nidBuktiPotongPPH1721A1Config(models.Model):
    _name = "l10n_id.bukti_potong_pph_1721_a1_config"
    _description = "Bukti Potong PPh 21 1721 A1 Config"

    company_id = fields.Many2one(
        string="# Company",
        comodel_name="res.company",
        ondelete="cascade",
    )

    def _get_allowed_field(self):
        res = [
            "penghasilan_01",
            "penghasilan_02",
            "penghasilan_03",
            "penghasilan_04",
            "penghasilan_05",
            "penghasilan_06",
            "penghasilan_07",
            "pengurang_10",
            "perhitungan_13",
            "perhitungan_18",
            "perhitungan_20",
        ]
        return res

    @api.depends(
        "company_id",
    )
    def _compute_allowed_field_ids(self):
        obj_fields = self.env["ir.model.fields"]

        for document in self:
            result = []
            criteria = [("model_id.model", "=", "l10n_id.bukti_potong_pph_1721_a1")]
            field_ids = obj_fields.search(criteria)
            if field_ids:
                result = field_ids.filtered(
                    lambda x: x.name in self._get_allowed_field()
                ).ids
            document.allowed_field_ids = result

    allowed_field_ids = fields.Many2many(
        string="Allowed Fields",
        comodel_name="ir.model.fields",
        compute="_compute_allowed_field_ids",
        store=False,
    )
    field_id = fields.Many2one(
        string="Field",
        comodel_name="ir.model.fields",
    )
    python_code = fields.Text(
        string="Python Code",
        default="""# Available locals:\n#  - rec: current record\n result = 0.0""",
    )
