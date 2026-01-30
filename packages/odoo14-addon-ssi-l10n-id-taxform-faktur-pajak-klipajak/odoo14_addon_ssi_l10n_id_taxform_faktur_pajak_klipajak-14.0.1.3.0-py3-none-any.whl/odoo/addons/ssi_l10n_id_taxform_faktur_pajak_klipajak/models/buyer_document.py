# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BuyerDocument(models.Model):
    _inherit = ["buyer_document"]

    klikpajak_code = fields.Char(
        string="Klik Pajak Code",
        copy=False,
    )
