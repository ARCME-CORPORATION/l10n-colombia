# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .. import hooks


@tagged("post_install", "-at_install")
class TestWithholdingHooks(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Withholding hook test",
                "country_id": cls.env.ref("base.co").id,
            }
        )
        cls.other_company = cls.env["res.company"].create(
            {
                "name": "Other withholding company",
                "country_id": cls.env.ref("base.co").id,
            }
        )
        cls.group = cls.env["account.tax.group"].create(
            {
                "name": "Withholding test group",
                "company_id": cls.company.id,
                "country_id": cls.company.country_id.id,
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Renamed withholding tax",
                "amount": -4,
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
                "tax_group_id": cls.group.id,
            }
        )
        cls.env["ir.model.data"].create(
            {
                "module": "account",
                "name": f"{cls.company.id}_l10n_co_tax_23",
                "model": "account.tax",
                "res_id": cls.tax.id,
            }
        )
        cls.env["ir.model.data"].create(
            {
                "module": "account",
                "name": f"{cls.company.id}_tax_group_r_ren_0",
                "model": "account.tax.group",
                "res_id": cls.group.id,
            }
        )

    def test_company_chart_tax_resolves_after_rename(self):
        self.assertEqual(
            hooks._find_tax_by_xmlid(
                self.env,
                self.company,
                "l10n_co.l10n_co_tax_23",
            ),
            self.tax,
        )
        self.assertFalse(
            hooks._find_tax_by_xmlid(
                self.env,
                self.other_company,
                "l10n_co.l10n_co_tax_23",
            )
        )

    def test_legacy_reference_cannot_cross_companies(self):
        self.env["ir.model.data"].create(
            {
                "module": "l10n_co",
                "name": "withholding_legacy_test_tax",
                "model": "account.tax",
                "res_id": self.tax.id,
            }
        )
        self.assertEqual(
            hooks._find_tax_by_xmlid(
                self.env,
                self.company,
                "l10n_co.withholding_legacy_test_tax",
            ),
            self.tax,
        )
        self.assertFalse(
            hooks._find_tax_by_xmlid(
                self.env,
                self.other_company,
                "l10n_co.withholding_legacy_test_tax",
            )
        )

    def test_zero_tax_uses_company_group_and_is_reused(self):
        tax = hooks._get_or_create_zero_tax(
            self.env,
            self.company,
            "Test RteFte 0%",
            "l10n_co.tax_group_r_ren_0",
            "rte_fte",
        )
        self.assertEqual(tax.tax_group_id, self.group)
        self.assertEqual(tax.company_id, self.company)
        self.assertEqual(
            tax,
            hooks._get_or_create_zero_tax(
                self.env,
                self.company,
                "Test RteFte 0%",
                "l10n_co.tax_group_r_ren_0",
                "rte_fte",
            ),
        )

    def test_missing_group_does_not_select_an_unrelated_group(self):
        with self.assertRaises(UserError):
            hooks._get_or_create_zero_tax(
                self.env,
                self.company,
                "Missing group test",
                "l10n_co.missing_withholding_group_test",
                "rte_fte",
            )

    def test_numeric_account_mappings_are_created_and_reused(self):
        account_model = self.env["account.account"].with_company(self.company)
        accounts = {}
        codes = set(hooks.ACCOUNT_MAPPINGS) | set(hooks.ACCOUNT_MAPPINGS.values())
        for code in codes:
            self.assertTrue(code.isdigit())
            accounts[code] = account_model.create(
                {
                    "name": f"Test {code}",
                    "code": code,
                    "account_type": "liability_current"
                    if code.startswith("23")
                    else "asset_current",
                    "company_ids": [(6, 0, [self.company.id])],
                }
            )
        position = self.env["account.fiscal.position"].create(
            {
                "name": "Hook mapping test",
                "company_id": self.company.id,
            }
        )
        hooks._add_account_mappings(self.env, self.company, position)
        first_ids = position.account_ids.ids
        self.assertEqual(len(first_ids), 9)
        hooks._add_account_mappings(self.env, self.company, position)
        self.assertEqual(position.account_ids.ids, first_ids)
        for src, dst in hooks.ACCOUNT_MAPPINGS.items():
            line = position.account_ids.filtered(
                lambda row, src=src: row.account_src_id == accounts[src],
            )
            self.assertEqual(line.account_dest_id, accounts[dst])
            self.assertFalse(
                hooks._find_account_by_code(
                    self.env,
                    self.other_company,
                    src,
                )
            )

    def _prepare_purchase_chart(self):
        for key in ("tax_group_r_iva_075", "tax_group_r_ica_0"):
            group = self.env["account.tax.group"].create(
                {
                    "name": key,
                    "company_id": self.company.id,
                    "country_id": self.company.country_id.id,
                }
            )
            self.env["ir.model.data"].create(
                {
                    "module": "account",
                    "name": f"{self.company.id}_{key}",
                    "model": "account.tax.group",
                    "res_id": group.id,
                }
            )
        taxes = self.tax
        for number, amount in [(16, -0.1), (12, -2.85), (46, -0.414), (43, 0)]:
            tax = self.env["account.tax"].create(
                {
                    "name": f"Renamed purchase tax {number}",
                    "amount": amount,
                    "type_tax_use": "purchase",
                    "company_id": self.company.id,
                    "tax_group_id": self.group.id,
                }
            )
            self.env["ir.model.data"].create(
                {
                    "module": "account",
                    "name": f"{self.company.id}_l10n_co_tax_{number}",
                    "model": "account.tax",
                    "res_id": tax.id,
                }
            )
            taxes |= tax
        return taxes

    def test_purchase_types_and_preserved_configuration(self):
        taxes = self._prepare_purchase_chart()
        before = taxes.read(
            [
                "amount",
                "type_tax_use",
                "invoice_repartition_line_ids",
                "refund_repartition_line_ids",
            ]
        )
        hooks._configure_chart_withholding_taxes(self.env, self.company)
        self.assertEqual(
            set(taxes.mapped("l10n_co_withholding_type")),
            {"rte_fte", "rte_iva", "rte_ica"},
        )
        self.assertEqual(
            before,
            taxes.read(
                [
                    "amount",
                    "type_tax_use",
                    "invoice_repartition_line_ids",
                    "refund_repartition_line_ids",
                ]
            ),
        )
        self.tax.l10n_co_withholding_type = "rte_iva"
        hooks._configure_chart_withholding_taxes(self.env, self.company)
        self.assertEqual(self.tax.l10n_co_withholding_type, "rte_iva")
        self.assertFalse(self.company.l10n_co_is_retention_agent)
        self.assertFalse(self.company.l10n_co_default_rte_fte_tax_ids)

    def test_future_setup_maps_all_purchase_types_without_counterparts(self):
        taxes = self._prepare_purchase_chart()
        hooks._configure_chart_withholding_taxes(self.env, self.company)
        hooks._setup_withholding_for_company(self.env, self.company)
        hooks._create_sales_withholding_counterparts(self.env, self.company)
        positions = self.env["account.fiscal.position"].search(
            [("company_id", "=", self.company.id)]
        )
        simple = positions.filtered(lambda p: p.name == "Régimen Simple (Sin ReteFte)")
        non_taxpayer = positions.filtered(
            lambda p: p.name == "No Contribuyente (Sin Retenciones)"
        )
        self.assertEqual(len(simple.tax_ids), 2)
        self.assertEqual(len(non_taxpayer.tax_ids), 4)
        self.assertEqual(
            non_taxpayer.tax_ids.tax_src_id, taxes.filtered(lambda t: t.amount < 0)
        )
        self.assertTrue(
            all(
                t.amount == 0 and t.type_tax_use == "purchase"
                for t in non_taxpayer.tax_ids.tax_dest_id
            )
        )
        self.assertFalse(taxes.filtered("l10n_co_withholding_counterpart"))
        self.assertFalse(
            self.env["account.tax"].search(
                [
                    ("company_id", "=", self.company.id),
                    ("l10n_co_withholding_counterpart", "=", True),
                ]
            )
        )
        original_ids = positions.tax_ids.ids
        tax_ids = (
            self.env["account.tax"].search([("company_id", "=", self.company.id)]).ids
        )
        hooks._configure_chart_withholding_taxes(self.env, self.company)
        hooks._setup_withholding_for_company(self.env, self.company)
        self.assertEqual(positions.tax_ids.ids, original_ids)
        self.assertEqual(
            self.env["account.tax"].search([("company_id", "=", self.company.id)]).ids,
            tax_ids,
        )

    def test_positive_chart_tax_is_not_classified(self):
        self.tax.amount = 4
        hooks._configure_chart_withholding_taxes(self.env, self.company)
        self.assertFalse(self.tax.l10n_co_withholding_type)
