"""Shared pytest fixtures for CollabAtlas script tests."""

import json
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal CollabAtlas project structure under tmp_path.

    Returns the project root path with:
      - schemas/ containing the real tool schema
      - data/taxonomies/ with minimal taxonomy files
      - data/entries/tools/ (empty, ready for test entries)
    """
    # Schemas dir — copy real tool schema so tests use the actual schema
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    real_schema = Path(__file__).resolve().parent.parent / "schemas" / "tool.schema.json"
    if real_schema.exists():
        (schemas_dir / "tool.schema.json").write_text(
            real_schema.read_text(encoding="utf-8"), encoding="utf-8"
        )

    # Taxonomies
    taxonomies_dir = tmp_path / "data" / "taxonomies"
    taxonomies_dir.mkdir(parents=True)

    taxonomy_data = {
        "domains": [
            {"id": "healthcare", "label": "Healthcare"},
            {"id": "education", "label": "Education"},
        ],
        "collaboration_types": [
            {"id": "co-design", "label": "Co-Design"},
            {"id": "consultation", "label": "Consultation"},
        ],
        "scales": [
            {"id": "pair", "label": "Pair"},
            {"id": "small-team", "label": "Small Team"},
            {"id": "organization", "label": "Organization"},
            {"id": "multi-org", "label": "Multi-Org"},
            {"id": "community", "label": "Community"},
        ],
        "modalities": [
            {"id": "in-person", "label": "In-Person"},
            {"id": "remote", "label": "Remote"},
            {"id": "hybrid", "label": "Hybrid"},
        ],
        "maturity_levels": [
            {"id": "emerging", "label": "Emerging"},
            {"id": "established", "label": "Established"},
            {"id": "well-documented", "label": "Well-Documented"},
        ],
        "research_methods": [
            {"id": "case-study", "label": "Case Study"},
            {"id": "survey", "label": "Survey"},
        ],
    }

    for name, items in taxonomy_data.items():
        (taxonomies_dir / f"{name}.yaml").write_text(
            yaml.dump(items, default_flow_style=False), encoding="utf-8"
        )

    # Entry directories
    (tmp_path / "data" / "entries" / "tools").mkdir(parents=True)

    return tmp_path


@pytest.fixture
def valid_tool_entry():
    """Return a minimal valid tool YAML dict that passes schema validation."""
    return {
        "id": "test-tool",
        "type": "tool",
        "title": "Test Tool",
        "tagline": "A tool for testing.",
        "description": "This is a test tool used for validation tests.",
        "domains": ["healthcare"],
        "collaboration-types": ["co-design"],
        "scales": ["small-team"],
        "modalities": ["remote"],
        "maturity": "emerging",
        "contributors": ["tester"],
        "status": "draft",
    }
