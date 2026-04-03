#!/usr/bin/env python3
"""Tests for issue_to_entry.py — CollabAtlas issue-to-PR bot."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the scripts directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from issue_to_entry import (
    parse_issue_body,
    get_checkboxes,
    get_dropdown,
    get_comma_list,
    get_external_links,
    get_seminal_works,
    get_lines_as_list,
    get_bool,
    get_int,
    get_text,
    title_to_id,
    detect_entry_type,
    extract_clean_title,
    build_common_fields,
    add_tool_fields,
    build_frontmatter,
    DOMAIN_MAP,
    COLLAB_TYPE_MAP,
    SCALE_MAP,
    MODALITY_MAP,
    MATURITY_MAP,
)


class TestParseIssueBody(unittest.TestCase):
    """Test the Markdown issue body parser."""

    def test_basic_parsing(self):
        body = """\
### Title

My Cool Tool

### Full Description

A tool for doing things.
It has many features.

### Maturity Level

Established
"""
        sections = parse_issue_body(body)
        self.assertEqual(sections["Title"], "My Cool Tool")
        self.assertEqual(sections["Full Description"], "A tool for doing things.\nIt has many features.")
        self.assertEqual(sections["Maturity Level"], "Established")

    def test_empty_field(self):
        body = """\
### Title

My Tool

### Additional Context

_No response_
"""
        sections = parse_issue_body(body)
        self.assertEqual(sections["Title"], "My Tool")
        self.assertEqual(sections["Additional Context"], "_No response_")

    def test_checkboxes(self):
        body = """\
### Relevant Domains (select all that apply)

- [X] Healthcare
- [ ] Education
- [X] Software Engineering
- [ ] Design
"""
        sections = parse_issue_body(body)
        result = get_checkboxes(sections, "Relevant Domains (select all that apply)", DOMAIN_MAP)
        self.assertEqual(result, ["healthcare", "software-engineering"])

    def test_checkboxes_lowercase_x(self):
        body = """\
### Scale (select all that apply)

- [x] Pair
- [X] Small Team (3-10)
- [ ] Organization (11-100)
"""
        sections = parse_issue_body(body)
        result = get_checkboxes(sections, "Scale (select all that apply)", SCALE_MAP)
        self.assertEqual(result, ["pair", "small-team"])


class TestFieldExtractors(unittest.TestCase):
    """Test individual field extraction functions."""

    def test_get_text_normal(self):
        sections = {"Title": "My Tool"}
        self.assertEqual(get_text(sections, "Title"), "My Tool")

    def test_get_text_no_response(self):
        sections = {"Title": "_No response_"}
        self.assertIsNone(get_text(sections, "Title"))

    def test_get_text_missing(self):
        sections = {}
        self.assertIsNone(get_text(sections, "Title"))

    def test_get_dropdown(self):
        sections = {"Maturity Level": "Well-Documented"}
        result = get_dropdown(sections, "Maturity Level", MATURITY_MAP)
        self.assertEqual(result, "well-documented")

    def test_get_comma_list(self):
        sections = {"Tags (comma-separated)": "real-time, brainstorming, whiteboard"}
        result = get_comma_list(sections, "Tags (comma-separated)")
        self.assertEqual(result, ["real-time", "brainstorming", "whiteboard"])

    def test_get_comma_list_empty(self):
        sections = {"Tags (comma-separated)": "_No response_"}
        result = get_comma_list(sections, "Tags (comma-separated)")
        self.assertEqual(result, [])

    def test_get_external_links(self):
        sections = {"External Links": "website | https://example.com | Official Site\npaper | https://doi.org/10.1234 | Key Paper"}
        result = get_external_links(sections, "External Links")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "website")
        self.assertEqual(result[0]["url"], "https://example.com")
        self.assertEqual(result[0]["title"], "Official Site")

    def test_get_seminal_works(self):
        sections = {"Seminal Works": "Mind in Society | Lev Vygotsky | 1978 | https://example.com\nActivity Theory | Bonnie Nardi | 1996"}
        result = get_seminal_works(sections, "Seminal Works")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Mind in Society")
        self.assertEqual(result[0]["authors"], ["Lev Vygotsky"])
        self.assertEqual(result[0]["year"], 1978)
        self.assertEqual(result[0]["url"], "https://example.com")
        self.assertEqual(result[1]["title"], "Activity Theory")
        self.assertNotIn("url", result[1])

    def test_get_lines_as_list(self):
        sections = {"Method Steps (one per line)": "Step 1\nStep 2\n\nStep 3"}
        result = get_lines_as_list(sections, "Method Steps (one per line)")
        self.assertEqual(result, ["Step 1", "Step 2", "Step 3"])

    def test_get_bool_yes(self):
        sections = {"Is it open source?": "Yes"}
        self.assertTrue(get_bool(sections, "Is it open source?"))

    def test_get_bool_no(self):
        sections = {"Is it open source?": "No"}
        self.assertFalse(get_bool(sections, "Is it open source?"))

    def test_get_int(self):
        sections = {"Year": "2023"}
        self.assertEqual(get_int(sections, "Year"), 2023)

    def test_get_int_invalid(self):
        sections = {"Year": "not-a-number"}
        self.assertIsNone(get_int(sections, "Year"))


class TestTitleToId(unittest.TestCase):
    """Test ID generation from titles."""

    def test_simple(self):
        self.assertEqual(title_to_id("My Cool Tool"), "my-cool-tool")

    def test_special_characters(self):
        self.assertEqual(title_to_id("Miro (Online Whiteboard)"), "miro-online-whiteboard")

    def test_accented_characters(self):
        self.assertEqual(title_to_id("Recherche Data Gouv"), "recherche-data-gouv")

    def test_multiple_spaces(self):
        self.assertEqual(title_to_id("Some   Tool   Name"), "some-tool-name")

    def test_leading_trailing_hyphens(self):
        self.assertEqual(title_to_id("  -My Tool-  "), "my-tool")

    def test_unicode(self):
        # French accented characters should be stripped
        self.assertEqual(title_to_id("Méthode Participative"), "methode-participative")


class TestEntryTypeDetection(unittest.TestCase):
    """Test entry type detection from labels and titles."""

    def test_from_labels(self):
        self.assertEqual(detect_entry_type("new-entry,tool,triage", ""), "tool")

    def test_case_study_from_labels(self):
        self.assertEqual(detect_entry_type("new-entry,case-study,triage", ""), "case-study")

    def test_from_title(self):
        self.assertEqual(detect_entry_type("new-entry,triage", "[New Tool] My Tool"), "tool")

    def test_case_study_from_title(self):
        self.assertEqual(detect_entry_type("new-entry,triage", "[New Case Study] Some Study"), "case-study")

    def test_extract_clean_title(self):
        self.assertEqual(extract_clean_title("[New Tool] My Cool Tool"), "My Cool Tool")

    def test_extract_clean_title_no_prefix(self):
        self.assertEqual(extract_clean_title("My Cool Tool"), "My Cool Tool")


class TestBuildCommonFields(unittest.TestCase):
    """Test building the common entry data."""

    def test_basic_build(self):
        sections = {
            "Title": "Test Tool",
            "Tagline": "A test tool for testing.",
            "Full Description": "A longer description of the test tool.",
            "Relevant Domains (select all that apply)": "- [X] Software Engineering\n- [ ] Healthcare",
            "Collaboration Types (select all that apply)": "- [X] Distributed\n- [X] Open Source",
            "Scale (select all that apply)": "- [X] Small Team (3-10)",
            "Modality (select all that apply)": "- [X] Remote\n- [X] Hybrid",
            "Maturity Level": "Established",
        }
        data = build_common_fields("test-tool", "tool", sections, "testuser")

        self.assertEqual(data["id"], "test-tool")
        self.assertEqual(data["type"], "tool")
        self.assertEqual(data["title"], "Test Tool")
        self.assertEqual(data["tagline"], "A test tool for testing.")
        self.assertEqual(data["domains"], ["software-engineering"])
        self.assertEqual(data["collaboration-types"], ["distributed", "open-source"])
        self.assertEqual(data["scale"], ["small-team"])
        self.assertEqual(data["modality"], ["remote", "hybrid"])
        self.assertEqual(data["maturity"], "established")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["contributors"], ["testuser"])


class TestBuildFrontmatter(unittest.TestCase):
    """Test Markdown front matter generation."""

    def test_tool_frontmatter(self):
        data = {
            "id": "test-tool",
            "type": "tool",
            "title": "Test Tool",
            "tagline": "A test tool.",
            "domains": ["software-engineering", "education"],
            "collaboration_type": ["distributed"],
            "scale": ["small-team"],
            "modality": ["remote"],
            "maturity": "established",
            "status": "draft",
        }
        result = build_frontmatter(data)
        self.assertIn('title: "Test Tool"', result)
        self.assertIn('data_id: "test-tool"', result)
        self.assertIn('domains: ["software-engineering", "education"]', result)
        self.assertIn('status: "draft"', result)
        self.assertTrue(result.startswith("---\n"))
        self.assertTrue(result.strip().endswith("---"))


class TestEndToEnd(unittest.TestCase):
    """End-to-end test: parse a realistic issue body and generate files."""

    TOOL_ISSUE_BODY = """\
### Title

TestBot Tool

### Tagline

An automated testing tool for CI/CD pipelines.

### Full Description

TestBot is a powerful tool for automated testing in continuous integration
and continuous delivery pipelines. It supports multiple languages and
integrates with popular CI systems.

### Website URL

https://testbot.example.com

### Is it open source?

Yes

### License

MIT

### Supported Platforms (comma-separated)

Web, Linux, macOS

### Relevant Domains (select all that apply)

- [X] Software Engineering
- [ ] Healthcare
- [X] Education

### Collaboration Types (select all that apply)

- [X] Open Source
- [X] Distributed

### Scale (select all that apply)

- [X] Small Team (3-10)
- [X] Organization (11-100)

### Modality (select all that apply)

- [X] Remote
- [X] Hybrid

### Maturity Level

Well-Documented

### External Links

website | https://testbot.example.com | Official Website
documentation | https://docs.testbot.example.com | Documentation

### Tags (comma-separated)

testing, CI/CD, automation

### Related CollabAtlas Entries (comma-separated IDs)

github, jupyter

### Additional Context

_No response_
"""

    def test_full_tool_pipeline(self):
        """Parse a full tool issue body and verify the generated data."""
        from issue_to_entry import (
            build_common_fields,
            add_tool_fields,
            add_trailing_common_fields,
            write_yaml_entry,
            write_markdown_entry,
            ROOT,
            DATA_DIR,
            CONTENT_DIR,
        )

        sections = parse_issue_body(self.TOOL_ISSUE_BODY)

        # Verify parsing
        self.assertEqual(sections["Title"], "TestBot Tool")
        self.assertEqual(sections["Website URL"], "https://testbot.example.com")
        self.assertEqual(sections["Is it open source?"], "Yes")

        # Build entry
        entry_id = title_to_id(sections["Title"])
        self.assertEqual(entry_id, "testbot-tool")

        data = build_common_fields(entry_id, "tool", sections, "testuser")
        add_tool_fields(data, sections)
        add_trailing_common_fields(data, sections)

        # Verify data
        self.assertEqual(data["id"], "testbot-tool")
        self.assertEqual(data["type"], "tool")
        self.assertEqual(data["website_url"], "https://testbot.example.com")
        self.assertTrue(data["open_source"])
        self.assertEqual(data["license"], "MIT")
        self.assertEqual(data["supported_platforms"], ["Web", "Linux", "macOS"])
        self.assertEqual(data["domains"], ["software-engineering", "education"])
        self.assertEqual(data["collaboration-types"], ["open-source", "distributed"])
        self.assertEqual(data["scale"], ["small-team", "organization"])
        self.assertEqual(data["modality"], ["remote", "hybrid"])
        self.assertEqual(data["maturity"], "well-documented")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(len(data["external_links"]), 2)
        self.assertEqual(data["tags"], ["testing", "CI/CD", "automation"])
        self.assertEqual(data["related_entries"], ["github", "jupyter"])

        # Verify frontmatter generation
        fm = build_frontmatter(data)
        self.assertIn('data_id: "testbot-tool"', fm)
        self.assertIn('domains: ["software-engineering", "education"]', fm)


if __name__ == "__main__":
    unittest.main()
