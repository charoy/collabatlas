"""Tests for validate.py — schema and taxonomy validation pipeline."""

import json
from pathlib import Path

import pytest
import yaml

import validate


# ---------------------------------------------------------------------------
# load_taxonomy_values
# ---------------------------------------------------------------------------

class TestLoadTaxonomyValues:
    """Tests for loading taxonomy definition files."""

    def test_loads_all_taxonomy_files(self, tmp_project, monkeypatch):
        """All six taxonomy files should be discovered and parsed."""
        monkeypatch.setattr(validate, "TAXONOMIES_DIR", tmp_project / "data" / "taxonomies")

        taxonomies = validate.load_taxonomy_values()

        expected_keys = {
            "domains",
            "collaboration_types",
            "scales",
            "modalities",
            "maturity_levels",
            "research_methods",
        }
        assert set(taxonomies.keys()) == expected_keys

    def test_taxonomy_values_are_sets_of_ids(self, tmp_project, monkeypatch):
        """Each taxonomy should be a set containing the 'id' field values."""
        monkeypatch.setattr(validate, "TAXONOMIES_DIR", tmp_project / "data" / "taxonomies")

        taxonomies = validate.load_taxonomy_values()

        assert "healthcare" in taxonomies["domains"]
        assert "education" in taxonomies["domains"]
        assert "pair" in taxonomies["scales"]
        assert isinstance(taxonomies["domains"], set)

    def test_ignores_non_list_yaml_files(self, tmp_project, monkeypatch):
        """YAML files whose top-level value is not a list should be skipped."""
        monkeypatch.setattr(validate, "TAXONOMIES_DIR", tmp_project / "data" / "taxonomies")

        # Write a non-list YAML file into taxonomies dir
        extra = tmp_project / "data" / "taxonomies" / "config.yaml"
        extra.write_text("key: value\n", encoding="utf-8")

        taxonomies = validate.load_taxonomy_values()
        assert "config" not in taxonomies


# ---------------------------------------------------------------------------
# validate_entry
# ---------------------------------------------------------------------------

class TestValidateEntry:
    """Tests for single-entry validation."""

    def _write_entry(self, tmp_project, data):
        """Helper: write a YAML entry and return its path."""
        entry_path = tmp_project / "data" / "entries" / "tools" / "test.yaml"
        entry_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
        return entry_path

    def _load_schema(self, tmp_project):
        schema_path = tmp_project / "schemas" / "tool.schema.json"
        if schema_path.exists():
            return json.loads(schema_path.read_text(encoding="utf-8"))
        return None

    def _load_taxonomies(self, tmp_project, monkeypatch):
        monkeypatch.setattr(validate, "TAXONOMIES_DIR", tmp_project / "data" / "taxonomies")
        return validate.load_taxonomy_values()

    def test_valid_entry_passes(self, tmp_project, valid_tool_entry, monkeypatch):
        """A fully valid entry should produce zero errors."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)
        entry_path = self._write_entry(tmp_project, valid_tool_entry)

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        assert errors == []

    def test_missing_required_field_detected(self, tmp_project, valid_tool_entry, monkeypatch):
        """Removing a required field should produce a schema error."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)

        del valid_tool_entry["title"]
        entry_path = self._write_entry(tmp_project, valid_tool_entry)

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        assert len(errors) >= 1
        assert any("title" in e for e in errors)

    def test_invalid_taxonomy_value_caught(self, tmp_project, valid_tool_entry, monkeypatch):
        """Using a non-existent taxonomy value should produce a taxonomy error."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)

        valid_tool_entry["domains"] = ["nonexistent-domain"]
        entry_path = self._write_entry(tmp_project, valid_tool_entry)

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        assert any("Taxonomy" in e and "nonexistent-domain" in e for e in errors)

    def test_empty_file_detected(self, tmp_project, monkeypatch):
        """An empty YAML file should return an 'empty' error."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)

        entry_path = tmp_project / "data" / "entries" / "tools" / "empty.yaml"
        entry_path.write_text("", encoding="utf-8")

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        assert errors == ["File is empty"]

    def test_malformed_yaml_detected(self, tmp_project, monkeypatch):
        """Broken YAML syntax should return a parse error."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)

        entry_path = tmp_project / "data" / "entries" / "tools" / "bad.yaml"
        entry_path.write_text(":\n  - :\n  bad: [unterminated", encoding="utf-8")

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        assert len(errors) == 1
        assert "YAML parse error" in errors[0]

    def test_multiple_schema_errors(self, tmp_project, valid_tool_entry, monkeypatch):
        """Multiple missing fields should each produce an error."""
        schema = self._load_schema(tmp_project)
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)

        del valid_tool_entry["title"]
        del valid_tool_entry["description"]
        entry_path = self._write_entry(tmp_project, valid_tool_entry)

        errors = validate.validate_entry(entry_path, schema, taxonomies)
        schema_errors = [e for e in errors if e.startswith("Schema")]
        assert len(schema_errors) >= 2

    def test_no_schema_skips_schema_validation(self, tmp_project, valid_tool_entry, monkeypatch):
        """When schema is None, only taxonomy validation runs."""
        taxonomies = self._load_taxonomies(tmp_project, monkeypatch)
        entry_path = self._write_entry(tmp_project, valid_tool_entry)

        errors = validate.validate_entry(entry_path, None, taxonomies)
        assert errors == []


# ---------------------------------------------------------------------------
# check_references
# ---------------------------------------------------------------------------

class TestCheckReferences:
    """Tests for cross-reference checking."""

    def test_valid_references_pass(self):
        """Entries referencing each other should produce no errors."""
        entries = {
            "tool-a": {"related_entries": ["tool-b"]},
            "tool-b": {"related_entries": ["tool-a"]},
        }
        errors = validate.check_references(entries)
        assert errors == []

    def test_broken_related_entries_detected(self):
        """A reference to a non-existent entry should be flagged."""
        entries = {
            "tool-a": {"related_entries": ["nonexistent"]},
        }
        errors = validate.check_references(entries)
        assert len(errors) == 1
        assert "nonexistent" in errors[0]
        assert "related_entries" in errors[0]

    def test_broken_tools_used_detected(self):
        """A tools_used reference to a missing entry should be flagged."""
        entries = {
            "case-study-a": {"tools_used": ["missing-tool"]},
        }
        errors = validate.check_references(entries)
        assert len(errors) == 1
        assert "missing-tool" in errors[0]
        assert "tools_used" in errors[0]

    def test_broken_methods_used_detected(self):
        """A methods_used reference to a missing entry should be flagged."""
        entries = {
            "case-study-a": {"methods_used": ["missing-method"]},
        }
        errors = validate.check_references(entries)
        assert len(errors) == 1
        assert "missing-method" in errors[0]
        assert "methods_used" in errors[0]

    def test_no_references_no_errors(self):
        """Entries without any reference fields should produce no errors."""
        entries = {
            "tool-a": {"title": "A"},
            "tool-b": {"title": "B"},
        }
        errors = validate.check_references(entries)
        assert errors == []

    def test_multiple_broken_references(self):
        """Multiple broken references across entries should all be reported."""
        entries = {
            "tool-a": {"related_entries": ["ghost-1"], "tools_used": ["ghost-2"]},
            "tool-b": {"methods_used": ["ghost-3"]},
        }
        errors = validate.check_references(entries)
        assert len(errors) == 3
