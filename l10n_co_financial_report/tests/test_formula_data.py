# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Run directly without Odoo: python tests/test_formula_data.py.

Checks the shipped XML against a balanced reference ledger. This small adapter
supplies balances to formulas; it does not replace integration tests of OCA's ORM.
"""

import ast
import re
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

if __package__:
    from .statement_fixture import CHART, OPENING, OPERATIONS
else:
    from statement_fixture import CHART, OPENING, OPERATIONS

ROOT = Path(__file__).resolve().parents[1]
BALANCE = re.compile(r"\bbal([ipeu])\s*(\[.*?\])\s*(\[.*?\])?")


def matches(domain, values):
    tokens = iter(domain)

    def consume(token):
        if token == "|":
            left, right = consume(next(tokens)), consume(next(tokens))
            return left or right
        if token == "&":
            left, right = consume(next(tokens)), consume(next(tokens))
            return left and right
        if token == "!":
            return not consume(next(tokens))
        field, operator, expected = token
        actual = values.get(field, False)
        if operator == "=":
            return actual == expected
        if operator == "!=":
            return actual != expected
        if operator == "in":
            return actual in expected
        if operator == "like":
            return actual.startswith(expected.rstrip("%"))
        raise AssertionError(operator)

    # Odoo combines trailing expressions with an implicit AND.
    results = [consume(token) for token in tokens]
    return all(results)


class ReferenceLedger:
    def __init__(self):
        self.lines = []
        for account, amount in OPENING.items():
            self.add(account, amount, date(2024, 12, 31))
        for debit, credit, amount in OPERATIONS:
            self.move(debit, credit, amount)

    def add(self, account, amount, when, movement="other", company=1, posted=True):
        account_type, category = CHART[account]
        self.lines.append(
            {
                "account_type": account_type,
                "l10n_co_statement_category": category,
                "move_id.l10n_co_equity_movement": movement,
                "date": when,
                "amount": amount,
                "company": company,
                "posted": posted,
            }
        )

    def move(self, debit, credit, amount, when=date(2025, 6, 30), **kwargs):
        self.add(debit, amount, when, **kwargs)
        self.add(credit, -amount, when, **kwargs)

    def evaluate(self, report, start=date(2025, 1, 1), end=date(2025, 12, 31)):
        records = [
            record
            for filename in ("financial_report.xml", "equity_report.xml")
            for record in ET.parse(ROOT / "data" / filename).findall("record")
        ]
        expressions = {}
        for record in records:
            if record.get("model") != "mis.report.kpi.expression":
                continue
            kpi = record.find("field[@name='kpi_id']").get("ref")
            component = record.find("field[@name='subkpi_id']").get("ref")
            name = component.removeprefix("equity_component_")
            expressions.setdefault(kpi, {})[name] = record.find(
                "field[@name='name']"
            ).text
        kpis = [
            record
            for record in records
            if record.get("model") == "mis.report.kpi"
            and record.find("field[@name='report_id']").get("ref") == "report_" + report
        ]
        kpis.sort(key=lambda r: int(r.find("field[@name='sequence']").text))
        values = {}

        def replace(match):
            mode, accounts, lines = match.groups()
            account_domain = ast.literal_eval(accounts)
            line_domain = ast.literal_eval(lines or "[]")
            fiscal_start = date(start.year, 1, 1)
            amount = 0
            for line in self.lines:
                if not line["posted"] or line["company"] != 1:
                    continue
                if not matches(account_domain, line) or not matches(line_domain, line):
                    continue
                is_pl = line["account_type"].split("_")[0] in ("income", "expense")
                when = line["date"]
                if mode == "p":
                    include = start <= when <= end
                elif mode == "u":
                    include = is_pl and when < fiscal_start
                else:
                    include = when < start if mode == "i" else when <= end
                    include = include and (not is_pl or when >= fiscal_start)
                if include:
                    amount += line["amount"]
            return str(amount)

        def evaluate(expression):
            return eval(BALANCE.sub(replace, expression), {"__builtins__": {}}, values)

        # Evaluate a whole multi-KPI atomically, just as MIS Builder does. This
        # detects self references in total columns as well as missing KPI names.
        for kpi in kpis:
            name = kpi.find("field[@name='name']").text
            if kpi.get("id") in expressions:
                values[name] = SimpleNamespace(
                    **{c: evaluate(e) for c, e in expressions[kpi.get("id")].items()}
                )
            else:
                values[name] = evaluate(kpi.find("field[@name='expression']").text)
        return values


class TestFormulaData(unittest.TestCase):
    def setUp(self):
        self.ledger = ReferenceLedger()

    def assert_reconciles(self, start=date(2025, 1, 1)):
        balance = self.ledger.evaluate("bs", start)
        equity = self.ledger.evaluate("equity", start)
        self.assertEqual(balance["balance_check"], 0)
        self.assertEqual(equity["ending"].total, balance["equity"])
        self.assertTrue(all(v == 0 for v in vars(equity["reconciliation"]).values()))

    def test_reference_financial_position(self):
        result = self.ledger.evaluate("bs")
        self.assertEqual(result["assets"], 320730000)
        self.assertEqual(result["liabilities"], 142366000)
        self.assertEqual(result["equity"], 178364000)
        self.assert_reconciles()

    def test_reference_comprehensive_income(self):
        result = self.ledger.evaluate("pl")
        self.assertEqual(result["gross_profit"], 152129000)
        self.assertEqual(result["profit_before_tax"], 20904000)
        self.assertEqual(result["profit"], 13588000)
        self.assertEqual(result["comprehensive_income"], 13588000)
        self.assertEqual(result["profit_check"], 0)

    def test_dividends_and_transfers(self):
        self.ledger.move("retained", "cash", 2000000, movement="distribution")
        self.ledger.move("retained", "reserves", 1000000, movement="transfer")
        result = self.ledger.evaluate("equity")
        self.assertEqual(result["distribution"].total, -2000000)
        self.assertEqual(result["transfer"].total, 0)
        self.assert_reconciles()

    def test_other_comprehensive_income(self):
        self.ledger.move("ppe", "oci", 3000000)
        self.assertEqual(self.ledger.evaluate("pl")["comprehensive_income"], 16588000)
        self.assertEqual(self.ledger.evaluate("equity")["oci"].oci, 3000000)
        self.assert_reconciles()

    def test_assignment_to_unaffected_not_counted_twice(self):
        self.ledger.move("unaffected", "retained", 13588000, movement="transfer")
        self.assertEqual(self.ledger.evaluate("bs")["result"], 0)
        self.assert_reconciles()

    def test_formal_income_closing(self):
        for debit, credit, amount in OPERATIONS:
            self.ledger.move(credit, debit, amount, movement="closing")
        self.ledger.move("cash", "retained", 13588000, movement="closing")
        self.assertEqual(self.ledger.evaluate("pl")["profit"], 13588000)
        self.assertEqual(self.ledger.evaluate("bs")["result"], 0)
        self.assert_reconciles()

    def test_prior_unclosed_earnings(self):
        self.ledger.move("cash", "revenue", 9000000, when=date(2024, 9, 1))
        self.assertEqual(self.ledger.evaluate("bs")["retained"], 20091000)
        self.assert_reconciles()

    def test_partial_year_carries_earlier_months(self):
        self.ledger.move("cash", "revenue", 1000000, when=date(2025, 2, 1))
        start = date(2025, 4, 1)
        self.assertEqual(self.ledger.evaluate("bs", start)["retained"], 12091000)
        self.assert_reconciles(start)

    def test_corrections_and_contributions(self):
        self.ledger.move("cash", "capital", 500000, movement="contribution")
        self.ledger.move("cash", "retained", 100000, movement="correction")
        result = self.ledger.evaluate("equity")
        self.assertEqual(result["contribution"].capital, 500000)
        self.assertEqual(result["correction"].retained, 100000)
        self.assert_reconciles()

    def test_draft_and_other_company_excluded(self):
        self.ledger.move("cash", "revenue", 999999, company=2)
        self.ledger.move("cash", "revenue", 999999, posted=False)
        self.assertEqual(self.ledger.evaluate("pl")["profit"], 13588000)
        self.assert_reconciles()

    def test_empty_ledger(self):
        self.ledger.lines = []
        self.assertEqual(self.ledger.evaluate("pl")["comprehensive_income"], 0)
        self.assert_reconciles()

    def test_unclassified_accounts_still_included(self):
        self.ledger.move("cash", "capital", 400000)
        for line in self.ledger.lines[-2:]:
            line["l10n_co_statement_category"] = False
        self.assertEqual(self.ledger.evaluate("bs")["unclassified_assets"], 400000)
        self.assertEqual(self.ledger.evaluate("bs")["unclassified_equity"], 400000)
        self.assert_reconciles()


if __name__ == "__main__":
    unittest.main()
