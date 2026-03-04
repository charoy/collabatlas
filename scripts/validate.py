#!/usr/bin/env python3
"""Validate CollabAtlas YAML entries against JSON schemas."""

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "data" / "entries"
SCHEMAS_DIR = ROOT / "schemas"
TAXONOMIES_DIR = ROOT / "data" / "taxonomies"

TYPE_DIRS = {
    "tool": "tools",
    "method": "methods",
    "framework": "frameworks",
    "case-study": "case-studies",
    "dataset": "datasets",
    "resource": "resources",
}


def load_taxonomy_values():
    """Load all valid taxonomy values from definition files."""
    taxonomies = {}
    for tax_file in TAXONOMIES_DIR.glob("*.yaml"):
        with open(tax_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            taxonomies[tax_file.stem] = {item["id"] for item in data}
    return taxonomies


def load_schema(entry_type: str) -> dict:
    """Load and return the JSON schema for a given entry type."""
    schema_file = SCHEMAS_DIR / f"{entry_type}.schema.json"
    if not schema_file.exists():
        print(f"  WARNING: No schema found for type '{entry_type}'")
        return None
    with open(schema_file, encoding="utf-8") as f:
        return json.load(f)


def validate_entry(filepath: Path, schema: dict, taxonomies: dict) -> list[str]:
    """Validate a single YAML entry file. Returns list of error messages."""
    errors = []
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if data is None:
        return ["File is empty"]

    # Schema validation
    if schema:
        validator = Draft7Validator(schema)
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            path = ".".join(str(p) for p in error.path) or "(root)"
            errors.append(f"Schema: {path} — {error.message}")

    # Taxonomy validation
    tax_field_map = {
        "domains": "domains",
        "collaboration-types": "collaboration_types",
        "scales": "scales",
        "research_methods": "research_methods",
        "modalities": "modalities",
        "maturity": "maturity_levels",
    }
    for field, tax_key in tax_field_map.items():
        if field not in data:
            continue
        valid_values = taxonomies.get(tax_key, set())
        if not valid_values:
            continue
        values = data[field] if isinstance(data[field], list) else [data[field]]
        for val in values:
            if val not in valid_values:
                errors.append(
                    f"Taxonomy: '{val}' is not a valid {tax_key} value. "
                    f"Valid: {sorted(valid_values)}"
                )

    return errors


def check_references(all_entries: dict[str, dict]) -> list[str]:
    """Check that all related_entries references point to existing entries."""
    all_ids = set(all_entries.keys())
    errors = []
    for entry_id, data in all_entries.items():
        for ref in data.get("related_entries", []):
            if ref not in all_ids:
                errors.append(
                    f"Entry '{entry_id}': related_entries references "
                    f"unknown entry '{ref}'"
                )
        for ref_field in ("methods_used", "tools_used"):
            for ref in data.get(ref_field, []):
                if ref not in all_ids:
                    errors.append(
                        f"Entry '{entry_id}': {ref_field} references "
                        f"unknown entry '{ref}'"
                    )
    return errors


def validate_research_articles(taxonomies: dict) -> tuple[int, int, dict]:
    """Validate data/research_articles.yaml against its schema."""
    articles_file = ROOT / "data" / "research_articles.yaml"
    schema_file = SCHEMAS_DIR / "research-article.schema.json"
    errors = 0
    count = 0
    articles_by_id = {}

    if not articles_file.exists():
        return 0, 0, {}

    with open(articles_file, encoding="utf-8") as f:
        articles = yaml.safe_load(f)

    if not articles or not isinstance(articles, list):
        return 0, 0, {}

    schema = None
    if schema_file.exists():
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)

    valid_domains = taxonomies.get("domains", set())

    for i, article in enumerate(articles):
        count += 1
        art_id = article.get("id", f"(index {i})")
        art_errors = []

        # Schema validation
        if schema:
            validator = Draft7Validator(schema)
            for error in sorted(validator.iter_errors(article), key=lambda e: list(e.path)):
                path = ".".join(str(p) for p in error.path) or "(root)"
                art_errors.append(f"Schema: {path} — {error.message}")

        # Taxonomy validation for domains
        if valid_domains:
            for domain in article.get("domains", []):
                if domain not in valid_domains:
                    art_errors.append(
                        f"Taxonomy: '{domain}' is not a valid domain. "
                        f"Valid: {sorted(valid_domains)}"
                    )

        # Duplicate ID check
        if art_id in articles_by_id:
            art_errors.append(f"Duplicate article ID: '{art_id}'")

        articles_by_id[art_id] = article

        if art_errors:
            errors += len(art_errors)
            print(f"\n  FAIL: research_articles.yaml [{art_id}]")
            for err in art_errors:
                print(f"    - {err}")
        else:
            print(f"  OK: research_articles.yaml [{art_id}]")

    return count, errors, articles_by_id


def main():
    parser = argparse.ArgumentParser(description="Validate CollabAtlas entries")
    parser.add_argument(
        "--check-refs",
        action="store_true",
        help="Also check cross-references between entries",
    )
    args = parser.parse_args()

    taxonomies = load_taxonomy_values()
    schemas = {}
    for entry_type in TYPE_DIRS:
        schemas[entry_type] = load_schema(entry_type)

    total_errors = 0
    total_files = 0
    all_entries = {}

    # Validate catalogue entries
    for entry_type, dir_name in TYPE_DIRS.items():
        entry_dir = ENTRIES_DIR / dir_name
        if not entry_dir.exists():
            continue

        schema = schemas.get(entry_type)
        for filepath in sorted(entry_dir.glob("*.yaml")):
            total_files += 1
            errors = validate_entry(filepath, schema, taxonomies)

            # Load entry for cross-reference checking
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            entry_id = data.get("id", filepath.stem)
            all_entries[entry_id] = data

            if errors:
                total_errors += len(errors)
                print(f"\n  FAIL: {filepath.relative_to(ROOT)}")
                for err in errors:
                    print(f"    - {err}")
            else:
                print(f"  OK: {filepath.relative_to(ROOT)}")

    # Validate research articles
    print(f"\n--- Research Articles ---")
    art_count, art_errors, art_entries = validate_research_articles(taxonomies)
    total_files += art_count
    total_errors += art_errors

    if args.check_refs:
        ref_errors = check_references(all_entries)
        if ref_errors:
            total_errors += len(ref_errors)
            print(f"\n  Cross-reference errors:")
            for err in ref_errors:
                print(f"    - {err}")

    print(f"\n{'='*50}")
    print(f"Validated {total_files} entries ({art_count} research articles), {total_errors} error(s)")

    if total_errors > 0:
        sys.exit(1)
    elif total_files == 0:
        print("No entries found to validate.")
    else:
        print("All entries valid.")


if __name__ == "__main__":
    main()
