# Colombia - Estados financieros

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


## Installation

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


## Configuration

1. Review **Colombian financial statement category** on every account in the chart of accounts. The field is also available as an optional list column. Defaults follow Odoo account types, not account code prefixes. Inventory, financial investments, income tax, selling/administrative expenses, equity and deferred taxes usually need a more precise classification.
2. Classify contra-asset accounts such as depreciation in the same statement category as their associated assets; their credit balances reduce the net amount. Split accounts when balances need different current/non-current classifications. Shared accounts have one classification for all their companies.
3. Set **Colombian equity movement** on miscellaneous journal entries: contributions, distributions, transfers, corrections, result closing or other movements. Mixed entries with different movement types must be split.
4. Mark result-closing entries as **Cierre de resultados**. Income and expenses in these entries are excluded from the income statement, but retained in the balance sheet and equity reconciliation. Do not exclude closing entries from the MIS instance's global filter.
5. Map equity accounts for other comprehensive income (ORI) to the reclassifiable or non-reclassifiable category. Include the associated tax effects in these categories so the displayed movements are net of tax. Closing transfers out of ORI must be marked as closing entries; reserve transfers and corrections must have their appropriate movement type.
6. Open **Accounting > Configuration > MIS Reporting > MIS Report Templates** to edit the built-in template's labels, order and formulas. Template data uses `noupdate` to preserve local edits on upgrade. These assistants use the three built-in templates; duplicate templates can be used separately in MIS instances. Do not sum snapshots across periods: balance and equity KPIs have accumulation disabled.

There is no automatic maturity analysis, NIIF measurement adjustment, comparative
restatement or determination of whether an ORI item can be reclassified. The
accountant must configure these according to the applicable framework and policies.
An opening migration must not import both booked retained earnings and the same
historical unclosed income/expense balances.

Odoo's special `equity_unaffected` account is handled only in the unallocated
earnings adjustment, rather than also being summed as a booked equity component.
This follows OCA's treatment and prevents double counting when results are assigned.


## Usage

Open **Invoicing / Accounting > Reporting > Colombia** and select:

- **Estado de Situación Financiera**
- **Estado de Resultado Integral**
- **Estado de Cambios en el Patrimonio**

Each menu opens an Account Financial Reports assistant with company, start date,
end date, previous-year comparison and posted/all entry options. Click
**Visualizar**, **Descargar PDF** or **Descargar Excel**. The reports use native
QWeb HTML/PDF and OCA `report_xlsx`; the browser does not load a MIS widget.
HTML/PDF reuse Account Financial Reports layouts, typography and table styles.
The assistant contains only report filters and export buttons; mapping and formula
configuration are maintained beforehand under Accounting Configuration.
MIS Builder evaluates the financial formulas on the server without creating
persistent report instances. Previously created MIS instances remain available.

The equity PDF uses landscape orientation and a separate page for each period.
Its Excel workbook uses one sheet per period. Situation and result reports show
current and comparative amounts alongside each other. Exports use the company's
currency and decimal precision. Draft entries are explicitly identified when
included.

Equity opens without previous-year comparison, so it displays one period by
default. Enable comparison to display a second section explicitly labelled as
the previous year.

In **Visualizar**, click a concept to open its contributing journal items, or an
amount to restrict them to that column's period and equity component. Opening
balances include earlier items; closing balances include accumulated items.
Computed totals trace the accounting terms of their formulas. The list follows
the company's access rules and the posted/all filter. Amounts derived from
subtractions show contributing items, whose unsigned union need not sum to the
displayed result. PDF and Excel remain ordinary exports.

Before generating reports, open **Accounting > Configuration > Chart of Accounts**. Each account's
**Categoría de estados financieros colombianos** selects its reporting concept;
edit this column in the account list or the account form. Defaults
come from the Odoo account type, not Colombian account-code prefixes. Review
the defaults before issuing reports. For equity changes, classify each journal
entry with its **Movimiento de patrimonio colombiano**.

Open **Accounting > Configuration > MIS Reporting > MIS Report Templates** to
edit the corresponding Colombian report template: labels,
order and formulas determine the displayed rows and their account filters.
Changing formulas also changes the journal-item links. The category selection
on accounts is predefined; adding new category choices requires module code,
while template formulas can also select specific accounts or other fields.

The ending balance uses the selected end date. Income and movement rows use the
selected date range. Unallocated profit before the start date is carried into
accumulated earnings, including earlier months of the fiscal year. Assigned
results are deducted to avoid counting them twice. Off-balance accounts are
excluded. Review unclassified rows and reconciliation controls before issuing.


## Known issues / Roadmap

- Extend validation to representative production charts and disclosure policies.
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
templates; this module evaluates the latter on the server and uses the native export
assistant from Account Financial Reports.

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
- [CTCP, Orientación técnica 003, Marco conceptual](https://www.dian.gov.co/fizcalizacioncontrol/herramienconsulta/NIIF/Orientaciones%20CTCP/Documento3_Orientaciones_Tecnica_NIIF_para_las_Pymes_Marco.pdf): purpose and relationship of financial statements.
- [OCA financial report templates, 18.0](https://github.com/OCA/account-financial-reporting/tree/18.0/mis_template_financial_report): styles, balance expressions and treatment of unallocated results.
- [OCA MIS Builder, 18.0](https://github.com/OCA/mis-builder/tree/18.0): account domains, initial/period/ending/unallocated balances, sub-KPIs and PDF/XLSX export.

The model adds editable, stored classifications to existing accounting records.
No new persistent accounting model, elevated access, SQL bypass or separate
amount-computation engine is introduced. The assistant renders native HTML/PDF/XLSX reports; calculation continues to
use OCA's ORM and record rules. Existing MIS instances are preserved.

Version 18.0.1.1.1 adds the Colombia menu and individual report assistants. It
avoids the MIS widget lifecycle that attempted to read an invalid instance ID,
and repairs original incorrectly encoded labels without replacing custom labels.
The migration also updates the parent menu's Spanish translation.


## Contributors

* Juan Arcos
