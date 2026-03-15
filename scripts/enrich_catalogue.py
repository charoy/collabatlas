#!/usr/bin/env python3
"""
enrich_catalogue.py — Enrich existing tools and resources with GitHub metrics.

Scans data/entries/tools/*.yaml and data/entries/resources/*.yaml.
If `github_repo` is set (or can be inferred), fetches stars, forks, issues, and last commit date.
Updates the YAML file in place.
"""

import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

# Adjust path to import utility modules
sys.path.append(str(Path(__file__).parent))

from tool_utils import load_tool_entry, write_tool_files, load_markdown_body as load_tool_body
from resource_utils import load_resource_entry, write_resource_files, load_markdown_body as load_resource_body
from dataset_utils import load_dataset_entry, write_dataset_files, load_markdown_body as load_dataset_body

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "data" / "entries" / "tools"
RESOURCES_DIR = ROOT / "data" / "entries" / "resources"
DATASETS_DIR = ROOT / "data" / "entries" / "datasets"

GITHUB_API_URL = "https://api.github.com/repos/{}"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_github_headers():
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    return {"Accept": "application/vnd.github.v3+json"}


def fetch_repo_info(repo_slug):
    """Fetch repository metadata from GitHub API."""
    url = GITHUB_API_URL.format(repo_slug)
    try:
        response = requests.get(url, headers=get_github_headers(), timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"  Warning: Repository {repo_slug} not found (404).")
            return None
        elif response.status_code == 403:
            print(f"  Warning: Rate limit exceeded or forbidden for {repo_slug}.")
            return None
        else:
            print(f"  Error: {response.status_code} fetching {repo_slug}.")
            return None
    except requests.RequestException as e:
        print(f"  Error: Exception fetching {repo_slug}: {e}")
        return None


def extract_repo_slug(entry):
    """Return 'owner/repo' if available in entry."""
    if entry.get("github_repo"):
        return entry["github_repo"]
    
    # Collect potential URLs
    urls = [entry.get("website_url"), entry.get("source_url")]
    
    # Check external_links
    if "external_links" in entry:
        for link in entry["external_links"]:
            if isinstance(link, dict) and "url" in link:
                urls.append(link["url"])
    
    for url in urls:
        if url and "github.com/" in url:
            # Match github.com/owner/repo but ignore extra paths like /issues, /blob, etc.
            match = re.search(r"github\.com/([^/]+/[^/]+)", url)
            if match:
                slug = match.group(1)
                # Remove .git suffix if present
                if slug.endswith(".git"):
                    slug = slug[:-4]
                # Remove trailing slash if present
                if slug.endswith('/'):
                    slug = slug[:-1]
                return slug
    return None


def enrich_entry(entry_id, entry_type):
    """Load entry, fetch stats, and update if changed."""
    if entry_type == "tool":
        data = load_tool_entry(entry_id)
        body = load_tool_body(entry_id)
        writer = write_tool_files
    elif entry_type == "resource":
        data = load_resource_entry(entry_id)
        body = load_resource_body(entry_id)
        writer = write_resource_files
    else:  # dataset
        data = load_dataset_entry(entry_id)
        body = load_dataset_body(entry_id)
        writer = write_dataset_files

    if not data:
        return

    repo_slug = extract_repo_slug(data)
    if not repo_slug:
        return

    print(f"Enriching {entry_type}/{entry_id} ({repo_slug})...")
    repo_data = fetch_repo_info(repo_slug)
    if not repo_data:
        return

    # metrics
    metrics = {
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "last_commit": (repo_data.get("pushed_at") or "")[:10]
    }

    # Only update if changed (simple check)
    old_metrics = data.get("metrics", {})
    if old_metrics == metrics and data.get("github_repo") == repo_slug:
        print("  No changes.")
        return

    # Update fields
    data["metrics"] = metrics
    data["github_repo"] = repo_slug
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    
    # Also update visibility/license if missing
    if "visibility" not in data:
        data["visibility"] = "private" if repo_data.get("private") else "public"
    
    if "license" not in data and repo_data.get("license"):
        data["license"] = repo_data["license"].get("spdx_id") or repo_data["license"].get("name")

    # Save
    writer(data, body)
    print("  Updated.")
    time.sleep(1) # Be nice to API


def main():
    print("Starting catalogue enrichment...")
    
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set. Rate limits will be low.")

    # Process Tools
    if TOOLS_DIR.exists():
        for f in sorted(TOOLS_DIR.glob("*.yaml")):
            enrich_entry(f.stem, "tool")

    # Process Resources
    if RESOURCES_DIR.exists():
        for f in sorted(RESOURCES_DIR.glob("*.yaml")):
            enrich_entry(f.stem, "resource")
            
    # Process Datasets
    if DATASETS_DIR.exists():
        for f in sorted(DATASETS_DIR.glob("*.yaml")):
            enrich_entry(f.stem, "dataset")

    print("Done.")


if __name__ == "__main__":
    main()
