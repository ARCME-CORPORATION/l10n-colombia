# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast

from dateutil.relativedelta import relativedelta

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang


class FinancialReportWizard(models.TransientModel):
    _name = "l10n_co.financial.report.wizard"
    _description = "Colombian Financial Statements"
    _inherit = "account_financial_report_abstract_wizard"

    statement_type = fields.Selection(
        [
            ("bs", "Estado de Situación Financiera"),
            ("pl", "Estado de Resultado Integral"),
            ("equity", "Estado de Cambios en el Patrimonio"),
        ],
        required=True,
        default="bs",
        string="Estado financiero",
    )
    target_move = fields.Selection(
        [("posted", "Asientos publicados"), ("all", "Todos los asientos")],
        required=True,
        default="posted",
        string="Asientos",
    )

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

    @api.onchange("statement_type")
    def _onchange_statement_type(self):
        self.comparison = self.statement_type != "equity"

    def _get_kpi_domain(self, aep, kpi, start, end, component=None, visited=None):
        """Trace formula references; keep each accounting term's own date scope."""
        visited = set(visited or ())
        key = (kpi.name, component.name if component else None)
        if key in visited:
            return []
        visited.add(key)
        start = fields.Date.to_string(fields.Date.to_date(start))
        end = fields.Date.to_string(fields.Date.to_date(end))
        formula = (
            kpi._get_expression_str_for_subkpi(component)
            if component and kpi.multi
            else kpi.expression
        ) or "0"
        domains = [
            aep.get_aml_domain_for_expr(match.group(), start, end)
            for match in aep._ACC_RE.finditer(formula)
        ]
        tree = ast.parse(aep._ACC_RE.sub("0", formula), mode="eval")
        kpis = {item.name: item for item in kpi.report_id.kpi_ids}
        components = {item.name: item for item in kpi.report_id.subkpi_ids}
        references = set()
        attribute_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                attribute_names.add(id(node.value))
                if node.value.id in kpis and node.attr in components:
                    references.add((node.value.id, node.attr))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Name)
                and id(node) not in attribute_names
                and node.id in kpis
            ):
                references.add((node.id, component.name if component else None))
        for name, component_name in sorted(references, key=str):
            domain = self._get_kpi_domain(
                aep, kpis[name], start, end, components.get(component_name), visited
            )
            if domain:
                domains.append(domain)
        if not domains:
            return []
        return expression.AND(
            [
                expression.OR(domains),
                [("company_id", "=", self.company_id.id)],
                [
                    (
                        "parent_state",
                        "in",
                        ["posted"]
                        if self.target_move == "posted"
                        else ["draft", "posted"],
                    )
                ],
            ]
        )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id and self.date_to:
            self.date_from = self.company_id.compute_fiscalyear_dates(self.date_to)[
                "date_from"
            ]

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
        accounts = (
            self.env["account.account"]
            .with_company(self.company_id)
            .search(
                [
                    ("company_ids", "in", self.company_id.ids),
                    ("account_type", "!=", "off_balance"),
                    ("l10n_co_statement_category", "=", False),
                ]
            )
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

    def _validate_statement(self):
        self.ensure_one()
        self.check_access("read")
        if self.company_id not in self.env.companies:
            raise AccessError(self.env._("Select an allowed company."))
        self._check_dates()

    def _export(self, report_type):
        self._validate_statement()
        code = {"qweb-html": "html", "qweb-pdf": "pdf", "xlsx": "xlsx"}[report_type]
        action = self.env.ref(
            f"l10n_co_financial_report.action_{self.statement_type}_{code}"
        )
        return action.report_action(
            self, data=self._prepare_report_data(), config=False
        )

    def _get_statement_data(self):
        """One dataset shared by HTML, PDF and XLSX; no MIS widget/instance."""
        self._validate_statement()
        template = self.env.ref(
            f"l10n_co_financial_report.report_{self.statement_type}"
        ).with_company(self.company_id)
        periods = [(self.date_from, self.date_to)]
        if self.comparison:
            periods.append(
                (
                    self.date_from - relativedelta(years=1),
                    self.date_to - relativedelta(years=1),
                )
            )
        aep = template._prepare_aep(self.company_id)
        results = [
            template.evaluate(aep, start, end, target_move=self.target_move)
            for start, end in periods
        ]
        total_style = self.env.ref("mis_template_financial_report.style_header")
        components = template.subkpi_ids
        sections = []
        is_equity = self.statement_type == "equity"
        if is_equity:
            datasets = [
                ([result], [period])
                for result, period in zip(results, periods, strict=True)
            ]
        else:
            datasets = [(results, periods)]
        for values, dates in datasets:
            rows = []
            for kpi in template.kpi_ids:
                if is_equity:
                    amounts = [getattr(values[0][kpi.name], c.name) for c in components]
                else:
                    amounts = [result[kpi.name] for result in values]
                try:
                    amounts = [float(amount or 0) for amount in amounts]
                except (TypeError, ValueError) as error:
                    raise UserError(
                        self.env._("No se pudo calcular la línea %s.", kpi.description)
                    ) from error
                if is_equity:
                    domains = [
                        self._get_kpi_domain(aep, kpi, *dates[0], component=c)
                        for c in components
                    ]
                else:
                    domains = [
                        self._get_kpi_domain(aep, kpi, start, end)
                        for start, end in dates
                    ]
                contributing = [domain for domain in domains if domain]
                rows.append(
                    {
                        "name": kpi.description,
                        "code": kpi.name,
                        "amounts": amounts,
                        "domains": domains,
                        "domain": expression.OR(contributing) if contributing else [],
                        "formatted": [
                            formatLang(
                                self.env,
                                amount,
                                digits=self.company_id.currency_id.decimal_places,
                            )
                            for amount in amounts
                        ],
                        "header": kpi.name.endswith("_header"),
                        "total": kpi.style_id == total_style,
                        "check": (
                            kpi.name.endswith("_check") or kpi.name == "reconciliation"
                        ),
                    }
                )
            sections.append(
                {
                    "period": (
                        (
                            "Período seleccionado: "
                            if not sections
                            else "Comparativo del año anterior: "
                        )
                        + f"{dates[0][0]} / {dates[0][1]}"
                    )
                    if is_equity
                    else "",
                    "columns": [c.description for c in components]
                    if is_equity
                    else [str(end) for start, end in dates],
                    "rows": rows,
                }
            )
        return {
            "title": template.name,
            "company": self.company_id,
            "currency": self.company_id.currency_id,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "drafts": self.target_move == "all",
            "equity": is_equity,
            "sections": sections,
        }
