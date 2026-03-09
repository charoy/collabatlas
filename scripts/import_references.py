#!/usr/bin/env python3
"""
import_references.py — Import research articles from BibTeX, RIS, or
OpenAlex / Zotero sources.

Usage:
    python scripts/import_references.py --bibtex refs.bib
    python scripts/import_references.py --ris export.ris
    python scripts/import_references.py --bibtex refs.bib --enrich
    python scripts/import_references.py --bibtex refs.bib --dry-run
    python scripts/import_references.py --openalex-ids ids.txt
    python scripts/import_references.py --zotero-library groups/123456
"""

import argparse
import sys
import time
from pathlib import Path

from article_utils import (
    RATE_LIMIT,
    fetch_zotero_library,
    fetch_by_openalex_id,
    fetch_metadata,
    load_articles,
    lookup_doi_by_title,
    parse_csl_json_items,
    save_articles,
    upsert,
)


# ── Parsers ──────────────────────────────────────────────────────────────────


def merge_enriched_fields(entry: dict, enriched: dict) -> None:
    """Merge enrichment data into an imported entry without losing provenance."""
    for key, val in enriched.items():
        if val is None:
            continue

        if key in {"source_services", "orcid_ids"}:
            merged = []
            for item in (entry.get(key) or []) + (val or []):
                if item and item not in merged:
                    merged.append(item)
            if merged:
                entry[key] = merged
            continue

        if key == "citation_count":
            current = entry.get(key)
            if current is None or val > current:
                entry[key] = val
            continue

        if key == "access":
            if val == "open" or not entry.get(key) or entry.get(key) == "unknown":
                entry[key] = val
            continue

        if key == "fetched_at" or not entry.get(key):
            entry[key] = val


def parse_bibtex(filepath: Path) -> list[dict]:
    """Parse a BibTeX file and return normalised article dicts."""
    import bibtexparser

    with open(filepath, encoding="utf-8") as f:
        bib_database = bibtexparser.load(f)

    articles = []
    for entry in bib_database.entries:
        # bibtexparser v1.x returns dicts directly
        authors_raw = entry.get("author", "")
        if authors_raw:
            author_list = [
                a.strip()
                for a in authors_raw.replace("\n", " ").split(" and ")
            ]
            authors = ", ".join(author_list)
        else:
            authors = None

        year_str = entry.get("year", "")
        try:
            year = int(year_str) if year_str else None
        except ValueError:
            year = None

        doi = entry.get("doi", "").strip()
        url = entry.get("url", "").strip()
        if doi and not url:
            url = f"https://doi.org/{doi}"

        articles.append(
            {
                "title": entry.get("title", "").strip("{}"),
                "authors": authors,
                "journal": (
                    entry.get("journal")
                    or entry.get("booktitle")
                    or entry.get("publisher")
                ),
                "year": year,
                "doi": doi or None,
                "url": url or None,
                "abstract": entry.get("abstract"),
                "access": "unknown",
                "_source_key": entry.get("ID", ""),
            }
        )

    return articles


def parse_ris(filepath: Path) -> list[dict]:
    """Parse a RIS file and return normalised article dicts."""
    import rispy

    with open(filepath, encoding="utf-8") as f:
        entries = rispy.load(f)

    articles = []
    for entry in entries:
        author_list = (
            entry.get("authors") or entry.get("first_authors") or []
        )
        authors = ", ".join(author_list) if author_list else None

        year_str = (
            entry.get("year") or entry.get("publication_year") or ""
        )
        try:
            year = int(year_str) if year_str else None
        except ValueError:
            year = None

        doi = entry.get("doi", "").strip()
        url = entry.get("url", "").strip()
        if doi and not url:
            url = f"https://doi.org/{doi}"

        articles.append(
            {
                "title": (
                    entry.get("title")
                    or entry.get("primary_title")
                    or ""
                ),
                "authors": authors,
                "journal": (
                    entry.get("journal_name")
                    or entry.get("secondary_title")
                    or entry.get("alternate_title3")
                ),
                "year": year,
                "doi": doi or None,
                "url": url or None,
                "abstract": entry.get("abstract"),
                "access": "unknown",
            }
        )

    return articles


def parse_zotero_json(filepath: Path) -> list[dict]:
    """Parse a Zotero CSL JSON export file into normalised article dicts."""
    import json

    with open(filepath, encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError("Zotero JSON export must contain a list of items")

    return parse_csl_json_items(items, source_service="zotero")


# ── OpenAlex ID Import ────────────────────────────────────────────────────────


def import_openalex_ids(filepath: Path, dry_run: bool = False):
    """Import articles from a text file of OpenAlex Work IDs."""
    lines = filepath.read_text(encoding="utf-8").splitlines()
    ids = [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    print(f"Importing {len(ids)} OpenAlex Work IDs from {filepath}\n")

    if not ids:
        print("No IDs to import.")
        return

    articles = load_articles()
    stats = {"added": 0, "updated": 0, "failed": 0}

    for oa_id in ids:
        print(f"\nFetching: {oa_id}")
        meta = fetch_by_openalex_id(oa_id)
        if meta:
            # Remove None values for cleaner YAML
            meta = {k: v for k, v in meta.items() if v is not None}
            before_len = len(articles)
            articles = upsert(articles, meta.get("doi"), meta)
            if len(articles) > before_len:
                stats["added"] += 1
            else:
                stats["updated"] += 1
        else:
            print(f"  Failed to fetch {oa_id}", file=sys.stderr)
            stats["failed"] += 1
        time.sleep(RATE_LIMIT)

    print(f"\n{'='*50}")
    print("OpenAlex import summary:")
    print(f"  IDs read: {len(ids)}")
    print(f"  Added:    {stats['added']}")
    print(f"  Updated:  {stats['updated']}")
    print(f"  Failed:   {stats['failed']}")
    print(f"  Total:    {len(articles)} articles")

    if dry_run:
        print("\n  DRY RUN — no changes written.")
    else:
        save_articles(articles)


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Import research articles from BibTeX, RIS, Zotero, or OpenAlex "
            "into CollabAtlas"
        ),
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--bibtex", "-b", type=Path, help="BibTeX file to import"
    )
    input_group.add_argument(
        "--ris", "-r", type=Path, help="RIS file to import"
    )
    input_group.add_argument(
        "--openalex-ids",
        "-o",
        type=Path,
        help="Text file with one OpenAlex Work ID per line",
    )
    input_group.add_argument(
        "--zotero-json",
        type=Path,
        help="Zotero CSL JSON export file to import",
    )
    input_group.add_argument(
        "--zotero-library",
        help="Zotero library identifier like groups/123456 or users/123456",
    )

    parser.add_argument(
        "--enrich",
        "-e",
        action="store_true",
        help=(
            "Enrich entries with metadata from OpenAlex / CrossRef "
            "(requires DOI or title lookup)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without writing to the articles file",
    )
    parser.add_argument(
        "--zotero-api-key",
        help="Optional Zotero API key for private libraries or higher limits",
    )
    parser.add_argument(
        "--zotero-tag",
        help="Optional Zotero tag filter when using --zotero-library",
    )
    parser.add_argument(
        "--zotero-limit",
        type=int,
        default=100,
        help="Maximum number of items to request from a Zotero library",
    )
    args = parser.parse_args()

    # ── Parse input file ─────────────────────────────────────────────────
    if args.openalex_ids:
        if not args.openalex_ids.exists():
            print(f"File not found: {args.openalex_ids}", file=sys.stderr)
            sys.exit(1)
        import_openalex_ids(args.openalex_ids, dry_run=args.dry_run)
        return

    if args.zotero_library:
        print(f"Fetching Zotero library: {args.zotero_library}")
        try:
            parsed = fetch_zotero_library(
                args.zotero_library,
                api_key=args.zotero_api_key,
                tag=args.zotero_tag,
                limit=args.zotero_limit,
            )
        except Exception as exc:
            print(f"Zotero import failed: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.zotero_json:
        if not args.zotero_json.exists():
            print(f"File not found: {args.zotero_json}", file=sys.stderr)
            sys.exit(1)
        print(f"Parsing Zotero JSON: {args.zotero_json}")
        try:
            parsed = parse_zotero_json(args.zotero_json)
        except Exception as exc:
            print(f"Invalid Zotero JSON: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.bibtex:
        if not args.bibtex.exists():
            print(f"File not found: {args.bibtex}", file=sys.stderr)
            sys.exit(1)
        print(f"Parsing BibTeX: {args.bibtex}")
        parsed = parse_bibtex(args.bibtex)
    else:
        if not args.ris.exists():
            print(f"File not found: {args.ris}", file=sys.stderr)
            sys.exit(1)
        print(f"Parsing RIS: {args.ris}")
        parsed = parse_ris(args.ris)

    print(f"Found {len(parsed)} entries\n")

    if not parsed:
        print("No entries to import.")
        return

    articles = load_articles()
    stats = {"added": 0, "updated": 0, "enriched": 0, "skipped": 0}

    for entry in parsed:
        title = entry.get("title", "")
        doi = entry.get("doi")

        # Remove internal-only fields
        entry.pop("_source_key", None)

        # ── Optional enrichment ──────────────────────────────────────────
        if args.enrich:
            if doi:
                print(f"\nEnriching: {title[:60]}...")
                enriched = fetch_metadata(doi)
                if enriched:
                    merge_enriched_fields(entry, enriched)
                    stats["enriched"] += 1
                time.sleep(RATE_LIMIT)
            else:
                print(f"\nLooking up DOI for: {title[:60]}...")
                found_doi = lookup_doi_by_title(title, entry.get("authors"))
                if found_doi:
                    print(f"  Found DOI: {found_doi}")
                    entry["doi"] = found_doi
                    enriched = fetch_metadata(found_doi)
                    if enriched:
                        merge_enriched_fields(entry, enriched)
                        stats["enriched"] += 1
                else:
                    print("  No DOI found")
                time.sleep(RATE_LIMIT)

        # Remove None values for cleaner YAML output
        entry = {k: v for k, v in entry.items() if v is not None}

        if not entry.get("title"):
            stats["skipped"] += 1
            continue

        doi = entry.get("doi")

        before_len = len(articles)
        articles = upsert(articles, doi, entry)
        if len(articles) > before_len:
            stats["added"] += 1
        else:
            stats["updated"] += 1

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print("Import summary:")
    print(f"  Parsed:   {len(parsed)}")
    print(f"  Added:    {stats['added']}")
    print(f"  Updated:  {stats['updated']}")
    print(f"  Enriched: {stats['enriched']}")
    print(f"  Skipped:  {stats['skipped']}")
    print(f"  Total:    {len(articles)} articles")

    if args.dry_run:
        print("\n  DRY RUN — no changes written.")
    else:
        save_articles(articles)


if __name__ == "__main__":
    main()
