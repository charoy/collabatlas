#!/usr/bin/env python3
"""Shared utilities for CollabAtlas research article management."""

import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_FILE = ROOT / "data" / "research_articles.yaml"

CROSSREF_URL = "https://api.crossref.org/works/{doi}"
CROSSREF_SEARCH_URL = "https://api.crossref.org/works"
OPENALEX_URL = "https://api.openalex.org/works/doi:{doi}"
OPENALEX_ID_URL = "https://api.openalex.org/works/{openalex_id}"
HEADERS = {"User-Agent": "CollabAtlas/1.0 (mailto:admin@collabatlas.org)"}
RATE_LIMIT = 0.5  # seconds between API calls


# ── Data I/O ─────────────────────────────────────────────────────────────────


def load_articles() -> list:
    """Load articles from the YAML data file."""
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def save_articles(articles: list):
    """Save articles to the YAML data file."""
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        yaml.dump(
            articles, f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    print(f"Saved {len(articles)} articles to {ARTICLES_FILE}")


# ── ID Generation ────────────────────────────────────────────────────────────


def generate_id(
    authors: str | None, year: int | None, existing_ids: set[str]
) -> str:
    """Generate a unique article ID from first author surname + year."""
    first_author = (authors or "unknown").split(",")[0].split()[-1].lower()
    first_author = re.sub(r"[^a-z0-9]", "", first_author)
    yr = year or "xxxx"
    new_id = f"{first_author}-{yr}"
    base_id, n = new_id, 2
    while new_id in existing_ids:
        new_id = f"{base_id}-{n}"
        n += 1
    return new_id


# ── Upsert ───────────────────────────────────────────────────────────────────

PRESERVED_FIELDS = ("id", "domains", "tags", "related_entries", "notes")


def upsert(articles: list, doi: str | None, meta: dict) -> list:
    """Update existing entry or append new one, preserving manual fields."""
    if doi:
        doi_clean = doi.strip().lower()
        for i, art in enumerate(articles):
            if art.get("doi", "").lower() == doi_clean:
                preserved = {
                    k: v for k, v in art.items() if k in PRESERVED_FIELDS
                }
                articles[i] = {**meta, **preserved}
                print(f"  Updated: {meta.get('title', doi)[:70]}")
                return articles

    # Check by title match
    title_lower = (meta.get("title") or "").lower().strip()
    if title_lower:
        for i, art in enumerate(articles):
            if (art.get("title") or "").lower().strip() == title_lower:
                preserved = {
                    k: v for k, v in art.items() if k in PRESERVED_FIELDS
                }
                articles[i] = {**meta, **preserved}
                print(f"  Updated (title match): {meta.get('title', '')[:70]}")
                return articles

    # New entry
    existing_ids = {a.get("id") for a in articles}
    new_id = generate_id(meta.get("authors"), meta.get("year"), existing_ids)
    articles.append({"id": new_id, **meta})
    print(f"  Added:   {meta.get('title', '')[:70]}")
    return articles


# ── CrossRef ─────────────────────────────────────────────────────────────────


def fetch_crossref(doi: str) -> dict | None:
    """Fetch article metadata from CrossRef by DOI."""
    url = CROSSREF_URL.format(doi=doi)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("message", {})
    except Exception as e:
        print(f"  CrossRef error for {doi}: {e}", file=sys.stderr)
        return None

    authors = []
    for a in data.get("author", []):
        given = a.get("given", "")
        family = a.get("family", "")
        if family:
            authors.append(f"{given} {family}".strip())

    container = (
        data.get("container-title", [None])[0]
        or data.get("publisher")
        or ""
    )

    issued = data.get("issued", {}).get("date-parts", [[None]])[0]
    year = issued[0] if issued else None

    abstract = data.get("abstract", "")
    if abstract:
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()

    license_list = data.get("license", [])
    access = "open" if license_list else "unknown"

    return {
        "title": data.get("title", [doi])[0],
        "authors": ", ".join(authors) if authors else None,
        "journal": container or None,
        "year": year,
        "doi": doi,
        "url": data.get("URL") or f"https://doi.org/{doi}",
        "access": access,
        "abstract": abstract or None,
        "citation_count": data.get("is-referenced-by-count"),
    }


# ── OpenAlex ─────────────────────────────────────────────────────────────────


def _parse_openalex_response(data: dict) -> dict:
    """Parse an OpenAlex Work response into a normalised article dict."""
    authors = []
    for a in data.get("authorships", []):
        name = a.get("author", {}).get("display_name")
        if name:
            authors.append(name)

    venue = data.get("primary_location", {}) or {}
    source = venue.get("source") or {}
    journal = source.get("display_name") or data.get(
        "host_venue", {}
    ).get("display_name")

    year = data.get("publication_year")
    abstract_inv = data.get("abstract_inverted_index")
    abstract = _reconstruct_abstract(abstract_inv) if abstract_inv else None

    oa_info = data.get("open_access", {})
    access = "open" if oa_info.get("is_oa") else "paid"

    doi = data.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    url = oa_info.get("oa_url")
    if not url and doi:
        url = f"https://doi.org/{doi}"
    if not url:
        url = data.get("id")  # OpenAlex URL as fallback

    return {
        "title": data.get("title"),
        "authors": ", ".join(authors) if authors else None,
        "journal": journal or None,
        "year": year,
        "doi": doi or None,
        "url": url,
        "access": access,
        "abstract": abstract,
        "citation_count": data.get("cited_by_count"),
        "openalex_id": data.get("id"),
    }


def fetch_openalex(doi: str) -> dict | None:
    """Fetch article metadata from OpenAlex by DOI."""
    url = OPENALEX_URL.format(doi=doi)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  OpenAlex error for {doi}: {e}", file=sys.stderr)
        return None

    result = _parse_openalex_response(data)
    # Ensure DOI is set even if OpenAlex response lacks it
    if not result.get("doi"):
        result["doi"] = doi
    return result


def fetch_by_openalex_id(openalex_id: str) -> dict | None:
    """Fetch article metadata from OpenAlex by Work ID (e.g. W54955629)."""
    # Strip URL prefix if present
    if openalex_id.startswith("https://openalex.org/"):
        openalex_id = openalex_id.replace("https://openalex.org/", "")
    url = OPENALEX_ID_URL.format(openalex_id=openalex_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  OpenAlex error for {openalex_id}: {e}", file=sys.stderr)
        return None

    return _parse_openalex_response(data)


def _reconstruct_abstract(inv_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index."""
    positions = {}
    for word, pos_list in inv_index.items():
        for pos in pos_list:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions))


# ── Combined Fetcher ─────────────────────────────────────────────────────────


def fetch_metadata(doi: str) -> dict | None:
    """Try OpenAlex first (richer OA info), fall back to CrossRef."""
    print(f"  Fetching {doi} via OpenAlex...")
    meta = fetch_openalex(doi)
    if not meta or not meta.get("title"):
        print(f"  Falling back to CrossRef...")
        meta = fetch_crossref(doi)
    return meta


# ── DOI Lookup ───────────────────────────────────────────────────────────────


def lookup_doi_by_title(
    title: str, author: str | None = None
) -> str | None:
    """Search CrossRef for a DOI by title (and optionally author)."""
    params = {"query.bibliographic": title, "rows": 3}
    if author:
        params["query.author"] = author.split(",")[0].strip()
    try:
        r = requests.get(
            CROSSREF_SEARCH_URL, params=params, headers=HEADERS, timeout=10
        )
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        if items:
            result_title = (items[0].get("title", [""])[0] or "").lower()
            if _title_similarity(title.lower(), result_title) > 0.8:
                return items[0].get("DOI")
    except Exception as e:
        print(f"  CrossRef search error: {e}", file=sys.stderr)
    return None


def _title_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity between two titles."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / max(len(words_a), len(words_b))
