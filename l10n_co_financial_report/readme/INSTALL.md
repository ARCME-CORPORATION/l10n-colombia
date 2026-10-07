Add the 18.0 branches of these OCA repositories to the Odoo addons path:

- `l10n-colombia` (this module)
- `account-financial-reporting` (`account_financial_report`, `mis_template_financial_report`)
- `mis-builder` (`mis_builder`)
- `reporting-engine` (`report_xlsx`)
- `server-ux` (`date_range`)

Install their declared Python dependencies and then `l10n_co_financial_report`.
This module does not require Odoo Enterprise or `account_reports`.

Run Odoo integration tests in a disposable database with these addons installed:

```sh
odoo -d test_co_statements -i l10n_co_financial_report --test-enable --stop-after-init --test-tags /l10n_co_financial_report
```

For dependency-free arithmetic regression checks of the shipped formulas:

```sh
python l10n_co_financial_report/tests/test_formula_data.py
```

These checks substitute balances from an anonymous reference ledger; they do not
validate Odoo installation, ORM behavior, permissions or PDF/XLSX rendering.
