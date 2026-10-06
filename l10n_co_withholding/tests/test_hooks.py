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
