Provides three Colombian financial statement templates for Odoo 18:

- Estado de Situación Financiera, with current/non-current assets and liabilities.
- Estado de Resultado Integral, including profit and other comprehensive income.
- Estado de Cambios en el Patrimonio, with opening balances, movements, closing balances and reconciliation for each equity component.

Uses OCA MIS Builder and `mis_template_financial_report` from
[account-financial-reporting](https://github.com/OCA/account-financial-reporting/tree/18.0/mis_template_financial_report).
HTML/PDF presentation follows Account Financial Reports and Excel uses OCA
`report_xlsx`. Financial formulas and period comparisons use MIS Builder on the
server; report screens do not use its Owl widget.
The module follows the directory and manifest conventions of the OCA
[maintainer-tools module template](https://github.com/OCA/maintainer-tools/tree/master/template/module).

The templates are a configurable starting point for individual statements. They
are not a complete set of statutory statements: cash flows, notes, consolidation,
signatures and an assertion of NIIF compliance are outside the scope.
