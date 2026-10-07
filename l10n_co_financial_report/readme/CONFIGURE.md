1. Review **Colombian financial statement category** on every account in the chart of accounts. The field is also available as an optional list column. Defaults follow Odoo account types, not account code prefixes. Inventory, financial investments, income tax, selling/administrative expenses, equity and deferred taxes usually need a more precise classification.
2. Classify contra-asset accounts such as depreciation in the same statement category as their associated assets; their credit balances reduce the net amount. Split accounts when balances need different current/non-current classifications. Shared accounts have one classification for all their companies.
3. Set **Colombian equity movement** on miscellaneous journal entries: contributions, distributions, transfers, corrections, result closing or other movements. Mixed entries with different movement types must be split.
4. Mark result-closing entries as **Cierre de resultados**. Income and expenses in these entries are excluded from the income statement, but retained in the balance sheet and equity reconciliation. Do not exclude closing entries from the MIS instance's global filter.
5. Map equity accounts for other comprehensive income (ORI) to the reclassifiable or non-reclassifiable category. Include the associated tax effects in these categories so the displayed movements are net of tax. Closing transfers out of ORI must be marked as closing entries; reserve transfers and corrections must have their appropriate movement type.
6. Use **Configurar conceptos** in the assistant to edit the built-in template's labels, order and formulas. Template data uses `noupdate` to preserve local edits on upgrade. These assistants use the three built-in templates; duplicate templates can be used separately in MIS instances. Do not sum snapshots across periods: balance and equity KPIs have accumulation disabled.

There is no automatic maturity analysis, NIIF measurement adjustment, comparative
restatement or determination of whether an ORI item can be reclassified. The
accountant must configure these according to the applicable framework and policies.
An opening migration must not import both booked retained earnings and the same
historical unclosed income/expense balances.

Odoo's special `equity_unaffected` account is handled only in the unallocated
earnings adjustment, rather than also being summed as a booked equity component.
This follows OCA's treatment and prevents double counting when results are assigned.
