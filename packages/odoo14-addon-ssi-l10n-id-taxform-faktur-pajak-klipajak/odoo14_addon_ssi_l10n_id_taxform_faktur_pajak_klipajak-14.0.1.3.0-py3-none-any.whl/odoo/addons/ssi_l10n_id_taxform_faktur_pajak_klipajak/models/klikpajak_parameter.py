# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class KlikPajakBackendParameter(models.Model):
    _name = "klikpajak_backend.parameter"
    _description = "Klikpajak Backend Parameter Definition"

    backend_id = fields.Many2one(
        string="#Backend ID",
        comodel_name="klikpajak_backend",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(
        string="Parameter Name",
        required=True,
        help="Name of the parameter."
        "This is used to identify the parameter in the script.",
    )
    type = fields.Selection(
        string="Parameter Type",
        selection=[
            ("char", "String"),
            ("int", "Integer"),
            ("float", "Float"),
            ("bool", "Boolean"),
            ("json", "JSON Object"),
            ("date", "Date"),
            ("datetime", "Datetime"),
        ],
        default="char",
        required=True,
        help="Type of the parameter."
        "This determines how the parameter is processed in the script.",
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the parameter."
        "This is used to provide additional context or usage information.",
    )
    value = fields.Char(string="Value", help="Value for the parameter.")

    @api.constrains(
        "value",
        "type",
    )
    def _check_value_format(self):
        for record in self:
            t = record.type
            v = record.value
            try:
                if t == "int":
                    int(v)
                elif t == "float":
                    float(v)
                elif t == "bool":
                    if v.lower() not in ("1", "0", "true", "false", "yes", "no"):
                        raise ValueError()
                elif t == "json":
                    json.loads(v)
                elif t == "date":
                    datetime.strptime(v, "%Y-%m-%d")
                elif t == "datetime":
                    datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except Exception:
                raise ValidationError(
                    f"Invalid value format for parameter '{record.name}' (type {t})."
                )

    def parse_value(self):
        t = self.type
        v = self.value
        try:
            if t == "int":
                return int(v)
            elif t == "float":
                return float(v)
            elif t == "bool":
                return v.lower() in ("1", "true", "yes")
            elif t == "json":
                return json.loads(v)
            elif t == "date":
                return datetime.strptime(v, "%Y-%m-%d").date()
            elif t == "datetime":
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            return v
        except Exception as e:
            raise UserError(f"Invalid value for parameter '{self.name}': {e}")
