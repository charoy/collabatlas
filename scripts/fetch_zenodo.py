#!/usr/bin/env python3
"""Import or enrich CollabAtlas dataset entries from Zenodo records."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timezone
from html import unescape
from pathlib import Path

import requests

from dataset_utils import (
    DATASET_DATA_DIR,
    load_dataset_entry,
    load_markdown_body,
    load_taxonomy_records,
    merge_dataset_metadata,
    slugify,
    write_dataset_files,
)

ZENODO_RECORD_URL = "https://zenodo.org/api/records/{record_id}"
ZENODO_SEARCH_URL = "https://zenodo.org/api/records"
HEADERS = {"User-Agent": "CollabAtlas/1.0 (mailto:admin@collabatlas.org)"}

DOMAINS = load_taxonomy_records("domains")
COLLAB_TYPES = load_taxonomy_records("collaboration_types")
SCALES = load_taxonomy_records("scales")
MODALITIES = load_taxonomy_records("modalities")
RESEARCH_METHODS = load_taxonomy_records("research_methods")

DOMAIN_IDS = [record["id"] for record in DOMAINS if record.get("id")]
COLLAB_TYPE_IDS = [record["id"] for record in COLLAB_TYPES if record.get("id")]
SCALE_IDS = [record["id"] for record in SCALES if record.get("id")]
MODALITY_IDS = [record["id"] for record in MODALITIES if record.get("id")]
RESEARCH_METHOD_IDS = [record["id"] for record in RESEARCH_METHODS if record.get("id")]
MATURITY_OPTIONS = ["emerging", "established", "well-documented"]
STATUS_OPTIONS = ["draft", "published", "archived"]


def current_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def print_taxonomy_options() -> None:
    """Display accepted taxonomy IDs for new dataset creation."""
    groups = [
        ("domains", DOMAINS),
        ("collaboration-types", COLLAB_TYPES),
        ("scales", SCALES),
        ("modalities", MODALITIES),
        ("research-methods", RESEARCH_METHODS),
    ]
    for group_name, records in groups:
        print(f"\n{group_name}:")
        for record in records:
            print(f"  - {record.get('id')}: {record.get('label')}")


def read_input(prompt: str) -> str:
    """Read interactive input and exit cleanly if the prompt is aborted."""
    try:
        return input(prompt)
    except EOFError:
        print("\nInteractive input aborted.", file=sys.stderr)
        sys.exit(1)


def prompt_text(
    label: str,
    default: str | None = None,
    required: bool = False,
) -> str | None:
    """Prompt for a text value with optional default and required mode."""
    while True:
        suffix = f" [{default}]" if default else ""
        value = read_input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return None
        print("Please enter a value.")


def prompt_yes_no(label: str, default: bool = False) -> bool:
    """Prompt for a yes/no answer."""
    default_hint = "Y/n" if default else "y/N"
    while True:
        value = read_input(f"{label} [{default_hint}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


def prompt_single_choice(
    label: str,
    options: list[str],
    default: str | None = None,
) -> str:
    """Prompt for a single choice by number or exact value."""
    print(f"\n{label}:")
    for index, option in enumerate(options, start=1):
        marker = " (default)" if option == default else ""
        print(f"  {index}. {option}{marker}")

    while True:
        value = read_input("Select one option by number or value: ").strip()
        if not value and default is not None:
            return default
        if value.isdigit():
            idx = int(value) - 1
            if 0 <= idx < len(options):
                return options[idx]
        if value in options:
            return value
        print("Invalid choice. Try again.")


def prompt_multi_choice(
    label: str,
    records: list[dict],
    required: bool = False,
) -> list[str]:
    """Prompt for one or more taxonomy values by number or id."""
    print(f"\n{label}:")
    for index, record in enumerate(records, start=1):
        print(f"  {index}. {record.get('label')} [{record.get('id')}]")

    print("Enter one or more numbers or ids separated by commas.")
    while True:
        raw = read_input("Selection: ").strip()
        if not raw:
            if required:
                print("At least one selection is required.")
                continue
            return []

        values = []
        valid_ids = [record.get("id") for record in records]
        for token in [part.strip() for part in raw.split(",") if part.strip()]:
            resolved = None
            if token.isdigit():
                idx = int(token) - 1
                if 0 <= idx < len(records):
                    resolved = records[idx].get("id")
            elif token in valid_ids:
                resolved = token

            if not resolved:
                print(f"Unknown selection: {token}")
                values = []
                break
            if resolved not in values:
                values.append(resolved)

        if values:
            return values
        print("Please try again.")


def prompt_contributors(defaults: list[str]) -> list[str]:
    """Prompt for contributor names as a comma-separated list."""
    default_text = ", ".join(defaults)
    raw = prompt_text("Contributors (comma-separated)", default=default_text)
    values = [item.strip() for item in (raw or "").split(",") if item.strip()]
    return values or defaults


def run_interactive_setup(args: argparse.Namespace) -> argparse.Namespace:
    """Fill missing CLI arguments interactively."""
    print("CollabAtlas Zenodo import — interactive mode")
    print("Press Enter to accept defaults when shown.\n")

    if not args.identifier:
        args.identifier = prompt_text(
            "Zenodo record ID, DOI, or URL",
            required=True,
        )

    return args


def strip_html(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def build_tagline(description: str | None, title: str) -> str:
    if description:
        first_sentence = re.split(r"(?<=[.!?])\s+", description.strip())[0]
        tagline = first_sentence.strip()
        if len(tagline) <= 200:
            return tagline
        return tagline[:197].rstrip() + "..."
    fallback = f"Zenodo dataset record for {title}."
    return fallback[:200]


def human_size(num_bytes: int | None, file_count: int) -> str | None:
    if num_bytes is None:
        return None
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    unit = units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    size_str = f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
    if file_count > 1:
        return f"{size_str} across {file_count} files"
    return size_str


def fetch_zenodo_record(identifier: str) -> dict:
    identifier = identifier.strip()
    if identifier.startswith("https://doi.org/"):
        identifier = identifier.replace("https://doi.org/", "", 1)
    if identifier.startswith("https://zenodo.org/records/"):
        identifier = identifier.rsplit("/", 1)[-1]

    if re.fullmatch(r"\d+", identifier):
        response = requests.get(
            ZENODO_RECORD_URL.format(record_id=identifier),
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    response = requests.get(
        ZENODO_SEARCH_URL,
        params={"q": f'doi:"{identifier}"', "size": 1},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    if not hits:
        raise ValueError(f"No Zenodo record found for '{identifier}'")
    return hits[0]


def parse_temporal_coverage(metadata: dict) -> str | None:
    dates = metadata.get("dates") or []
    parts = []
    for entry in dates:
        label = (entry.get("type") or entry.get("description") or "").strip()
        value = (entry.get("date") or "").strip()
        if label and value:
            parts.append(f"{label}: {value}")
        elif value:
            parts.append(value)
    return "; ".join(parts) or None


def parse_zenodo_dataset(record: dict) -> dict:
    metadata = record.get("metadata") or {}
    description = strip_html(metadata.get("description"))
    files = record.get("files") or []
    total_size = sum(file_info.get("size") or 0 for file_info in files)
    formats = []
    for file_info in files:
        key = file_info.get("key") or ""
        ext = Path(key).suffix.lower().lstrip(".")
        if ext and ext not in formats:
            formats.append(ext.upper())

    doi = metadata.get("doi") or record.get("doi")
    source_url = (
        (record.get("links") or {}).get("self_html")
        or (record.get("links") or {}).get("html")
        or (f"https://doi.org/{doi}" if doi else None)
    )

    rights = metadata.get("license") or metadata.get("rights") or {}
    if isinstance(rights, list):
        rights = rights[0] if rights else {}

    keywords = [keyword for keyword in (metadata.get("keywords") or []) if keyword]
    publication_date = metadata.get("publication_date")
    record_id = str(record.get("id") or metadata.get("prereserve_doi", {}).get("recid") or "")

    external_links = []
    if doi:
        external_links.append(
            {
                "type": "doi",
                "url": f"https://doi.org/{doi}",
                "title": "Zenodo DOI",
            }
        )
    if source_url:
        external_links.append(
            {
                "type": "website",
                "url": source_url,
                "title": "Zenodo record",
            }
        )

    return {
        "type": "dataset",
        "title": metadata.get("title") or f"Zenodo record {record_id}",
        "tagline": build_tagline(description, metadata.get("title") or "dataset"),
        "description": description or f"Zenodo dataset record {record_id}.",
        "source_url": source_url,
        "format": ", ".join(formats) if formats else None,
        "size": human_size(total_size if files else None, len(files)),
        "license": rights.get("id") or rights.get("title") or rights.get("label"),
        "temporal_coverage": parse_temporal_coverage(metadata),
        "platform": "zenodo",
        "platform_id": doi or record_id,
        "doi": doi,
        "version": metadata.get("version"),
        "tags": keywords,
        "external_links": external_links,
        "source_services": ["zenodo"],
        "fetched_at": current_timestamp(),
        "last_reviewed": date.today().isoformat(),
        "created": publication_date or date.today().isoformat(),
    }


def build_new_entry(parsed: dict, entry_id: str, args: argparse.Namespace) -> dict:
    return {
        "id": entry_id,
        **parsed,
        "domains": args.domains,
        "collaboration-types": args.collaboration_types,
        "scales": args.scales,
        "modalities": args.modalities,
        "maturity": args.maturity,
        "contributors": args.contributors,
        "status": args.status,
        **({"research_methods": args.research_methods} if args.research_methods else {}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import or enrich a dataset entry from a Zenodo record"
    )
    parser.add_argument(
        "identifier",
        nargs="?",
        help="Zenodo record ID, DOI, or record URL",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing values interactively",
    )
    parser.add_argument(
        "--list-taxonomies",
        action="store_true",
        help="Print allowed taxonomy IDs for domains, collaboration types, scales, modalities, and research methods",
    )
    parser.add_argument(
        "--entry-id",
        help="Existing or new CollabAtlas dataset ID. Defaults to a slug from the Zenodo title.",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        choices=DOMAIN_IDS,
        help="Required for new entries: one or more CollabAtlas domain IDs",
    )
    parser.add_argument(
        "--collaboration-types",
        dest="collaboration_types",
        nargs="+",
        choices=COLLAB_TYPE_IDS,
        help="Required for new entries: one or more collaboration type IDs",
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        choices=SCALE_IDS,
        help="Required for new entries: one or more scale IDs",
    )
    parser.add_argument(
        "--modalities",
        nargs="+",
        choices=MODALITY_IDS,
        help="Required for new entries: one or more modality IDs",
    )
    parser.add_argument(
        "--maturity",
        default="established",
        choices=["emerging", "established", "well-documented"],
        help="Default maturity for newly created entries",
    )
    parser.add_argument(
        "--contributors",
        nargs="+",
        default=["collabatlas-team"],
        help="Contributor names for newly created entries",
    )
    parser.add_argument(
        "--status",
        default="draft",
        choices=["draft", "published", "archived"],
        help="Publication status for newly created entries",
    )
    parser.add_argument(
        "--research-methods",
        nargs="+",
        choices=RESEARCH_METHOD_IDS,
        help="Optional research method IDs for newly created entries",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the parsed dataset without writing files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_taxonomies:
        print_taxonomy_options()
        return

    interactive = args.interactive or not args.identifier
    if interactive:
        args = run_interactive_setup(args)

    if not args.identifier:
        print("A Zenodo record identifier is required.", file=sys.stderr)
        sys.exit(1)

    try:
        record = fetch_zenodo_record(args.identifier)
    except Exception as exc:
        print(f"Zenodo fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)

    parsed = parse_zenodo_dataset(record)
    suggested_entry_id = args.entry_id or slugify(parsed["title"])
    if interactive:
        print(f"\nZenodo title: {parsed['title']}")
        entry_id = prompt_text(
            "CollabAtlas entry id",
            default=suggested_entry_id,
            required=True,
        )
    else:
        entry_id = suggested_entry_id

    existing = load_dataset_entry(entry_id)

    if existing:
        if interactive:
            print(f"Updating existing dataset entry '{entry_id}'.")
        merged = merge_dataset_metadata(existing, parsed)
        merged["last_reviewed"] = date.today().isoformat()
        body = load_markdown_body(entry_id)
    else:
        if interactive:
            print("Creating a new dataset entry. Please map it to CollabAtlas taxonomies.")
            if not args.domains:
                args.domains = prompt_multi_choice("Domains", DOMAINS, required=True)
            if not args.collaboration_types:
                args.collaboration_types = prompt_multi_choice(
                    "Collaboration types",
                    COLLAB_TYPES,
                    required=True,
                )
            if not args.scales:
                args.scales = prompt_multi_choice("Scales", SCALES, required=True)
            if not args.modalities:
                args.modalities = prompt_multi_choice(
                    "Modalities",
                    MODALITIES,
                    required=True,
                )
            if not args.research_methods:
                args.research_methods = prompt_multi_choice(
                    "Research methods (optional)",
                    RESEARCH_METHODS,
                    required=False,
                )
            args.maturity = prompt_single_choice(
                "Maturity",
                MATURITY_OPTIONS,
                default=args.maturity,
            )
            args.status = prompt_single_choice(
                "Status",
                STATUS_OPTIONS,
                default=args.status,
            )
            args.contributors = prompt_contributors(args.contributors)

        required_args = {
            "domains": args.domains,
            "collaboration_types": args.collaboration_types,
            "scales": args.scales,
            "modalities": args.modalities,
        }
        missing = [name for name, value in required_args.items() if not value]
        if missing:
            print(
                "Creating a new dataset entry requires: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing),
                file=sys.stderr,
            )
            sys.exit(1)
        merged = build_new_entry(parsed, entry_id, args)
        body = ""

    if interactive and not args.dry_run:
        args.dry_run = prompt_yes_no("Preview only without writing files", default=False)

    if args.dry_run:
        import yaml

        print(yaml.dump(merged, allow_unicode=True, sort_keys=False))
        return

    write_dataset_files(merged, body=body)
    print(f"Saved dataset entry: {DATASET_DATA_DIR / (entry_id + '.yaml')}")


if __name__ == "__main__":
    main()
