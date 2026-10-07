# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Each category belongs to exactly one accounting family. Codes are deliberately
# not used: companies can adapt their chart without changing report expressions.
CATEGORIES = {
    "asset": [
        ("cash", "Efectivo y equivalentes de efectivo"),
        ("investments_current", "Inversiones corrientes"),
        ("trade_receivables", "Deudores comerciales"),
        ("shareholder_receivables", "Cuentas por cobrar a socios"),
        ("tax_receivables", "Impuestos por cobrar"),
        ("employee_receivables", "Cuentas por cobrar a trabajadores"),
        ("other_receivables", "Otros deudores"),
        ("inventory", "Inventarios"),
        ("prepayments", "Pagos anticipados"),
        ("other_current_assets", "Otros activos corrientes"),
        ("leased_ppe", "Propiedades, planta y equipo en arrendamiento"),
        ("ppe", "Propiedades, planta y equipo"),
        ("intangibles", "Intangibles"),
        ("deferred_tax_assets", "Activos por impuesto diferido"),
        ("other_noncurrent_assets", "Otros activos no corrientes"),
    ],
    "liability": [
        ("borrowings_current", "Obligaciones financieras corrientes"),
        ("trade_payables", "Proveedores"),
        ("other_current_liabilities", "Otras cuentas por pagar corrientes"),
        ("shareholder_payables", "Cuentas por pagar a socios"),
        ("tax_payables", "Impuestos corrientes por pagar"),
        ("employee_benefits", "Beneficios a empleados corrientes"),
        ("borrowings_noncurrent", "Obligaciones financieras no corrientes"),
        ("provisions_noncurrent", "Provisiones no corrientes"),
        ("advances_noncurrent", "Anticipos recibidos no corrientes"),
        ("deferred_tax_liabilities", "Pasivos por impuesto diferido"),
        ("other_noncurrent_liabilities", "Otros pasivos no corrientes"),
    ],
    "equity": [
        ("capital", "Capital social"),
        ("capitalization", "Capitalización"),
        ("reserves", "Reservas"),
        ("transition", "Ajustes de adopción NIIF"),
        ("retained", "Ganancias o pérdidas acumuladas"),
        ("oci_reclassifiable", "ORI susceptible de reclasificación"),
        ("oci_non_reclassifiable", "ORI no susceptible de reclasificación"),
        ("other_equity", "Otros componentes del patrimonio"),
    ],
    "income": [
        ("revenue", "Ingresos de actividades ordinarias"),
        ("other_income", "Otros ingresos"),
    ],
    "expense": [
        ("cost_of_sales", "Costo de ventas"),
        ("selling_expenses", "Gastos de ventas y distribución"),
        ("administrative_expenses", "Gastos de administración"),
        ("finance_costs", "Gastos financieros"),
        ("other_expenses", "Otros gastos"),
        ("income_tax", "Gasto por impuesto a las ganancias"),
    ],
}
DEFAULT_CATEGORIES = {
    "asset_cash": "cash",
    "asset_receivable": "trade_receivables",
    "asset_current": "other_current_assets",
    "asset_non_current": "other_noncurrent_assets",
    "asset_prepayments": "prepayments",
    "asset_fixed": "ppe",
    "liability_payable": "trade_payables",
    "liability_credit_card": "borrowings_current",
    "liability_current": "other_current_liabilities",
    "liability_non_current": "other_noncurrent_liabilities",
    "equity": "other_equity",
    "equity_unaffected": "retained",
    "income": "revenue",
    "income_other": "other_income",
    "expense": "other_expenses",
    "expense_depreciation": "other_expenses",
    "expense_direct_cost": "cost_of_sales",
}


class AccountAccount(models.Model):
    _inherit = "account.account"

    l10n_co_statement_category = fields.Selection(
        selection=[item for items in CATEGORIES.values() for item in items],
        string="Colombian financial statement category",
        compute="_compute_l10n_co_statement_category",
        store=True,
        readonly=False,
        precompute=True,
        help="Review the default classification before issuing statements. "
        "Changing the account type resets this category. Shared accounts use "
        "the same category in every company.",
    )

    @api.depends("account_type")
    def _compute_l10n_co_statement_category(self):
        for account in self:
            account.l10n_co_statement_category = DEFAULT_CATEGORIES.get(
                account.account_type, False
            )

    @api.constrains("account_type", "l10n_co_statement_category")
    def _check_l10n_co_statement_category(self):
        for account in self:
            category = account.l10n_co_statement_category
            if not category:
                continue
            family = account.account_type.split("_")[0]
            allowed = dict(CATEGORIES.get(family, []))
            if category not in allowed:
                raise ValidationError(
                    self.env._(
                        "The financial statement category does not match "
                        "the accounting type of account %s.",
                        account.display_name,
                    )
                )
