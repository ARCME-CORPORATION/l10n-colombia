# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Template IDs from Odoo 18 l10n_co/data/template/account.tax-co.csv.
# Include the zero-rate ICA tax; exclude positive purchase counterparts.
WITHHOLDING_TAX_XMLIDS = {
    "rte_fte": tuple(f"l10n_co_tax_{n}" for n in (*range(16, 43), 53, 54)),
    "rte_iva": tuple(f"l10n_co_tax_{n}" for n in (12, 13, 55, 56)),
    "rte_ica": tuple(f"l10n_co_tax_{n}" for n in (*range(43, 49), 57, 58)),
}

ACCOUNT_MAPPINGS = {
    "236515": "135515",
    "236520": "135515",
    "236525": "135515",
    "236530": "135515",
    "236535": "135515",
    "236540": "135515",
    "236550": "135515",
    "236700": "135517",
    "236800": "135518",
}

# Cuenta de pasivo (tipo 23) equivalente a la de activo (tipo 13) usada
# por las retenciones de venta del módulo base l10n_co.
LIABILITY_ACCOUNT_CODE_MAP = {
    "135515": "236500",  # Withheld at source
    "135517": "236700",  # Sales tax withheld
    "135518": "236800",  # Industry and commerce tax withheld
}

RETE_NAME_PATTERN = "rte"

COUNTERPART_TAX_GROUP_NAME = "Retenciones (Contrapartida)"


def _l10n_co_withholding_post_init(env):
    _set_default_uvt_value(env)
    companies = env["res.company"].search([("chart_template", "=", "co")])
    for company in companies:
        _configure_chart_withholding_taxes(env, company)
        _setup_withholding_for_company(env, company)
        _create_sales_withholding_counterparts(env, company)


def _configure_chart_withholding_taxes(env, company):
    """Classify existing chart taxes without changing rates or accounts."""
    for wh_type, xmlids in WITHHOLDING_TAX_XMLIDS.items():
        for xmlid in xmlids:
            tax = _find_tax_by_xmlid(env, company, f"l10n_co.{xmlid}")
            if (
                tax
                and tax.type_tax_use in ("purchase", "sale")
                and tax.amount <= 0
                and not tax.l10n_co_withholding_counterpart
                and not tax.l10n_co_withholding_type
            ):
                tax.l10n_co_withholding_type = wh_type


def _get_purchase_withholding_taxes(env, company, wh_types):
    return (
        env["account.tax"]
        .with_context(active_test=False)
        .search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                ("amount", "<", 0),
                ("l10n_co_withholding_type", "in", wh_types),
                ("l10n_co_withholding_counterpart", "=", False),
            ]
        )
    )


def _get_sales_withholding_taxes(env, company):
    """Filtro de impuestos de retención de ventas.

    Impuestos cuyo nombre contiene "Rte" y son de tipo venta, con monto
    negativo (retención que reduce el total de la factura).
    """
    domain = [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", "sale"),
        ("amount", "<", 0),
    ]
    taxes = env["account.tax"].search(domain)
    return taxes.filtered(
        lambda t: RETE_NAME_PATTERN in (t.name or "").lower(),
    )


def _get_or_create_counterpart_tax_group(env, company):
    tax_group = env["account.tax.group"].search(
        [
            ("name", "=", COUNTERPART_TAX_GROUP_NAME),
            ("company_id", "=", company.id),
        ],
        limit=1,
    )
    if not tax_group:
        tax_group = env["account.tax.group"].create(
            {
                "name": COUNTERPART_TAX_GROUP_NAME,
                "company_id": company.id,
                "country_id": company.country_id.id,
                "l10n_co_withholding_counterpart": True,
            },
        )
    return tax_group


def _get_or_create_liability_account(env, company, asset_account):
    """Cuenta de pasivo (tipo 23) con el mismo nombre que la de activo (tipo 13)."""
    if not asset_account:
        return False
    asset_code = asset_account.with_company(company).code
    code = LIABILITY_ACCOUNT_CODE_MAP.get(asset_code, "2365" + asset_code[-3:])
    account_env = env["account.account"].with_company(company)
    liability_account = account_env.search(
        [("code_store", "=", code), ("company_ids", "in", [company.id])],
        limit=1,
    )
    if not liability_account:
        liability_account = account_env.create(
            {
                "code": code,
                "name": asset_account.name,
                "account_type": "liability_current",
                "company_ids": [(6, 0, [company.id])],
                "reconcile": True,
            },
        )
    return liability_account


def _get_or_create_positive_counterpart(
    env, company, wh_tax, tax_group, liability_account
):
    counterpart = env["account.tax"].search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "=", "sale"),
            ("l10n_co_withholding_compensates_tax_id", "=", wh_tax.id),
            ("l10n_co_withholding_counterpart", "=", True),
        ],
        limit=1,
    )
    if counterpart:
        if counterpart.tax_group_id != tax_group:
            counterpart.tax_group_id = tax_group.id
        if liability_account:
            for line in counterpart.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "tax" and not r.account_id,
            ):
                line.account_id = liability_account.id
            for line in counterpart.refund_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "tax" and not r.account_id,
            ):
                line.account_id = liability_account.id
        return counterpart
    vals = {
        "name": f"Compensación {wh_tax.name}",
        "amount": abs(wh_tax.amount),
        "amount_type": "percent",
        "type_tax_use": "sale",
        "tax_group_id": tax_group.id,
        "company_id": company.id,
        "l10n_co_withholding_type": wh_tax.l10n_co_withholding_type,
        "l10n_co_withholding_counterpart": True,
        "l10n_co_withholding_compensates_tax_id": wh_tax.id,
        "price_include_override": "tax_excluded",
    }
    if liability_account:
        repartition_vals = [
            (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
            (
                0,
                0,
                {
                    "repartition_type": "tax",
                    "factor_percent": 100.0,
                    "account_id": liability_account.id,
                },
            ),
        ]
        vals["invoice_repartition_line_ids"] = list(repartition_vals)
        vals["refund_repartition_line_ids"] = list(repartition_vals)
    return env["account.tax"].create(vals)


def _create_sales_withholding_counterparts(env, company):
    """Crea la contrapartida positiva de cada retención de venta.

    Al aplicar retención + contrapartida sobre una línea de venta, el neto
    sobre el subtotal queda en 0 y el total de la factura coincide con el
    total que se envía a la DIAN.
    """
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    company = company.with_company(company)
    sales_wh_taxes = _get_sales_withholding_taxes(env, company)
    if not sales_wh_taxes:
        return
    tax_group = _get_or_create_counterpart_tax_group(env, company)
    for wh_tax in sales_wh_taxes:
        asset_account = wh_tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax",
        )[:1].account_id
        liability_account = _get_or_create_liability_account(
            env,
            company,
            asset_account,
        )
        _get_or_create_positive_counterpart(
            env,
            company,
            wh_tax,
            tax_group,
            liability_account,
        )


def _set_default_uvt_value(env):
    param = env["ir.config_parameter"].sudo()
    if not param.get_param("l10n_co_withholding.uvt_value"):
        param.set_param("l10n_co_withholding.uvt_value", "52374")
        _logger.info("UVT value set to 52374 (2026)")


def _setup_withholding_for_company(env, company):
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    company = company.with_company(company)
    rte_fte_0 = _get_or_create_zero_tax(
        env,
        company,
        "RteFte 0%",
        "l10n_co.tax_group_r_ren_0",
        "rte_fte",
    )
    rte_iva_0 = _get_or_create_zero_tax(
        env,
        company,
        "RteIVA 0%",
        "l10n_co.tax_group_r_iva_075",
        "rte_iva",
    )
    rte_ica_0 = _find_tax_by_xmlid(env, company, "l10n_co.l10n_co_tax_43")
    if not rte_ica_0 or rte_ica_0.amount != 0 or rte_ica_0.type_tax_use != "purchase":
        rte_ica_0 = _get_or_create_zero_tax(
            env,
            company,
            "0% RteICA",
            "l10n_co.tax_group_r_ica_0",
            "rte_ica",
        )
    _create_fiscal_position_simple(env, company, rte_fte_0)
    _create_fiscal_position_non_taxpayer(env, company, rte_fte_0, rte_iva_0, rte_ica_0)


def _get_or_create_zero_tax(env, company, name, tax_group_xmlid, wh_type):
    existing = env["account.tax"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", name),
            ("amount", "=", 0.0),
        ],
        limit=1,
    )
    if existing:
        return existing
    tax_group = _find_chart_record(env, company, tax_group_xmlid)
    if not tax_group:
        raise UserError(
            _(
                "Missing withholding tax group %(xmlid)s for %(company)s.",
                xmlid=tax_group_xmlid,
                company=company.display_name,
            )
        )
    return env["account.tax"].create(
        {
            "name": name,
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": "purchase",
            "tax_group_id": tax_group.id if tax_group else False,
            "company_id": company.id,
            "l10n_co_withholding_type": wh_type,
            "price_include_override": "tax_excluded",
        },
    )


def _find_chart_record(env, company, xmlid):
    """Resolve Odoo 18 chart records in the requested company."""
    record = (
        env["account.chart.template"]
        .with_company(company)
        .ref(
            xmlid.split(".")[-1],
            raise_if_not_found=False,
        )
    )
    if not record:
        record = env.ref(xmlid, raise_if_not_found=False)
    return record if record and record.company_id == company else False


def _find_tax_by_xmlid(env, company, xmlid):
    return _find_chart_record(env, company, xmlid)


def _find_account_by_code(env, company, code):
    return (
        env["account.account"]
        .with_company(company)
        .search(
            [("code_store", "=", code), ("company_ids", "in", [company.id])],
            limit=1,
        )
    )


def _add_account_mappings(env, company, fp):
    for src_code, dest_code in ACCOUNT_MAPPINGS.items():
        src_account = _find_account_by_code(env, company, src_code)
        dest_account = _find_account_by_code(env, company, dest_code)
        if src_account and dest_account:
            existing = env["account.fiscal.position.account"].search(
                [
                    ("position_id", "=", fp.id),
                    ("account_src_id", "=", src_account.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.account"].create(
                    {
                        "position_id": fp.id,
                        "account_src_id": src_account.id,
                        "account_dest_id": dest_account.id,
                    },
                )


def _create_fiscal_position_simple(env, company, rte_fte_0):
    fp = env["account.fiscal.position"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", "Régimen Simple (Sin ReteFte)"),
        ],
        limit=1,
    )
    if not fp:
        fp = env["account.fiscal.position"].create(
            {
                "name": "Régimen Simple (Sin ReteFte)",
                "company_id": company.id,
            },
        )
    for src_tax in _get_purchase_withholding_taxes(env, company, ["rte_fte"]):
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_fte_0.id,
                    },
                )
    _add_account_mappings(env, company, fp)


def _create_fiscal_position_non_taxpayer(env, company, rte_fte_0, rte_iva_0, rte_ica_0):
    fp = env["account.fiscal.position"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", "No Contribuyente (Sin Retenciones)"),
        ],
        limit=1,
    )
    if not fp:
        fp = env["account.fiscal.position"].create(
            {
                "name": "No Contribuyente (Sin Retenciones)",
                "company_id": company.id,
            },
        )
    for src_tax in _get_purchase_withholding_taxes(env, company, ["rte_fte"]):
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_fte_0.id,
                    },
                )
    for src_tax in _get_purchase_withholding_taxes(env, company, ["rte_iva"]):
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_iva_0.id,
                    },
                )
    for src_tax in _get_purchase_withholding_taxes(env, company, ["rte_ica"]):
        if src_tax and rte_ica_0:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_ica_0.id,
                    },
                )
    _add_account_mappings(env, company, fp)
