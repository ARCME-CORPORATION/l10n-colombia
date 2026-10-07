# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api

LABELS = {
    "bs_capitalization": "Capitalización",
    "bs_transition": "Ajustes de adopción NIIF",
    "bs_retained": "Ganancias o pérdidas acumuladas",
    "pl_selling_expenses": "Gastos de ventas y distribución",
    "pl_administrative_expenses": "Gastos de administración",
    "pl_oci_reclassifiable": "ORI susceptible de reclasificación (neto de impuestos)",
    "pl_oci_non_reclassifiable": (
        "ORI no susceptible de reclasificación (neto de impuestos)"
    ),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Repair only the original incorrectly encoded noupdate labels. Preserve
    # any labels that an accountant has customized since installation.
    for xml_id, label in LABELS.items():
        record = env.ref(f"l10n_co_financial_report.{xml_id}", raise_if_not_found=False)
        if record:
            original = label.encode("utf-8").decode("cp1252")
            if record.with_context(lang="en_US").description == original:
                record.with_context(lang="en_US").description = label
    menu = env.ref("l10n_co_financial_report.financial_report_menu")
    for lang in env["res.lang"].search([("code", "in", ["es_ES", "es_CO"])]):
        menu.update_field_translations("name", {lang.code: "Colombia"})
