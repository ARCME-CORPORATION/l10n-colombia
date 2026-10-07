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
