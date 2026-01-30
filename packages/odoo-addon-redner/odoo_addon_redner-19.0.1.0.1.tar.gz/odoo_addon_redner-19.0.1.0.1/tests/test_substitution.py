##############################################################################
#
#    Redner Odoo module
#    Copyright © 2026 XCG SAS <https://orbeet.io/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from .common import TestCommon


class TestSubstitution(TestCommon):
    """Test cases for redner.substitution model."""

    def setUp(self):
        super().setUp()
        self.Substitution = self.env["redner.substitution"]
        # Create a redner report for res.partner model
        self.report = self.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "redner",
                "report_name": "test_report",
                "redner_filetype": "html",
                "redner_tmpl_id": self._create_redner_template().id,
            }
        )

    def test_enrich_path_simple_field_no_relation(self):
        """Test that a simple field without relations returns path as-is."""
        sub = self.Substitution.create(
            {
                "keyword": "name",
                "value": "name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        # No path, so _enrich_path_with_model_names is not called
        # but we can test it directly
        result = self.Substitution._enrich_path_with_model_names(sub, "name")
        # 'name' is not a relational field, should return as-is
        self.assertEqual(result, "name")

    def test_enrich_path_single_relation(self):
        """Test enrichment of a single relational field."""
        sub = self.Substitution.create(
            {
                "keyword": "company",
                "value": "company_id.name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        result = self.Substitution._enrich_path_with_model_names(sub, "company_id")
        # company_id on res.partner points to res.company
        self.assertEqual(result, "company_id(res.company)")

    def test_enrich_path_nested_relations(self):
        """Test enrichment of nested relational fields."""
        sub = self.Substitution.create(
            {
                "keyword": "parent_company",
                "value": "parent_id.company_id.name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        result = self.Substitution._enrich_path_with_model_names(
            sub, "parent_id.company_id"
        )
        # parent_id -> res.partner, company_id -> res.company
        self.assertEqual(result, "parent_id(res.partner)/company_id(res.company)")

    def test_enrich_path_already_enriched(self):
        """Test that already enriched paths are preserved."""
        sub = self.Substitution.create(
            {
                "keyword": "test",
                "value": "parent_id(res.partner).name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        result = self.Substitution._enrich_path_with_model_names(
            sub, "parent_id(res.partner)"
        )
        # Should keep the existing annotation
        self.assertEqual(result, "parent_id(res.partner)")

    def test_enrich_path_mixed_enriched_and_plain(self):
        """Test path with both enriched and plain fields."""
        sub = self.Substitution.create(
            {
                "keyword": "test",
                "value": "parent_id(res.partner).company_id.name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        result = self.Substitution._enrich_path_with_model_names(
            sub, "parent_id(res.partner).company_id"
        )
        # parent_id is already enriched, company_id should be enriched
        self.assertEqual(result, "parent_id(res.partner)/company_id(res.company)")

    def test_enrich_path_no_source_model(self):
        """Test that path is returned as-is when no source model."""
        sub = self.Substitution.create(
            {
                "keyword": "test",
                "value": "partner_id.name",
                "converter": "field",
                # No ir_actions_report_id or template_id
            }
        )
        result = self.Substitution._enrich_path_with_model_names(sub, "partner_id")
        # No source model, should just replace dots with slashes
        self.assertEqual(result, "partner_id")

    def test_enrich_path_unknown_field(self):
        """Test that unknown fields are kept as-is."""
        sub = self.Substitution.create(
            {
                "keyword": "test",
                "value": "unknown_field.name",
                "converter": "field",
                "ir_actions_report_id": self.report.id,
            }
        )
        result = self.Substitution._enrich_path_with_model_names(sub, "unknown_field")
        # Field doesn't exist, should return as-is
        self.assertEqual(result, "unknown_field")
