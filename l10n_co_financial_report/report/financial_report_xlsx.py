# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class FinancialStatementXlsx(models.AbstractModel):
    _name = "report.l10n_co_financial_report.statement_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Colombian Financial Statement XLSX"

    def generate_xlsx_report(self, workbook, data, objects):
        wizard = self.env["l10n_co.financial.report.wizard"].browse(data["wizard_id"])
        statement = wizard._get_statement_data()
        decimals = statement["currency"].decimal_places
        number_format = "#,##0" + ("." + "0" * decimals if decimals else "")
        title_format = workbook.add_format({"bold": True, "font_size": 14})
        header_format = workbook.add_format({"bold": True, "bg_color": "#E8EDF2"})
        number = workbook.add_format({"num_format": number_format})
        total_number = workbook.add_format(
            {"num_format": number_format, "bold": True, "top": 1}
        )
        for index, section in enumerate(statement["sections"]):
            sheet = workbook.add_worksheet(f"Estado {index + 1}")
            sheet.set_landscape() if statement["equity"] else sheet.set_portrait()
            sheet.fit_to_pages(1, 0)
            sheet.set_paper(9)
            sheet.set_column(0, 0, 55 if not statement["equity"] else 40)
            sheet.set_column(1, len(section["columns"]), 20)
            sheet.write(0, 0, statement["company"].name, title_format)
            sheet.write(1, 0, statement["title"], title_format)
            sheet.write(2, 0, "NIT: " + (statement["company"].vat or ""))
            sheet.write(
                3,
                0,
                section["period"]
                or (f"{statement['date_from']} / {statement['date_to']}"),
            )
            sheet.write(4, 0, "Moneda: " + statement["currency"].name)
            if statement["drafts"]:
                sheet.write(5, 0, "Incluye asientos en borrador")
            sheet.write(6, 0, section["period"])
            sheet.write_row(7, 0, ["Concepto"] + section["columns"], header_format)
            for row_index, row in enumerate(section["rows"], 8):
                sheet.write(
                    row_index, 0, row["name"], header_format if row["total"] else None
                )
                if not row["header"]:
                    sheet.write_row(
                        row_index,
                        1,
                        row["amounts"],
                        total_number if row["total"] else number,
                    )
            sheet.freeze_panes(8, 1)
            sheet.repeat_rows(0, 7)
            sheet.print_area(0, 0, len(section["rows"]) + 7, len(section["columns"]))
