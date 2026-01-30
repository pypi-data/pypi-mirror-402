# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json
import logging
import uuid
from datetime import datetime

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FakturPajakKeluaran(models.Model):
    _inherit = [
        "faktur_pajak_keluaran",
    ]

    change_backend_ok = fields.Boolean(
        string="Can Change Backend",
        compute="_compute_policy",
        compute_sudo=True,
        help="""Change Backend policy
* If active user can see and change 'Backend' field""",
    )

    @api.model
    def _get_klikpajak_backend_id(self):
        company = self.env.company
        backend = company.klikpajak_backend_id
        return backend and backend.id or False

    klikpajak_backend_id = fields.Many2one(
        string="Backend",
        comodel_name="klikpajak_backend",
        default=lambda self: self._get_klikpajak_backend_id(),
        required=True,
    )

    klikpajak_id = fields.Integer(
        string="Klikpajak ID",
        readonly=True,
        copy=False,
    )
    klikpajak_invoice_status = fields.Selection(
        string="Klikpajak Invoice Status",
        selection=[
            ("NORMAL", "Normal"),
            ("NORMAL_SUB", "Substitution"),
            ("SUBSTITUED", "Substituted"),
            ("CANCELLED", "Cancel"),
        ],
        readonly=True,
        copy=False,
    )
    klikpajak_approval_status = fields.Selection(
        string="Klikpajak Approval Status",
        selection=[
            ("DRAFT", "Draft"),
            ("APPROVED", "Approved"),
            ("IN_PROGRESS", "In Progress"),
            ("REJECTED", "Reject"),
        ],
        readonly=True,
        copy=False,
    )
    klikpajak_cancel_status = fields.Char(
        string="Klikpajak Cancel Status",
        readonly=True,
        copy=False,
    )
    klikpajak_qrcode_link = fields.Char(
        string="Klikpajak QRCode Linke",
        readonly=True,
        copy=False,
    )
    klikpajak_invoice_link = fields.Char(
        string="Klikpajak Invoice Linke",
        readonly=True,
        copy=False,
    )
    klik_pajak_submit_ok = fields.Boolean(
        string="Klikpajak Submit Ok",
        compute="_compute_klikpajak_state",
        store=False,
        compute_sudo=True,
    )
    klik_pajak_approve_ok = fields.Boolean(
        string="Klikpajak Approve Ok",
        compute="_compute_klikpajak_state",
        store=False,
        compute_sudo=True,
    )
    klik_pajak_cancel_ok = fields.Boolean(
        string="Klikpajak Cancel Ok",
        compute="_compute_klikpajak_state",
        store=False,
        compute_sudo=True,
    )
    klik_pajak_resubmit_ok = fields.Boolean(
        string="Klikpajak Resubmit Ok",
        compute="_compute_klikpajak_state",
        store=False,
        compute_sudo=True,
    )

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "change_backend_ok",
        ]
        res += policy_field
        return res

    def _compute_policy(self):
        _super = super()
        _super._compute_policy()

    @api.depends(
        "klikpajak_id",
        "klikpajak_invoice_status",
        "klikpajak_approval_status",
        # "lock_taxform",
    )
    def _compute_klikpajak_state(self):
        for record in self:
            record.klik_pajak_submit_ok = record.klik_pajak_cancel_ok = (
                record.klik_pajak_approve_ok
            ) = record.klik_pajak_resubmit_ok = False

            # if record.klikpajak_id == 0 and record.lock_taxform:
            #     record.klik_pajak_submit_ok = True
            if record.klikpajak_id == 0:
                record.klik_pajak_submit_ok = True
            elif (
                record.klikpajak_invoice_status == "NORMAL"
                or record.klikpajak_invoice_status == "NORMAL_SUB"
            ) and record.klikpajak_approval_status == "APPROVED":
                record.klik_pajak_cancel_ok = True
                record.klik_pajak_resubmit_ok = True
            elif (
                record.klikpajak_invoice_status == "NORMAL"
                or record.klikpajak_invoice_status == "NORMAL_SUB"
            ) and record.klikpajak_approval_status == "DRAFT":
                record.klik_pajak_approve_ok = True

    def action_klikpajak_submit_sale_invoice(self):
        for record in self:
            record._klikpajak_submit_sale_invoice()

    def _klikpajak_submit_sale_invoice(self):
        self.ensure_one()
        backend = self.klikpajak_backend_id
        params = {}
        if not backend:
            strWarning = _("No backend define for klikpajak")
            raise UserError(strWarning)

        base_url = backend.base_url
        path = backend.sale_invoice_api
        api_url = base_url + path

        headers = backend._get_header(path, "POST")
        headers.update(
            {
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4()),
            }
        )
        # Mengambil parameters dari backend
        if backend.parameter_value_ids:
            for param in backend.parameter_value_ids:
                params[param.name] = param.parse_value()

        json_data = self._prepare_klikpajak_json_data()

        response = requests.post(
            api_url, params=params, headers=headers, json=json_data
        )

        if response.status_code == 201 or response.status_code == 200:
            response_json = json.loads(response.text)
            data = response_json["data"]
            self.write(self._prepare_faktur_pajak_keluaran_data(data))
            if self.klikpajak_approval_status == "IN_PROGRESS":
                self._klikpajak_retrieve_sale_invoice()
            attachment, message = self._get_klikpajak_pdf(self.klikpajak_invoice_link)
            self._post_klikpajak_pdf(attachment, message)
        else:
            str_error = """Response code: {}

            {}""".format(
                response.status_code,
                response.text,
            )

            raise UserError(str_error)

    def action_klikpajak_resubmit_sale_invoice(self):
        for record in self:
            record._klikpajak_resubmit_sale_invoice()

    def _klikpajak_resubmit_sale_invoice(self):
        self.ensure_one()
        backend = self.klikpajak_backend_id
        params = {}
        if not backend:
            strWarning = _("No backend define for klikpajak")
            raise UserError(strWarning)

        base_url = backend.base_url
        path = backend.sale_invoice_api
        api_url = base_url + path

        headers = backend._get_header(path, "POST")
        headers.update(
            {
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4()),
            }
        )
        # Mengambil parameters dari backend
        if backend.parameter_value_ids:
            for param in backend.parameter_value_ids:
                params[param.name] = param.parse_value()

        json_data = self._prepare_klikpajak_json_data()
        json_data.update(
            {
                "substitution_flag": True,
                "substituted_tax_invoice_id": self.klikpajak_id,
            }
        )

        response = requests.post(
            api_url, params=params, headers=headers, json=json_data
        )

        if response.status_code == 201 or response.status_code == 200:
            response_json = json.loads(response.text)
            data = response_json["data"]
            self.write(self._prepare_faktur_pajak_keluaran_data(data))
            if self.klikpajak_approval_status == "IN_PROGRESS":
                self._klikpajak_retrieve_sale_invoice()
            attachment, message = self._get_klikpajak_pdf(self.klikpajak_invoice_link)
            self._post_klikpajak_pdf(attachment, message)
        else:
            str_error = """Response code: {}

            {}""".format(
                response.status_code,
                response.text,
            )

            raise UserError(str_error)

    def _prepare_klikpajak_json_data(self):
        self.ensure_one()

        # Format document_date ke YYYY-MM-DD
        document_date = None
        if self.efaktur_tanggal_faktur:
            if isinstance(self.efaktur_tanggal_faktur, str):
                # Jika sudah string, pastikan formatnya YYYY-MM-DD
                try:
                    # Coba parse berbagai format tanggal yang mungkin
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                        try:
                            dt = datetime.strptime(self.efaktur_tanggal_faktur, fmt)
                            document_date = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                    if not document_date:
                        # Jika tidak bisa diparse,
                        # gunakan string asli jika sudah format YYYY-MM-DD
                        if (
                            len(self.efaktur_tanggal_faktur) == 10
                            and self.efaktur_tanggal_faktur[4] == "-"
                            and self.efaktur_tanggal_faktur[7] == "-"
                        ):
                            document_date = self.efaktur_tanggal_faktur
                except Exception:
                    document_date = self.efaktur_tanggal_faktur
            else:
                # Jika datetime/date object
                document_date = self.efaktur_tanggal_faktur.strftime("%Y-%m-%d")

        result = {
            "client_reference_id": self.efaktur_of_name,
            "reference": self.efaktur_referensi,
            "transaction_detail": self.efaktur_kd_jenis_transaksi,
            "substitution_flag": int(self.efaktur_fg_pengganti),
            "substituted_tax_invoice_id": None,
            "document_date": document_date,
            "customer": self._prepare_klikpajak_customer_json_data(),
            "items": self._prepare_klikpajak_items_json_data(),
            "downpayment_flag": 0,
            "total_price": 0,
            "total_stlg": 0,
            "total_other_tax_base": 0,
            "total_tax_base": 0,
            "total_vat": 0,
            "total_discount": 0,
        }
        if self.efaktur_of_add_info:
            result["additional_trx_detail"] = self.efaktur_of_add_info

        return result

    def _prepare_faktur_pajak_keluaran_data(self, data):
        self.ensure_one()
        return {
            "klikpajak_id": data["id"],
            "klikpajak_invoice_status": data["invoice_status"],
            "klikpajak_approval_status": data["approval_status"],
            "klikpajak_qrcode_link": data["qr_code"],
            "klikpajak_invoice_link": data["tax_invoice_link"],
            "name": (
                data["tax_invoice_number"] if data["tax_invoice_number"] else self.name
            ),
        }

    def _prepare_klikpajak_customer_json_data(self):
        self.ensure_one()
        return {
            "id_type": self.buyer_document_id.klikpajak_code,
            "name": self.efaktur_nama,
            "country_code": self.efaktur_country,
            "npwp": self.efaktur_npwp,
            "address": self.efaktur_alamat_lengkap,
        }

    def _prepare_klikpajak_items_json_data(self):
        self.ensure_one()
        result = []

        if self.efaktur_mode == "detail":
            for detail in self.detail_ids:
                if detail.efaktur_of_opt == "A":
                    goods_service = "GOODS"
                else:
                    goods_service = "SERVICES"
                vals = {
                    "goods_service": goods_service,
                    "goods_service_name": detail.efaktur_of_name,
                    "unit_measurement": detail.efaktur_of_unit,
                    "unit_price": detail.efaktur_of_harga_satuan,
                    "quantity": detail.efaktur_of_jumlah_barang,
                    "discount": detail.efaktur_of_diskon,
                    "ppnbm_rate": 0,
                    "tax_base": 0,
                    "vat": 0,
                    "selling_price": 0,
                }
                result.append(vals)
        else:
            if self.efaktur_of_opt == "A":
                goods_service = "GOODS"
            else:
                goods_service = "SERVICES"
            uom_unit = self.header_uom_id
            vals = {
                "goods_service": goods_service,
                "goods_service_name": self.efaktur_of_name,
                "unit_measurement": uom_unit.efaktur_code,
                "unit_price": self.efaktur_of_harga_satuan,
                "quantity": self.efaktur_of_jumlah_barang,
                "discount": self.efaktur_of_diskon,
                "ppnbm_rate": 0,
                "tax_base": 0,
                "vat": 0,
                "selling_price": 0,
            }
            result.append(vals)
        return result

    def _get_klikpajak_pdf(self, url):
        self.ensure_one()
        attachment = False
        message = ""
        url = url.replace("efaktur-v2", "efaktur")
        url = url.replace("preview", "pdf")
        url = url.replace("public", "public/api")
        IrAttachment = self.env["ir.attachment"]
        try:
            _logger.info("Downloading PDF from URL: ", url)
            r = requests.get(url, allow_redirects=True, timeout=30)
            r.raise_for_status()  # Raise an exception for bad status codes

            if not r.content:
                message = "No content received from PDF URL"
                return attachment, message

            # Verify content is PDF
            if not r.content.startswith(b"%PDF"):
                message = "Downloaded content is not a valid PDF file"
                return attachment, message

            b64_pdf = base64.b64encode(r.content)
            filename = "efaktur_" + self.name + ".pdf"
            ir_values = {
                "name": filename,
                "type": "binary",
                "datas": b64_pdf,
                "store_fname": filename,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/pdf",
                "description": "E-Faktur PDF from Klikpajak",
            }
            attachment = IrAttachment.create(ir_values)
            message = ("PDF attachment created successfully with ID: ", attachment.id)
            return attachment, message
        except requests.exceptions.RequestException as err:
            message = ("Failed to download PDF from Klikpajak: ", err)
            return attachment, message
        except Exception as err:
            message = ("Unexpected error while processing PDF: ", err)
            return attachment, message

    def _post_klikpajak_pdf(self, attachment, message):
        self.ensure_one()
        if attachment:
            message = "E-Faktur PDF is successfully downloaded"

        self.message_post(
            body=message,
            message_type="notification",
            attachment_ids=attachment and [attachment.id] or [],
            subject=_("E-Faktur PDF"),
        )

    def action_klikpajak_approve_sale_invoice(self):
        for record in self:
            record._klikpajak_approve_sale_invoice()

    def _klikpajak_approve_sale_invoice(self):
        self.ensure_one()
        backend = self.klikpajak_backend_id
        if not backend:
            strWarning = _("No backend define for klikpajak")
            raise UserError(strWarning)

        base_url = backend.base_url
        approve_sale_invoice_api = backend.approve_sale_invoice_api

        # Ganti {id} dengan klikpajak_id
        path = approve_sale_invoice_api.format(id=self.klikpajak_id)
        api_url = base_url + path

        headers = backend._get_header(path, "PUT")
        response = requests.put(api_url, headers=headers)

        if response.status_code == 201 or response.status_code == 200:
            response_json = json.loads(response.text)
            data = response_json["data"]
            self.write(
                {
                    "klikpajak_approval_status": data["approval_status"],
                }
            )
        else:
            str_error = """Response code: {}

            {}""".format(
                response.status_code,
                response.text,
            )

            raise UserError(str_error)

    def _klikpajak_retrieve_sale_invoice(self):
        self.ensure_one()
        backend = self.klikpajak_backend_id
        if not backend:
            strWarning = _("No backend define for klikpajak")
            raise UserError(strWarning)

        base_url = backend.base_url
        retrieve_sale_invoice_api = backend.retrieve_sale_invoice_api

        # Ganti {id} dengan klikpajak_id
        path = retrieve_sale_invoice_api.format(id=self.klikpajak_id)
        api_url = base_url + path

        headers = backend._get_header(path, "GET")
        response = requests.get(api_url, headers=headers)

        if response.status_code == 201 or response.status_code == 200:
            response_json = json.loads(response.text)
            data = response_json["data"]
            self.write(self._prepare_faktur_pajak_keluaran_data(data))
        else:
            str_error = """Response code: {}

            {}""".format(
                response.status_code,
                response.text,
            )

            raise UserError(str_error)

    def action_klikpajak_cancel_sale_invoice(self):
        for record in self:
            record._klikpajak_cancel_sale_invoice()

    def _klikpajak_cancel_sale_invoice(self):
        self.ensure_one()
        backend = self.klikpajak_backend_id
        if not backend:
            strWarning = _("No backend define for klikpajak")
            raise UserError(strWarning)

        base_url = backend.base_url
        cancel_sale_invoice_api = backend.cancel_sale_invoice_api

        # Ganti {id} dengan klikpajak_id
        path = cancel_sale_invoice_api.format(id=self.klikpajak_id)
        api_url = base_url + path

        headers = backend._get_header(path, "PUT")
        response = requests.put(api_url, headers=headers)

        if response.status_code == 201 or response.status_code == 200:
            response_json = json.loads(response.text)
            data = response_json["data"]
            self.write(
                {
                    "klikpajak_approval_status": data["approval_status"],
                }
            )
        else:
            str_error = """Response code: {}

            {}""".format(
                response.status_code,
                response.text,
            )

            raise UserError(str_error)

    def _has_klikpajak_pdf_attachment(self):
        """Check if klikpajak PDF attachment already exists"""
        self.ensure_one()
        IrAttachment = self.env["ir.attachment"]
        attachment = IrAttachment.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "like", "efaktur_%"),
                ("mimetype", "=", "application/pdf"),
            ],
            limit=1,
        )
        return attachment

    def action_redownload_klikpajak_pdf(self):
        """Manual action to download PDF from klikpajak"""
        for record in self:
            if not record.klikpajak_invoice_link:
                raise UserError(_("No invoice link available from Klikpajak"))

            # Check if PDF already exists
            existing_attachment = record._has_klikpajak_pdf_attachment()
            if existing_attachment:
                message = _("PDF already exists. Re-downloading...")
                record.message_post(body=message, message_type="notification")

            attachment, message = record._get_klikpajak_pdf(
                record.klikpajak_invoice_link
            )
            record._post_klikpajak_pdf(attachment, message)
