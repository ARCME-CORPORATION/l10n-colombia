# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_co_equity_movement = fields.Selection(
        selection=[
            ("contribution", "Aportes de propietarios"),
            ("distribution", "Dividendos y retiros de utilidades"),
            ("transfer", "Transferencias entre componentes del patrimonio"),
            ("correction", "Correcciones y cambios de políticas contables"),
            ("closing", "Cierre de resultados"),
            ("other", "Otros movimientos"),
        ],
        string="Colombian equity movement",
        default="other",
        required=True,
        copy=True,
        help="Classifies equity lines in this entry. Mark result-closing entries "
        "as Closing so they do not cancel income and expenses in the income "
        "statement. Other comprehensive income is identified by account category.",
    )
