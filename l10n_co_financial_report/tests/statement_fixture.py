# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Anonymous accounting fixture, amounts in COP."""

CHART = {
    "cash": ("asset_cash", "cash"),
    "receivables": ("asset_receivable", "trade_receivables"),
    "other_receivables": ("asset_current", "other_receivables"),
    "inventory": ("asset_current", "inventory"),
    "ppe": ("asset_fixed", "ppe"),
    "payables": ("liability_payable", "trade_payables"),
    "capital": ("equity", "capital"),
    "capitalization": ("equity", "capitalization"),
    "reserves": ("equity", "reserves"),
    "retained": ("equity", "retained"),
    "unaffected": ("equity_unaffected", "retained"),
    "oci": ("equity", "oci_non_reclassifiable"),
    "revenue": ("income", "revenue"),
    "other_income": ("income_other", "other_income"),
    "cost": ("expense_direct_cost", "cost_of_sales"),
    "selling": ("expense", "selling_expenses"),
    "admin": ("expense", "administrative_expenses"),
    "finance": ("expense", "finance_costs"),
    "tax": ("expense", "income_tax"),
}
OPENING = {
    "cash": 2706000,
    "receivables": 85028000,
    "other_receivables": 13560000,
    "inventory": 75500000,
    "ppe": 130348000,
    "payables": -142366000,
    "capital": -5000000,
    "capitalization": -143685000,
    "reserves": -5000000,
    "retained": -11091000,
}
# Debit account, credit account, amount.
OPERATIONS = [
    ("cash", "revenue", 751663000),
    ("cash", "other_income", 280000),
    ("cost", "cash", 599534000),
    ("selling", "cash", 101000000),
    ("admin", "cash", 19580000),
    ("finance", "cash", 10925000),
    ("tax", "cash", 7316000),
]
