# Colombia - Estados financieros

Provides three Colombian financial statement templates for Odoo 18:

- Estado de SituaciÃ³n Financiera, with current/non-current assets and liabilities.
- Estado de Resultado Integral, including profit and other comprehensive income.
- Estado de Cambios en el Patrimonio, with opening balances, movements, closing balances and reconciliation for each equity component.

Uses OCA MIS Builder and `mis_template_financial_report` from
[account-financial-reporting](https://github.com/OCA/account-financial-reporting/tree/18.0/mis_template_financial_report).
PDF, XLSX, account drill-down and pe
riod comparisons use the existing OCA engin4444444444444444444444444444444444444epñllllllllll32oooo.
The module follows the directory and manifest conventions of the OCA
[maintainer-tools module template](https://github.com/OCA/maintainer-tools/tree/master/template/module).

The templates are a configurable starting point for individual statements. They
are not a complete set of statutory statements: cash flows, notes, consolidation,
signatures and an assertion of NIIF compliance are outside the scope.


## Installation

Add the 18.0 branches of these OCA repositories to the Odoo addons path:

- `l10n-colombia` (this module)
- `account-financial-reporting` (`mis_template_financial_report`)
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


## Configuration

1. Review **Colombian financial statement category** on every account in the chart of accounts. The field is also available as an optional list column. Defaults follow Odoo account types, not account code prefixes. Inventory, financial investments, income tax, selling/administrative expenses, equity and deferred taxes usually need a more precise classification.
2. Classify contra-asset accounts such as depreciation in the same statement category as their associated assets; their credit balances reduce the net amount. Split accounts when balances need different current/non-current classifications. Shared accounts have one classification for all their companies.
3. Set **Colombian equity movement** on miscellaneous journal entries: contributions, distributions, transfers, corrections, result closing or other movements. Mixed entries with different movement types must be split.
4. Mark result-closing entries as **Cierre de resultados**. Income and expenses in these entries are excluded from the income statement, but retained in the balance sheet and equity reconciliation. Do not exclude closing entries from the MIS instance's global filter.
5. Map equity accounts for other comprehensive income (ORI) to the reclassifiable or non-reclassifiable category. Include the associated tax effects in these categories so the displayed movements are net of tax. Closing transfers out of ORI must be marked as closing entries; reserve transfers and corrections must have their appropriate movement type.
6. Duplicate the templates before changing labels, formulas, grouping, precision or styles. Template data uses `noupdate` to preserve local edits on upgrade. Do not sum snapshots across periods: balance and equity KPIs have accumulation disabled.

There is no automatic maturity analysis, NIIF measurement adjustment, comparative
restatement or determination of whether an ORI item can be reclassified. The
accountant must configure these according to the applicable framework and policies.
An opening migration must not import both booked retained earnings and the same
historical unclosed income/expense balances.

Odoo's special `equity_unaffected` account is handled only in the unallocated
earnings adjustment, rather than also being summed as a booked equity component.
This follows OCA's treatment and prevents double counting when results are assigned.


## Usage

Open **Accounting > Reporting > Colombian Financial Statements**, choose the
company and period and click **Create reports**. The assistant creates three MIS
instances using posted entries and the company's currency. Optionally it adds the
same date range in the preceding year (29 February maps to 28 February).

Open each instance to preview, drill down or export PDF/Excel using MIS Builder.
Situation and result reports use portrait orientation; the equity matrix uses
landscape. For wide comparisons, export XLSX or use separate PDF instances for
each year; the equity matrix has nine component columns per period.

The ending balance uses the selected end date. Income and movement rows use the
selected date range. Unallocated profit before the start date is carried into
accumulated earnings, including earlier months of the fiscal year. Profit already
assigned through Odoo's `equity_unaffected` account is deducted from unallocated
profit to avoid counting it twice. Off-balance-sheet accounts are excluded.

**Control: activos menos pasivos y patrimonio**, **Control: resultado menos saldo
de ingresos y gastos**, and all cells in the equity reconciliation must be zero.
Unclassified account rows must be zero and their classifications reviewed, even
if balances offset. The assistant refuses charts with unclassified on-balance
accounts, but templates can still be used directly in MIS Builder.

Each instance is limited to one selected company. MIS Builder handles access
rights and record rules. Do not use multi-company mode for statutory individual
statements or companies with different fiscal calendars.


## Known issues / Roadmap

- Verify installation, rendering and accounting behavior in a real Odoo 18 database before production use.
- Add note references and configurable signatory blocks.
- Provide a company-specific mapping model for shared accounts with different reporting policies.
- Add finer detail for individual ORI items and accounting policy changes.
- Add cash flow and note disclosures in separate work.

This first version is Alpha. It does not reproduce the source company's branding
or contain its identity, signatures or accounting records.


## Design and sources

## Design and references

**Suggested technical name:** `l10n_co_financial_report`. The `l10n_co` prefix
places the Colombian presentation rules in the localization repository. The
broader name allows later extension beyond these three statements. The OCA
reference `account_financial_report` provides ledger/trial-balance reporting,
while `mis_template_financial_report` provides configurable balance and result
templates; this module uses the latter rather than creating another report engine.

The source PDF was reviewed as an example of presentation: account grouping,
profit subtotals and an equity-component matrix. Its figures were checked
arithmetically; anonymous figures in tests are regression fixtures, not demo
company data. The example's equity heading and final row use different dates;
the module uses selected period dates.

The statement of financial position presents assets, liabilities and equity at a
date. The income statement presents revenue, expenses and profit over a period;
the comprehensive income statement additionally presents other comprehensive
income. The equity statement reconciles each component's opening and closing
balances with profit, ORI, owner transactions, transfers and corrections.

Sources consulted on 7 October 2026:

- [Decreto 2420, Anexo 2, sections 3-6](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=74535): presentation, financial position, comprehensive income and changes in equity for the referenced SME framework. Applicable group and amendments must be assessed for the company.
- [CTCP, OrientaciÃ³n tÃ©cnica 003, Marco conceptual](https://www.dian.gov.co/fizcalizacioncontrol/herramienconsulta/NIIF/Orientaciones%20CTCP/Documento3_Orientaciones_Tecnica_NIIF_para_las_Pymes_Marco.pdf): purpose and relationship of financial statements.
- [OCA financial report templates, 18.0](https://github.com/OCA/account-financial-reporting/tree/18.0/mis_template_financial_report): styles, balance expressions and treatment of unallocated results.
- [OCA MIS Builder, 18.0](https://github.com/OCA/mis-builder/tree/18.0): account domains, initial/period/ending/unallocated balances, sub-KPIs and PDF/XLSX export.

The model adds editable, stored classifications to existing accounting records.
No new persistent accounting model, elevated access, SQL bypass or separate
amount-computation engine is introduced. The assistant creates ordinary MIS
instances; calculation continues to use OCA's ORM and record rules.


## Contributors

* Juan Arcos
