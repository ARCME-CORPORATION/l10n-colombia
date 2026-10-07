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
