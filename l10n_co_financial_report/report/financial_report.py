# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.exceptions import UserError


class FinancialStatement(models.AbstractModel):
    _name = "report.l10n_co_financial_report.financial_statement"
    _description = "Colombian Financial Statement"

    def _get_report_values(self, docids, data=None):
        wizard_id = (data or {}).get("wizard_id")
        wizard = (
            self.env["l10n_co.financial.report.wizard"]
            .browse([wizard_id] if wizard_id else docids)
            .exists()
        )
        if len(wizard) != 1:
            raise UserError(self.env._("Abra de nuevo el asistente del informe."))
        return {
            "doc_ids": wizard.ids,
            "doc_model": wizard._name,
            "docs": wizard,
            "statement": wizard._get_statement_data(),
        }


class SituationStatement(models.AbstractModel):
    _name = "report.l10n_co_financial_report.statement_bs"
    _inherit = "report.l10n_co_financial_report.financial_statement"
    _description = "Colombian Statement of Financial Position"


class IncomeStatement(models.AbstractModel):
    _name = "report.l10n_co_financial_report.statement_pl"
    _inherit = "report.l10n_co_financial_report.financial_statement"
    _description = "Colombian Statement of Comprehensive Income"


class EquityStatement(models.AbstractModel):
    _name = "report.l10n_co_financial_report.statement_equity"
    _inherit = "report.l10n_co_financial_report.financial_statement"
    _description = "Colombian Statement of Changes in Equity"
