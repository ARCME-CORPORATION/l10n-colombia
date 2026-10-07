# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Estados financieros",
    "summary": "Situación financiera, resultado integral y cambios en el patrimonio",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting/Localizations",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Juan Arcos, Odoo Community Association (OCA)",
    "maintainers": ["juanparmer"],
    "license": "AGPL-3",
    "depends": ["l10n_co", "mis_template_financial_report"],
    "data": [
        "security/ir.model.access.csv",
        "data/financial_report.xml",
        "data/equity_report.xml",
        "views/account_account_views.xml",
        "views/account_move_views.xml",
        "wizard/financial_report_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
