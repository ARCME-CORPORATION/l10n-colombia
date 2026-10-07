# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class FinancialReportWizard(models.TransientModel):
    _name = "l10n_co.financial.report.wizard"
    _description = "Colombian Financial Statements"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    date_from = fields.Date(
        required=True,
        default=lambda self: self.env.company.compute_fiscalyear_dates(
            fields.Date.context_today(self)
        )["date_from"],
    )
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    comparison = fields.Boolean(string="Compare with previous year", default=True)

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id and self.date_to:
            self.date_from = self.company_id.compute_fiscalyear_dates(
                self.date_to
            )["date_from"]

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise ValidationError(
                    self.env._("The end date precedes the start date.")
                )

    def action_create_reports(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise AccessError(self.env._("Select an allowed company."))
        accounts = self.env["account.account"].with_company(self.company_id).search(
            [
                ("company_ids", "in", self.company_id.ids),
                ("account_type", "!=", "off_balance"),
                ("l10n_co_statement_category", "=", False),
            ]
        )
        if accounts:
            raise ValidationError(
                self.env._(
                    "Classify these accounts before creating statements: %s",
                    ", ".join(accounts.mapped("display_name")),
                )
            )
        periods = [(self.date_from, self.date_to)]
        if self.comparison:
            periods.append(
                (
                    self.date_from - relativedelta(years=1),
                    self.date_to - relativedelta(years=1),
                )
            )
        instances = self.env["mis.report.instance"]
        for report_code in ("bs", "pl", "equity"):
            report = self.env.ref(f"l10n_co_financial_report.report_{report_code}")
            instances |= instances.create(
                {
                    "name": f"{report.name} - {self.company_id.name} - {self.date_to}",
                    "report_id": report.id,
                    "company_id": self.company_id.id,
                    "currency_id": self.company_id.currency_id.id,
                    "target_move": "posted",
                    "landscape_pdf": report_code == "equity",
                    "display_columns_description": True,
                    "period_ids": [
                        Command.create(
                            {
                                "name": str(date_to.year),
                                "mode": "fix",
                                "source": "actuals",
                                "manual_date_from": date_from,
                                "manual_date_to": date_to,
                                "sequence": sequence,
                            }
                        )
                        for sequence, (date_from, date_to) in enumerate(periods)
                    ],
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Colombian Financial Statements"),
            "res_model": "mis.report.instance",
            "view_mode": "list,form",
            "domain": [("id", "in", instances.ids)],
        }
