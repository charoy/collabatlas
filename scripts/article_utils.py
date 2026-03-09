#!/usr/bin/env python3
"""Shared utilities for CollabAtlas research article management."""

from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_FILE = ROOT / "data" / "research_articles.yaml"

CROSSREF_URL = "https://api.crossref.org/works/{doi}"
CROSSREF_SEARCH_URL = "https://api.crossref.org/works"
OPENALEX_URL = "https://api.openalex.org/works/doi:{doi}"
OPENALEX_ID_URL = "https://api.openalex.org/works/{openalex_id}"
ZOTERO_API_ROOT = "https://api.zotero.org"
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


def _merge_unique_str_list(*values: list[str] | None) -> list[str]:
    """Merge multiple string lists while preserving order and uniqueness."""
    merged = []
    for items in values:
        for item in items or []:
            if item and item not in merged:
                merged.append(item)
    return merged


def _normalize_orcid(value: str | None) -> str | None:
    """Normalise an ORCID value to the canonical HTTPS URL form."""
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    value = value.replace("http://orcid.org/", "")
    value = value.replace("https://orcid.org/", "")
    value = value.replace("orcid.org/", "")

    if re.fullmatch(r"\d{4}-\d{4}-\d{4}-[\dX]{4}", value, re.I):
        return f"https://orcid.org/{value.upper()}"
    return None


def _merge_metadata(primary: dict | None, secondary: dict | None) -> dict:
    """Merge two metadata dictionaries, preferring richer primary values."""
    primary = dict(primary or {})
    secondary = dict(secondary or {})
    merged = dict(secondary)
    merged.update(primary)

    merged["source_services"] = _merge_unique_str_list(
        secondary.get("source_services"), primary.get("source_services")
    )
    merged["orcid_ids"] = _merge_unique_str_list(
        secondary.get("orcid_ids"), primary.get("orcid_ids")
    )

    if primary.get("citation_count") is not None or secondary.get("citation_count") is not None:
        merged["citation_count"] = max(
            [
                value
                for value in (
                    primary.get("citation_count"),
                    secondary.get("citation_count"),
                )
                if value is not None
            ],
            default=None,
        )

    if "open" in {primary.get("access"), secondary.get("access")}:
        merged["access"] = "open"
    elif primary.get("access") or secondary.get("access"):
        merged["access"] = primary.get("access") or secondary.get("access")

    for key in ("title", "authors", "journal", "year", "doi", "url", "abstract"):
        if not merged.get(key):
            merged[key] = primary.get(key) or secondary.get(key)

    return {k: v for k, v in merged.items() if v not in (None, [], "")}


def _current_timestamp() -> str:
    """Return a UTC timestamp suitable for persisted enrichment metadata."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def upsert(articles: list, doi: str | None, meta: dict) -> list:
    """Update existing entry or append new one, preserving manual fields."""
    if doi:
        doi_clean = doi.strip().lower()
        for i, art in enumerate(articles):
            if art.get("doi", "").lower() == doi_clean:
                preserved = {
                    k: v for k, v in art.items() if k in PRESERVED_FIELDS
                }
                articles[i] = _merge_metadata({**meta, **preserved}, art)
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
                articles[i] = _merge_metadata({**meta, **preserved}, art)
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
    orcid_ids = []
    for a in data.get("author", []):
        given = a.get("given", "")
        family = a.get("family", "")
        if family:
            authors.append(f"{given} {family}".strip())
        orcid = _normalize_orcid(a.get("ORCID"))
        if orcid:
            orcid_ids.append(orcid)

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
        "orcid_ids": _merge_unique_str_list(orcid_ids),
        "source_services": ["crossref"],
    }


# ── OpenAlex ─────────────────────────────────────────────────────────────────


def _parse_openalex_response(data: dict) -> dict:
    """Parse an OpenAlex Work response into a normalised article dict."""
    authors = []
    orcid_ids = []
    for a in data.get("authorships", []):
        author = a.get("author", {})
        name = author.get("display_name")
        if name:
            authors.append(name)
        orcid = _normalize_orcid(author.get("orcid"))
        if orcid:
            orcid_ids.append(orcid)

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
        "orcid_ids": _merge_unique_str_list(orcid_ids),
        "source_services": ["openalex"],
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

    result = _parse_openalex_response(data)
    if result:
        result["fetched_at"] = _current_timestamp()
    return result


def _reconstruct_abstract(inv_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index."""
    positions = {}
    for word, pos_list in inv_index.items():
        for pos in pos_list:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions))


# ── Combined Fetcher ─────────────────────────────────────────────────────────


def fetch_metadata(doi: str) -> dict | None:
    """Merge OpenAlex and CrossRef metadata for richer enrichment."""
    print(f"  Fetching {doi} via OpenAlex...")
    openalex_meta = fetch_openalex(doi)

    print(f"  Fetching {doi} via CrossRef...")
    crossref_meta = fetch_crossref(doi)

    if not openalex_meta and not crossref_meta:
        return None

    meta = _merge_metadata(openalex_meta, crossref_meta)
    meta["fetched_at"] = _current_timestamp()
    return meta


def _extract_csl_year(item: dict) -> int | None:
    """Extract a publication year from CSL JSON date fields."""
    for field in ("issued", "published-print", "published-online"):
        date_info = item.get(field) or {}
        date_parts = date_info.get("date-parts") or []
        if date_parts and date_parts[0]:
            year = date_parts[0][0]
            if isinstance(year, int):
                return year
            try:
                return int(year)
            except (TypeError, ValueError):
                return None
    return None


def parse_csl_json_items(
    items: list[dict[str, Any]], source_service: str = "zotero"
) -> list[dict]:
    """Parse CSL JSON items into normalised article dictionaries."""
    parsed = []
    for item in items:
        author_names = []
        orcid_ids = []
        for author in item.get("author", []):
            literal = (author.get("literal") or "").strip()
            if literal:
                author_names.append(literal)
            else:
                given = (author.get("given") or "").strip()
                family = (author.get("family") or "").strip()
                full_name = " ".join(part for part in (given, family) if part)
                if full_name:
                    author_names.append(full_name)

            orcid = _normalize_orcid(
                author.get("ORCID") or author.get("orcid")
            )
            if orcid:
                orcid_ids.append(orcid)

        doi = (item.get("DOI") or "").strip() or None
        url = (item.get("URL") or "").strip() or None
        if doi and not url:
            url = f"https://doi.org/{doi}"

        parsed.append(
            {
                "title": (item.get("title") or "").strip(),
                "authors": ", ".join(author_names) if author_names else None,
                "journal": (
                    item.get("container-title")
                    or item.get("publisher")
                    or item.get("collection-title")
                ),
                "year": _extract_csl_year(item),
                "doi": doi,
                "url": url,
                "abstract": item.get("abstract") or None,
                "access": "unknown",
                "orcid_ids": _merge_unique_str_list(orcid_ids),
                "source_services": [source_service],
                "fetched_at": _current_timestamp(),
            }
        )

    return parsed


def fetch_zotero_library(
    library: str,
    api_key: str | None = None,
    tag: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch items from a Zotero library using its public API."""
    parts = [part.strip() for part in library.split("/") if part.strip()]
    if len(parts) != 2 or parts[0] not in {"users", "groups"}:
        raise ValueError(
            "Zotero library must look like 'users/<id>' or 'groups/<id>'"
        )

    headers = dict(HEADERS)
    if api_key:
        headers["Zotero-API-Key"] = api_key

    params = {
        "format": "csljson",
        "itemType": "-attachment",
        "limit": limit,
    }
    if tag:
        params["tag"] = tag

    url = f"{ZOTERO_API_ROOT}/{parts[0]}/{parts[1]}/items"
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    items = response.json()
    if not isinstance(items, list):
        raise ValueError("Unexpected Zotero API response format")

    return parse_csl_json_items(items, source_service="zotero")


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
