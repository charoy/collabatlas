#!/usr/bin/env python3
"""
fetch_doi.py — Fetch article metadata from CrossRef or OpenAlex by DOI
and upsert into data/research_articles.yaml.

Usage:
    python scripts/fetch_doi.py 10.1145/175222.175230
    python scripts/fetch_doi.py --file dois.txt
    python scripts/fetch_doi.py --all
    python scripts/fetch_doi.py --enrich-missing
    python scripts/fetch_doi.py --lookup-doi
    python scripts/fetch_doi.py --openalex W54955629
"""

import argparse
import sys
import time
from pathlib import Path

from article_utils import (
    RATE_LIMIT,
    fetch_by_openalex_id,
    fetch_metadata,
    load_articles,
    lookup_doi_by_title,
    save_articles,
    upsert,
)


def process_dois(dois: list[str]):
    """Fetch metadata for a list of DOIs and upsert into articles."""
    articles = load_articles()
    for doi in dois:
        doi = doi.strip()
        if not doi or doi.startswith("#"):
            continue
        print(f"\nProcessing DOI: {doi}")
        meta = fetch_metadata(doi)
        if meta:
            articles = upsert(articles, doi, meta)
        else:
            print(f"  Could not fetch metadata for {doi}", file=sys.stderr)
        time.sleep(RATE_LIMIT)
    save_articles(articles)


def enrich_missing():
    """Enrich existing articles that have a DOI but lack key metadata."""
    articles = load_articles()
    enriched_count = 0

    for i, art in enumerate(articles):
        doi = art.get("doi")
        if not doi:
            continue

        missing = []
        if not art.get("abstract"):
            missing.append("abstract")
        if art.get("citation_count") is None:
            missing.append("citation_count")
        if not art.get("openalex_id"):
            missing.append("openalex_id")
        if not missing:
            continue

        title_short = art.get("title", doi)[:60]
        print(
            f"\nEnriching '{title_short}' — missing: {', '.join(missing)}"
        )
        meta = fetch_metadata(doi)
        if meta:
            for field in missing:
                if meta.get(field) is not None:
                    articles[i][field] = meta[field]
            enriched_count += 1
        time.sleep(RATE_LIMIT)

    print(f"\n{'='*50}")
    print(f"Enriched {enriched_count} articles")
    save_articles(articles)


def lookup_missing_dois():
    """For articles without DOIs, attempt CrossRef title search."""
    articles = load_articles()
    found_count = 0

    for i, art in enumerate(articles):
        if art.get("doi"):
            continue
        title = art.get("title", "")
        if not title:
            continue

        print(f"\nLooking up DOI for: {title[:60]}...")
        doi = lookup_doi_by_title(title, art.get("authors"))
        if doi:
            print(f"  Found: {doi}")
            articles[i]["doi"] = doi
            articles[i]["url"] = (
                articles[i].get("url") or f"https://doi.org/{doi}"
            )
            found_count += 1
        else:
            print("  Not found")
        time.sleep(RATE_LIMIT)

    print(f"\n{'='*50}")
    print(f"Found DOIs for {found_count} articles")
    save_articles(articles)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch DOI metadata into research_articles.yaml"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("doi", nargs="?", help="Single DOI to fetch")
    group.add_argument(
        "--file", "-f", help="Text file with one DOI per line"
    )
    group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Refresh metadata for all existing entries that have a DOI",
    )
    group.add_argument(
        "--enrich-missing",
        action="store_true",
        help=(
            "Enrich existing articles that have DOI "
            "but lack abstract/citations/OpenAlex ID"
        ),
    )
    group.add_argument(
        "--lookup-doi",
        action="store_true",
        help=(
            "Find DOIs for articles that don't have one "
            "(via CrossRef title search)"
        ),
    )
    group.add_argument(
        "--openalex",
        help=(
            "OpenAlex Work ID to import "
            "(e.g. W54955629 or https://openalex.org/W54955629)"
        ),
    )
    args = parser.parse_args()

    if args.doi:
        process_dois([args.doi])
    elif args.file:
        dois = Path(args.file).read_text(encoding="utf-8").splitlines()
        process_dois(dois)
    elif args.all:
        articles = load_articles()
        dois = [a["doi"] for a in articles if a.get("doi")]
        print(f"Refreshing {len(dois)} existing DOIs...")
        process_dois(dois)
    elif args.enrich_missing:
        enrich_missing()
    elif args.lookup_doi:
        lookup_missing_dois()
    elif args.openalex:
        process_openalex_id(args.openalex)


def process_openalex_id(openalex_id: str):
    """Fetch metadata by OpenAlex Work ID and upsert into articles."""
    articles = load_articles()
    print(f"\nFetching OpenAlex Work: {openalex_id}")
    meta = fetch_by_openalex_id(openalex_id)
    if meta:
        # Remove None values for cleaner YAML output
        meta = {k: v for k, v in meta.items() if v is not None}
        articles = upsert(articles, meta.get("doi"), meta)
        save_articles(articles)
    else:
        print(
            f"Could not fetch metadata for {openalex_id}", file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
