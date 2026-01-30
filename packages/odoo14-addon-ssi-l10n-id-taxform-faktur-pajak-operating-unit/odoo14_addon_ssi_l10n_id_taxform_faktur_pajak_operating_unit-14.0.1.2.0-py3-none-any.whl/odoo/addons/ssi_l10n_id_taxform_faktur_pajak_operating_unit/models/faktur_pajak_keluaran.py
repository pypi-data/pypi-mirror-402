# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


class FakturPajakKeluaran(models.Model):
    _name = "faktur_pajak_keluaran"
    _inherit = [
        "faktur_pajak_keluaran",
        "mixin.single_operating_unit",
    ]

    @api.depends(
        "operating_unit_id",
        "operating_unit_id.partner_id",
        "operating_unit_id.partner_id.nitku",
    )
    def _compute_efaktur_seller_id_tku(self):
        for record in self:
            result = "0000000000000000"
            if (
                record.operating_unit_id
                and record.operating_unit_id.partner_id
                and record.operating_unit_id.partner_id.nitku
            ):
                result = record.operating_unit_id.partner_id.nitku
            record.efaktur_seller_id_tku = result

    efaktur_seller_id_tku = fields.Char(
        compute="_compute_efaktur_seller_id_tku",
        compute_sudo=True,
    )

    @api.depends(
        "company_id",
        "company_id.partner_id",
        "company_id.partner_id.vat",
    )
    def _compute_efaktur_company_npwp(self):
        for record in self:
            result = "000000000000000"
            if record.operating_unit_id:
                partner = record.operating_unit_id.partner_id
            else:
                partner = record.company_id.partner_id

            if partner and partner.vat:
                npwp = partner.vat
                result = ""
                for s in re.findall(r"\d+", npwp):
                    result += s
            record.efaktur_company_npwp = result

    efaktur_company_npwp = fields.Char(
        string="Company NPWP",
        compute="_compute_efaktur_company_npwp",
        store=True,
        compute_sudo=True,
    )
