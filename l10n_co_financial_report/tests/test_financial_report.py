# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from .statement_fixture import CHART, OPENING, OPERATIONS


class TestFinancialReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Financial statement test",
                "currency_id": cls.env.ref("base.COP").id,
            }
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Statements",
                "code": "COST",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.accounts = {}
        for number, (name, (account_type, category)) in enumerate(CHART.items()):
            cls.accounts[name] = cls.env["account.account"].create(
                {
                    "name": name,
                    "code": f"CO{number:04d}",
                    "company_ids": [Command.set(cls.company.ids)],
                    "account_type": account_type,
                    "l10n_co_statement_category": category,
                }
            )
        cls._entry(list(OPENING.items()), date(2024, 12, 31))
        for debit, credit, amount in OPERATIONS:
            cls._entry([(debit, amount), (credit, -amount)])

    @classmethod
    def _entry(cls, amounts, when=date(2025, 6, 30), movement="other", posted=True):
        move = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "date": when,
                "l10n_co_equity_movement": movement,
                "line_ids": [
                    Command.create(
                        {
                            "name": name,
                            "account_id": cls.accounts[name].id,
                            "debit": max(amount, 0),
                            "credit": max(-amount, 0),
                        }
                    )
                    for name, amount in amounts
                ],
            }
        )
        if posted:
            move.action_post()
        return move

    def _evaluate(self, code, start=date(2025, 1, 1)):
        template = self.env.ref(f"l10n_co_financial_report.report_{code}")
        aep = template._prepare_aep(self.company)
        return template.evaluate(aep, start, date(2025, 12, 31))

    def _assert_reconciles(self, start=date(2025, 1, 1)):
        balance = self._evaluate("bs", start)
        equity = self._evaluate("equity", start)
        self.assertEqual(balance["balance_check"], 0)
        self.assertEqual(equity["ending"].total, balance["equity"])
        self.assertTrue(all(value == 0 for value in equity["reconciliation"]))

    def test_reference_totals(self):
        balance = self._evaluate("bs")
        result = self._evaluate("pl")
        self.assertEqual(balance["assets"], 320730000)
        self.assertEqual(balance["equity"], 178364000)
        self.assertEqual(result["gross_profit"], 152129000)
        self.assertEqual(result["profit_before_tax"], 20904000)
        self.assertEqual(result["profit"], 13588000)
        self._assert_reconciles()

    def test_dividends_transfers_and_oci(self):
        self._entry(
            [("retained", 2000000), ("cash", -2000000)], movement="distribution"
        )
        self._entry(
            [("retained", 1000000), ("reserves", -1000000)], movement="transfer"
        )
        self._entry([("ppe", 3000000), ("oci", -3000000)])
        equity = self._evaluate("equity")
        self.assertEqual(equity["distribution"].total, -2000000)
        self.assertEqual(equity["transfer"].total, 0)
        self.assertEqual(self._evaluate("pl")["comprehensive_income"], 16588000)
        self._assert_reconciles()

    def test_result_assignment(self):
        self._entry(
            [("unaffected", 13588000), ("retained", -13588000)], movement="transfer"
        )
        self.assertEqual(self._evaluate("bs")["result"], 0)
        self._assert_reconciles()

    def test_closing_does_not_cancel_income_statement(self):
        for debit, credit, amount in OPERATIONS:
            self._entry([(credit, amount), (debit, -amount)], movement="closing")
        self._entry([("cash", 13588000), ("retained", -13588000)], movement="closing")
        self.assertEqual(self._evaluate("pl")["profit"], 13588000)
        self.assertEqual(self._evaluate("bs")["result"], 0)
        self._assert_reconciles()

    def test_prior_and_partial_year_results(self):
        self._entry([("cash", 9000000), ("revenue", -9000000)], date(2024, 9, 1))
        self._entry([("cash", 1000000), ("revenue", -1000000)], date(2025, 2, 1))
        start = date(2025, 4, 1)
        self.assertEqual(self._evaluate("bs", start)["retained"], 21091000)
        self._assert_reconciles(start)

    def test_draft_and_other_company(self):
        self._entry([("cash", 999999), ("revenue", -999999)], posted=False)
        other = self.env["res.company"].create(
            {
                "name": "Other statements company",
                "currency_id": self.company.currency_id.id,
            }
        )
        other_env = self.env(
            context=dict(self.env.context, allowed_company_ids=other.ids)
        )
        accounts = other_env["account.account"].create(
            [
                {
                    "name": "Cash",
                    "code": "OTHER1",
                    "account_type": "asset_cash",
                    "company_ids": [Command.set(other.ids)],
                },
                {
                    "name": "Income",
                    "code": "OTHER2",
                    "account_type": "income",
                    "company_ids": [Command.set(other.ids)],
                },
            ]
        )
        journal = other_env["account.journal"].create(
            {"name": "Other", "code": "OTCO", "type": "general", "company_id": other.id}
        )
        other_env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": date(2025, 6, 30),
                "line_ids": [
                    Command.create({"account_id": accounts[0].id, "debit": 999999}),
                    Command.create({"account_id": accounts[1].id, "credit": 999999}),
                ],
            }
        ).action_post()
        self.assertEqual(self._evaluate("pl")["profit"], 13588000)
        self._assert_reconciles()

    def test_account_category_validation(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.accounts["cash"].l10n_co_statement_category = "revenue"

    def test_wizard_creates_comparative_instances(self):
        wizard = self.env["l10n_co.financial.report.wizard"].create(
            {
                "company_id": self.company.id,
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
            }
        )
        action = wizard.action_create_reports()
        instances = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(len(instances), 3)
        for instance in instances:
            self.assertEqual(instance.company_id, self.company)
            self.assertEqual(instance.target_move, "posted")
            self.assertEqual(len(instance.period_ids), 2)
            self.assertEqual(instance.period_ids[0].date_from, date(2025, 1, 1))
            self.assertEqual(instance.period_ids[1].date_to, date(2024, 12, 31))
            instance.compute()

    def test_wizard_dates_and_unclassified_accounts(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["l10n_co.financial.report.wizard"].create(
                {"date_from": "2025-12-31", "date_to": "2025-01-01"}
            )
        self.accounts["cash"].l10n_co_statement_category = False
        wizard = self.env["l10n_co.financial.report.wizard"].create(
            {"date_from": "2025-01-01", "date_to": "2025-12-31"}
        )
        with self.assertRaises(ValidationError):
            wizard.action_create_reports()

    def test_native_report_buttons_and_data(self):
        for code in ("bs", "pl", "equity"):
            wizard = self.env["l10n_co.financial.report.wizard"].create(
                {
                    "company_id": self.company.id,
                    "statement_type": code,
                    "date_from": "2025-01-01",
                    "date_to": "2025-12-31",
                }
            )
            statement = wizard._get_statement_data()
            self.assertEqual(statement["company"], self.company)
            self.assertEqual(len(statement["sections"]), 2 if code == "equity" else 1)
            for method, report_type in (
                ("button_export_html", "qweb-html"),
                ("button_export_pdf", "qweb-pdf"),
                ("button_export_xlsx", "xlsx"),
            ):
                action = getattr(wizard, method)()
                self.assertEqual(action["type"], "ir.actions.report")
                self.assertEqual(action["report_type"], report_type)
                self.assertEqual(action["data"]["wizard_id"], wizard.id)

    def test_native_html_and_xlsx_rendering(self):
        from io import BytesIO
        from zipfile import ZipFile

        for code in ("bs", "pl", "equity"):
            wizard = self.env["l10n_co.financial.report.wizard"].create(
                {
                    "company_id": self.company.id,
                    "statement_type": code,
                    "date_from": "2025-01-01",
                    "date_to": "2025-12-31",
                }
            )
            data = wizard._prepare_report_data()
            service = self.env["ir.actions.report"]
            html, _ = service._render_qweb_html(
                f"l10n_co_financial_report.action_{code}_html", wizard.ids, data=data
            )
            self.assertIn(b"data_table", html)
            self.assertIn(b'res-model="account.move.line"', html)
            self.assertNotIn(b"mis_report_widget", html)
            xlsx, _ = service._render_xlsx(
                f"l10n_co_financial_report.action_{code}_xlsx", wizard.ids, data=data
            )
            with ZipFile(BytesIO(xlsx)) as workbook:
                self.assertIn("xl/workbook.xml", workbook.namelist())

    def test_each_report_has_a_menu(self):
        parent = self.env.ref("l10n_co_financial_report.financial_report_menu")
        self.assertFalse(parent.action)
        for code in ("bs", "pl", "equity"):
            menu = self.env.ref(f"l10n_co_financial_report.menu_{code}")
            self.assertEqual(menu.parent_id, parent)
            self.assertEqual(menu.action.res_model, "l10n_co.financial.report.wizard")

    def test_equity_menu_defaults_to_one_period(self):
        from odoo.tools.safe_eval import safe_eval

        action = self.env.ref("l10n_co_financial_report.wizard_action_equity")
        wizard = (
            self.env["l10n_co.financial.report.wizard"]
            .with_context(**safe_eval(action.context))
            .create({"date_from": "2025-01-01", "date_to": "2025-12-31"})
        )
        self.assertFalse(wizard.comparison)
        self.assertEqual(len(wizard._get_statement_data()["sections"]), 1)
        wizard.comparison = True
        sections = wizard._get_statement_data()["sections"]
        self.assertEqual(len(sections), 2)
        self.assertIn("Comparativo del año anterior", sections[1]["period"])

    def test_drilldown_scopes_and_aggregates(self):
        self._entry([("cash", 999999), ("revenue", -999999)], posted=False)
        wizard = self.env["l10n_co.financial.report.wizard"].create(
            {"statement_type": "pl", "date_from": "2025-01-01", "date_to": "2025-12-31"}
        )
        rows = {
            row["code"]: row
            for row in wizard._get_statement_data()["sections"][0]["rows"]
        }
        revenue = self.env["account.move.line"].search(rows["revenue"]["domains"][0])
        self.assertTrue(revenue)
        self.assertEqual(revenue.account_id, self.accounts["revenue"])
        self.assertEqual(-sum(revenue.mapped("balance")), rows["revenue"]["amounts"][0])
        self.assertTrue(all(line.parent_state == "posted" for line in revenue))
        self.assertTrue(all(line.company_id == self.company for line in revenue))
        self.assertTrue(
            all(date(2025, 1, 1) <= line.date <= date(2025, 12, 31) for line in revenue)
        )
        previous = self.env["account.move.line"].search(rows["revenue"]["domains"][1])
        self.assertFalse(previous)
        profit = self.env["account.move.line"].search(rows["profit"]["domains"][0])
        self.assertEqual(-sum(profit.mapped("balance")), rows["profit"]["amounts"][0])
        wizard.target_move = "all"
        rows = {
            row["code"]: row
            for row in wizard._get_statement_data()["sections"][0]["rows"]
        }
        all_revenue = self.env["account.move.line"].search(
            rows["revenue"]["domains"][0]
        )
        self.assertGreater(len(all_revenue), len(revenue))

    def test_equity_drilldown_by_component_and_movement(self):
        self._entry([("cash", 500000), ("capital", -500000)], movement="contribution")
        wizard = self.env["l10n_co.financial.report.wizard"].create(
            {
                "statement_type": "equity",
                "comparison": False,
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
            }
        )
        rows = {
            row["code"]: row
            for row in wizard._get_statement_data()["sections"][0]["rows"]
        }
        template = self.env.ref("l10n_co_financial_report.report_equity")
        index = template.subkpi_ids.mapped("name").index("capital")
        lines = self.env["account.move.line"].search(
            rows["contribution"]["domains"][index]
        )
        self.assertEqual(-sum(lines.mapped("balance")), 500000)
        self.assertEqual(lines.account_id, self.accounts["capital"])
        self.assertTrue(
            all(
                line.move_id.l10n_co_equity_movement == "contribution" for line in lines
            )
        )
        opening = self.env["account.move.line"].search(
            rows["opening"]["domains"][index]
        )
        self.assertTrue(all(line.date < date(2025, 1, 1) for line in opening))
