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
