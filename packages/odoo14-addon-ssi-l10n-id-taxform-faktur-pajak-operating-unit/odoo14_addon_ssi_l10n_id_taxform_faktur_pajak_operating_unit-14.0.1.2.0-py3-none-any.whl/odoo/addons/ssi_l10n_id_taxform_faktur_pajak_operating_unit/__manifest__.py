# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Faktur Pajak + Operating Unit",
    "version": "14.0.1.2.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_l10n_id_taxform_faktur_pajak",
        "ssi_operating_unit_mixin",
    ],
    "data": [
        "security/res_group/faktur_pajak_keluaran.xml",
        "security/ir_rule/faktur_pajak_keluaran.xml",
        "views/faktur_pajak_keluaran_views.xml",
    ],
    "demo": [],
}
