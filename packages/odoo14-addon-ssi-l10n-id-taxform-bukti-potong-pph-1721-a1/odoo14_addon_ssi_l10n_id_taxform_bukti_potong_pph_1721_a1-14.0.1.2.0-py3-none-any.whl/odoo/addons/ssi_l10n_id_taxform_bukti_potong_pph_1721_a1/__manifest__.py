# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# pylint: disable=locally-disabled, manifest-required-author
{
    "name": "Indonesia - Bukti Potong PPh 21 Formulir 1721 A1",
    "version": "14.0.1.2.0",
    "category": "localization",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia, OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "ssi_transaction_mixin",
        "ssi_transaction_confirm_mixin",
        "ssi_transaction_done_mixin",
        "ssi_transaction_cancel_mixin",
        "ssi_l10n_id_taxform_bukti_potong_pph_mixin",
        "ssi_partner",
        "ssi_l10n_id_partner_identification_kependudukan",
        "ssi_l10n_id_taxform_pph_21",
        "report_py3o",
        "ssi_print_mixin",
        "partner_contact_in_several_companies",
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_group_data.xml",
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/ir_sequence_data.xml",
        "data/sequence_template_data.xml",
        "data/policy_template_data.xml",
        "data/approval_template_data.xml",
        "reports/bukti_potong_pph_1721_a1_report.xml",
        "views/bukti_potong_pph_1721_a1_views.xml",
        "views/bukti_potong_pph_1721_a1_config_views.xml",
        "views/res_company_views.xml",
    ],
    "demo": [
        # "demo/account_journal_demo.xml",
        # "demo/account_account_demo.xml",
        # "demo/account_tax_demo.xml",
        # "demo/l10n_id_bukti_potong_type_demo.xml",
    ],
}
