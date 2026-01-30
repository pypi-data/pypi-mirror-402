# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import hashlib
import hmac
import time
from datetime import datetime
from wsgiref.handlers import format_date_time

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class KlikpajakBackend(models.Model):
    _name = "klikpajak_backend"
    _inherit = [
        "mixin.master_data",
    ]
    _description = "Klik Pajak Backend"
    _automatically_insert_print_button = False

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id.id

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self._default_company_id(),
        copy=True,
    )
    auth_method = fields.Selection(
        string="Authentication",
        selection=[
            ("jwt", "JWT (JSON Web Token)"),
            ("basic", "Basic Authentication"),
            ("hmac", "HMAC (Hash-based Message Authentication Code)"),
        ],
        copy=False,
        default="hmac",
        required=True,
        readonly=False,
    )
    parameter_value_ids = fields.One2many(
        string="API Parameters",
        comodel_name="klikpajak_backend.parameter",
        inverse_name="backend_id",
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("running", "Running"),
        ],
        copy=False,
        default="draft",
        required=True,
        readonly=True,
    )

    # GENERAL
    base_url = fields.Char(
        string="Base URL",
        required=True,
        copy=True,
    )
    exclude_product_ids = fields.Many2many(
        string="Exclude Products",
        comodel_name="product.product",
        relation="rel_company_2_klikpajak_product",
        column1="company_id",
        column2="product_id",
    )
    # API
    sale_invoice_api = fields.Char(
        string="Create Sale Invoice",
        required=True,
        copy=True,
        default="/v2/klikpajak/v2/efaktur/out",
    )
    cancel_sale_invoice_api = fields.Char(
        string="Cancel Sale Invoice",
        required=True,
        copy=True,
        default="/v2/klikpajak/v2/efaktur/out/{id}/cancel/",
    )
    approve_sale_invoice_api = fields.Char(
        string="Approve Sale Invoice",
        required=True,
        copy=True,
        default="/v2/klikpajak/v2/efaktur/out/{id}/approve/",
    )
    retrieve_sale_invoice_api = fields.Char(
        string="Retrieve Sale Invoice",
        required=True,
        copy=True,
        default="/v2/klikpajak/v2/efaktur/out/{id}",
    )
    # BUAT AUTH JWT
    token = fields.Char(
        string="Token",
        copy=False,
    )
    # BUAT AUTH BASIC
    username = fields.Char(
        string="Username",
        copy=False,
    )
    password = fields.Char(
        string="Password",
        copy=False,
    )
    # BUAT AUTH BASIC USE PYTHON
    client_id = fields.Char(
        string="Client ID",
        copy=False,
    )
    client_secret = fields.Char(
        string="Client Secret",
        copy=False,
    )

    def _get_klikpajak_date_header(self):
        self.ensure_one()
        now_timestamp = time.mktime(datetime.utcnow().timetuple())
        return format_date_time(now_timestamp)

    def _get_klikpajak_sale_invoice_params(self):
        self.ensure_one()
        return {
            "auto_approval": "true",
            "auto_calculate": "true",
        }

    def _get_klikpajak_header(self):
        self.ensure_one()
        return {
            "Date": self._get_klikpajak_date_header(),
        }

    def _get_klikpajak_authorization_header(self, signature):
        self.ensure_one()
        result = 'hmac username="%s",' % self.client_id
        result += ' algorithm="hmac-sha256",'
        result += ' headers="date request-line",'
        result += ' signature="%s"' % (signature)
        return result

    def _get_signature(self, date, path, method):
        secret = self.client_secret
        request_line = method + " " + path + " HTTP/1.1"
        payload_tupple = ("date: " + date, request_line)
        payload = "\n".join(payload_tupple)

        hmac1 = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256,
        )
        message_digest1 = hmac1.digest()

        signature = base64.b64encode(message_digest1).decode("utf-8")
        return signature

    def _get_header(self, path, method):
        self.ensure_one()
        result = self._get_klikpajak_header()
        date = format_date_time(datetime.now().timestamp())
        signature = self._get_signature(date, path, method)
        authorization = self._get_klikpajak_authorization_header(signature)
        result.update(
            {
                "Authorization": authorization,
            }
        )
        return result

    def _get_hmac(self):
        self.ensure_one()
        date = format_date_time(datetime.now().timestamp())
        api_url = self.base_url + self.sale_invoice_api
        result = self._get_signature(date, api_url, "POST")
        return result

    def action_get_hmac(self):
        for record in self:
            result = record._get_hmac()
            raise ValidationError(f"Result: {result}")

    def action_running(self):
        for record in self:
            check_running_backend_ids = self.search(
                [
                    ("state", "=", "running"),
                    ("company_id", "=", self.env.user.company_id.id),
                    ("id", "!=", record.id),
                ]
            )
            if check_running_backend_ids:
                check_running_backend_ids.write({"state": "draft"})
            record.company_id.write({"klikpajak_backend_id": record.id})
            record.write({"state": "running"})

    def action_restart(self):
        for record in self:
            record.company_id.write({"klikpajak_backend_id": False})
            record.write({"state": "draft"})
