# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=locally-disabled, manifest-required-author
{
    "name": "Klik Pajak Integration",
    "version": "14.0.1.3.0",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia, OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "ssi_l10n_id_taxform_faktur_pajak",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/policy_template_data.xml",
        "menu.xml",
        "views/res_company_views.xml",
        "views/klikpajak_backend_views.xml",
        "views/faktur_pajak_keluaran_views.xml",
        "views/buyer_document_views.xml",
    ],
}
