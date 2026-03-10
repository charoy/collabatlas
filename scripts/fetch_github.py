#!/usr/bin/env python3
"""Import or enrich CollabAtlas tool or resource entries from GitHub."""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime, timezone

import requests
import yaml

from resource_utils import (
    RESOURCE_DATA_DIR,
    load_markdown_body as load_resource_body,
    load_resource_entry,
    merge_resource_metadata,
    slugify as slugify_resource,
    write_resource_files,
)
from tool_utils import (
    TOOL_DATA_DIR,
    load_markdown_body as load_tool_body,
    load_taxonomy_records,
    load_tool_entry,
    merge_tool_metadata,
    slugify as slugify_tool,
    write_tool_files,
)

GITHUB_API_ROOT = "https://api.github.com"
USER_AGENT = "CollabAtlas/1.0 (mailto:admin@collabatlas.org)"

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

ENTRY_TYPE_OPTIONS = ["tool", "resource"]
RESOURCE_TYPE_OPTIONS = ["article", "book", "course", "video", "tutorial", "report"]
MATURITY_OPTIONS = ["emerging", "established", "well-documented"]
STATUS_OPTIONS = ["draft", "published", "archived"]
ACCESS_OPTIONS = ["open", "restricted", "paid"]


def current_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def github_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def normalize_repo_identifier(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://github\.com/", "", value)
    value = value.strip("/")
    if value.endswith(".git"):
        value = value[:-4]
    parts = [part for part in value.split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub repository must look like 'owner/repo' or a GitHub URL")
    return f"{parts[0]}/{parts[1]}"


def fetch_github_repo(repo: str, token: str | None = None) -> dict:
    repo = normalize_repo_identifier(repo)
    response = requests.get(
        f"{GITHUB_API_ROOT}/repos/{repo}",
        headers=github_headers(token),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def fetch_readme_url(repo: str, token: str | None = None) -> str | None:
    response = requests.get(
        f"{GITHUB_API_ROOT}/repos/{repo}/readme",
        headers=github_headers(token),
        timeout=20,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json().get("html_url")


def build_tagline(description: str | None, title: str) -> str:
    if description:
        description = description.strip()
        if len(description) <= 200:
            return description
        return description[:197].rstrip() + "..."
    return f"GitHub repository for {title}."[:200]


def parse_license(repo_data: dict) -> str | None:
    license_info = repo_data.get("license") or {}
    return license_info.get("spdx_id") or license_info.get("name") or None


def infer_supported_platforms(repo_data: dict) -> list[str]:
    topics = set(repo_data.get("topics") or [])
    homepage = (repo_data.get("homepage") or "").lower()
    platforms = ["Web"]
    for topic, label in {
        "windows": "Windows",
        "macos": "macOS",
        "linux": "Linux",
        "android": "Android",
        "ios": "iOS",
    }.items():
        if topic in topics and label not in platforms:
            platforms.append(label)
    if any(token in homepage for token in ["appstore", "play.google", "windows", "mac"]):
        for label, checks in {
            "iOS": ["appstore"],
            "Android": ["play.google"],
            "Windows": ["windows"],
            "macOS": ["mac"],
        }.items():
            if any(check in homepage for check in checks) and label not in platforms:
                platforms.append(label)
    return platforms


def read_input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print("\nInteractive input aborted.", file=sys.stderr)
        sys.exit(1)


def prompt_text(label: str, default: str | None = None, required: bool = False) -> str | None:
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


def prompt_single_choice(label: str, options: list[str], default: str | None = None) -> str:
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


def prompt_multi_choice(label: str, records: list[dict], required: bool = False) -> list[str]:
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
    default_text = ", ".join(defaults)
    raw = prompt_text("Contributors (comma-separated)", default=default_text)
    values = [item.strip() for item in (raw or "").split(",") if item.strip()]
    return values or defaults


def prompt_int(label: str, default: int | None = None) -> int | None:
    while True:
        raw = prompt_text(label, default=str(default) if default else None)
        if raw in (None, ""):
            return None
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid integer year.")


def print_taxonomy_options() -> None:
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


def base_external_links(repo_data: dict, repo: str, readme_url: str | None) -> list[dict]:
    homepage = repo_data.get("homepage") or repo_data.get("html_url")
    external_links = [
        {
            "type": "repository",
            "url": repo_data.get("html_url"),
            "title": f"{repo} on GitHub",
        }
    ]
    if homepage and homepage != repo_data.get("html_url"):
        external_links.insert(
            0,
            {
                "type": "website",
                "url": homepage,
                "title": f"{repo_data.get('name')} website",
            },
        )
    if readme_url:
        external_links.append(
            {
                "type": "documentation",
                "url": readme_url,
                "title": f"{repo_data.get('name')} README",
            }
        )
    return external_links


def base_tags(repo_data: dict) -> list[str]:
    topics = [topic for topic in (repo_data.get("topics") or []) if topic]
    language = repo_data.get("language")
    if language and language.lower() not in [topic.lower() for topic in topics]:
        topics.append(language)
    return topics


def parse_github_tool(repo_data: dict, repo: str, readme_url: str | None) -> dict:
    description = repo_data.get("description")
    homepage = repo_data.get("homepage") or repo_data.get("html_url")
    visibility = repo_data.get("visibility") or ("private" if repo_data.get("private") else "public")
    return {
        "type": "tool",
        "title": repo_data.get("name") or repo.split("/", 1)[1],
        "tagline": build_tagline(description, repo_data.get("name") or repo),
        "description": description or f"GitHub repository for {repo}.",
        "website_url": homepage,
        "license": parse_license(repo_data) or ("Proprietary" if repo_data.get("private") else None),
        "open_source": bool(not repo_data.get("private") and parse_license(repo_data)),
        "supported_platforms": infer_supported_platforms(repo_data),
        "external_links": base_external_links(repo_data, repo, readme_url),
        "tags": base_tags(repo_data),
        "source_services": ["github"],
        "fetched_at": current_timestamp(),
        "last_reviewed": date.today().isoformat(),
        "created": (repo_data.get("created_at") or "")[:10] or date.today().isoformat(),
        "github_repo": repo,
        "visibility": visibility,
    }


def parse_github_resource(
    repo_data: dict,
    repo: str,
    readme_url: str | None,
    resource_type: str,
    authors: list[str] | None,
    year: int | None,
    access: str,
) -> dict:
    description = repo_data.get("description")
    owner_name = (repo_data.get("owner") or {}).get("login")
    visibility = repo_data.get("visibility") or ("private" if repo_data.get("private") else "public")
    return {
        "type": "resource",
        "title": repo_data.get("name") or repo.split("/", 1)[1],
        "tagline": build_tagline(description, repo_data.get("name") or repo),
        "description": description or f"GitHub repository for {repo}.",
        "resource_type": resource_type,
        "authors": authors or ([owner_name] if owner_name else []),
        "year": year,
        "access": access,
        "external_links": base_external_links(repo_data, repo, readme_url),
        "tags": base_tags(repo_data),
        "source_services": ["github"],
        "fetched_at": current_timestamp(),
        "last_reviewed": date.today().isoformat(),
        "created": (repo_data.get("created_at") or "")[:10] or date.today().isoformat(),
        "github_repo": repo,
        "visibility": visibility,
    }


def build_new_entry(parsed: dict, entry_id: str, args: argparse.Namespace) -> dict:
    base = {
        "id": entry_id,
        **parsed,
        "domains": args.domains,
        "collaboration-types": args.collaboration_types,
        "scales": args.scales,
        "modalities": args.modalities,
        "maturity": args.maturity,
        "contributors": args.contributors,
        "status": args.status,
    }
    if args.research_methods:
        base["research_methods"] = args.research_methods
    return base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import or enrich a tool or resource entry from GitHub")
    parser.add_argument("repo", nargs="?", help="GitHub repository as owner/repo or URL")
    parser.add_argument("--interactive", action="store_true", help="Prompt for missing values interactively")
    parser.add_argument("--list-taxonomies", action="store_true", help="Print allowed taxonomy IDs for domains, collaboration types, scales, modalities, and research methods")
    parser.add_argument("--entry-type", choices=ENTRY_TYPE_OPTIONS, default="tool", help="Entry kind to create or update")
    parser.add_argument("--entry-id", help="Existing or new CollabAtlas entry ID. Defaults to a slug from the repository name.")
    parser.add_argument("--token", help="Optional GitHub token. Defaults to GITHUB_TOKEN if set.")
    parser.add_argument("--domains", nargs="+", choices=DOMAIN_IDS, help="Required for new entries: one or more CollabAtlas domain IDs")
    parser.add_argument("--collaboration-types", dest="collaboration_types", nargs="+", choices=COLLAB_TYPE_IDS, help="Required for new entries: one or more collaboration type IDs")
    parser.add_argument("--scales", nargs="+", choices=SCALE_IDS, help="Required for new entries: one or more scale IDs")
    parser.add_argument("--modalities", nargs="+", choices=MODALITY_IDS, help="Required for new entries: one or more modality IDs")
    parser.add_argument("--maturity", default="established", choices=MATURITY_OPTIONS, help="Default maturity for newly created entries")
    parser.add_argument("--contributors", nargs="+", default=["collabatlas-team"], help="Contributor names for newly created entries")
    parser.add_argument("--status", default="draft", choices=STATUS_OPTIONS, help="Publication status for newly created entries")
    parser.add_argument("--research-methods", nargs="+", choices=RESEARCH_METHOD_IDS, help="Optional research method IDs for newly created entries")
    parser.add_argument("--resource-type", choices=RESOURCE_TYPE_OPTIONS, help="Resource type when --entry-type resource is used")
    parser.add_argument("--authors", nargs="+", help="Resource authors when --entry-type resource is used")
    parser.add_argument("--year", type=int, help="Publication year when --entry-type resource is used")
    parser.add_argument("--access", choices=ACCESS_OPTIONS, help="Access level when --entry-type resource is used")
    parser.add_argument("--dry-run", action="store_true", help="Preview the parsed entry without writing files")
    return parser.parse_args()


def run_interactive_setup(args: argparse.Namespace) -> argparse.Namespace:
    print("CollabAtlas GitHub import — interactive mode")
    print("Press Enter to accept defaults when shown.\n")
    if not args.repo:
        args.repo = prompt_text("GitHub repository (owner/repo or URL)", required=True)
    args.entry_type = prompt_single_choice("Entry type", ENTRY_TYPE_OPTIONS, default=args.entry_type)
    return args


def load_existing_entry(entry_type: str, entry_id: str):
    if entry_type == "resource":
        return load_resource_entry(entry_id), load_resource_body(entry_id), merge_resource_metadata
    return load_tool_entry(entry_id), load_tool_body(entry_id), merge_tool_metadata


def print_entry_summary(entry_type: str, entry_id: str, data: dict, repo: str, is_existing: bool) -> None:
    print("\nSummary")
    print("-" * 40)
    print(f"Type: {entry_type}")
    print(f"Entry ID: {entry_id}")
    print(f"Repository: {repo}")
    print(f"Title: {data.get('title')}")
    print(f"Tagline: {data.get('tagline')}")
    print(f"Mode: {'update existing entry' if is_existing else 'create new entry'}")
    print(f"Domains: {', '.join(data.get('domains', []))}")
    print(f"Collaboration types: {', '.join(data.get('collaboration-types', []))}")
    print(f"Scales: {', '.join(data.get('scales', []))}")
    print(f"Modalities: {', '.join(data.get('modalities', []))}")
    if entry_type == "resource":
        print(f"Resource type: {data.get('resource_type')}")
        print(f"Authors: {', '.join(data.get('authors', []))}")
        print(f"Access: {data.get('access')}")
    else:
        print(f"License: {data.get('license')}")
        print(f"Open source: {data.get('open_source')}")
    print()


def main() -> None:
    args = parse_args()

    if args.list_taxonomies:
        print_taxonomy_options()
        return

    interactive = args.interactive or not args.repo
    if interactive:
        args = run_interactive_setup(args)

    if not args.repo:
        print("A GitHub repository is required.", file=sys.stderr)
        sys.exit(1)

    token = args.token or os.getenv("GITHUB_TOKEN")

    try:
        repo = normalize_repo_identifier(args.repo)
        repo_data = fetch_github_repo(repo, token=token)
        readme_url = fetch_readme_url(repo, token=token)
    except Exception as exc:
        print(f"GitHub fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.entry_type == "resource":
        if interactive:
            args.resource_type = prompt_single_choice(
                "Resource type",
                RESOURCE_TYPE_OPTIONS,
                default=args.resource_type or "tutorial",
            )
            authors_default = ", ".join(args.authors or [((repo_data.get("owner") or {}).get("login") or "")])
            authors_raw = prompt_text("Authors (comma-separated)", default=authors_default)
            args.authors = [item.strip() for item in (authors_raw or "").split(",") if item.strip()]
            args.year = prompt_int("Publication year", default=args.year)
            args.access = prompt_single_choice(
                "Access",
                ACCESS_OPTIONS,
                default=args.access or ("open" if not repo_data.get("private") else "restricted"),
            )
        parsed = parse_github_resource(
            repo_data,
            repo,
            readme_url,
            resource_type=args.resource_type or "tutorial",
            authors=args.authors,
            year=args.year,
            access=args.access or ("open" if not repo_data.get("private") else "restricted"),
        )
        suggested_entry_id = args.entry_id or slugify_resource(parsed["title"])
    else:
        parsed = parse_github_tool(repo_data, repo, readme_url)
        suggested_entry_id = args.entry_id or slugify_tool(parsed["title"])

    if interactive:
        print(f"\nGitHub repository: {repo}")
        print(f"Repository title: {parsed['title']}")
        entry_id = prompt_text("CollabAtlas entry id", default=suggested_entry_id, required=True)
    else:
        entry_id = suggested_entry_id

    existing, body, merge_func = load_existing_entry(args.entry_type, entry_id)
    if existing:
        if interactive:
            print(f"Updating existing {args.entry_type} entry '{entry_id}'.")
        merged = merge_func(existing, parsed)
        merged["last_reviewed"] = date.today().isoformat()
    else:
        if interactive:
            print(f"Creating a new {args.entry_type} entry. Please map it to CollabAtlas taxonomies.")
            if not args.domains:
                args.domains = prompt_multi_choice("Domains", DOMAINS, required=True)
            if not args.collaboration_types:
                args.collaboration_types = prompt_multi_choice("Collaboration types", COLLAB_TYPES, required=True)
            if not args.scales:
                args.scales = prompt_multi_choice("Scales", SCALES, required=True)
            if not args.modalities:
                args.modalities = prompt_multi_choice("Modalities", MODALITIES, required=True)
            if not args.research_methods:
                args.research_methods = prompt_multi_choice("Research methods (optional)", RESEARCH_METHODS, required=False)
            args.maturity = prompt_single_choice("Maturity", MATURITY_OPTIONS, default=args.maturity)
            args.status = prompt_single_choice("Status", STATUS_OPTIONS, default=args.status)
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
                f"Creating a new {args.entry_type} entry requires: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing),
                file=sys.stderr,
            )
            sys.exit(1)
        merged = build_new_entry(parsed, entry_id, args)
        body = ""

    if interactive:
        print_entry_summary(args.entry_type, entry_id, merged, repo, existing is not None)
        if prompt_yes_no("Preview YAML before deciding", default=False):
            print(yaml.dump(merged, allow_unicode=True, sort_keys=False))
        if not prompt_yes_no("Write files now", default=not args.dry_run):
            print("No files written.")
            return

    if args.dry_run and not interactive:
        print(yaml.dump(merged, allow_unicode=True, sort_keys=False))
        return

    if args.entry_type == "resource":
        write_resource_files(merged, body=body)
        print(f"Saved resource entry: {RESOURCE_DATA_DIR / (entry_id + '.yaml')}")
    else:
        write_tool_files(merged, body=body)
        print(f"Saved tool entry: {TOOL_DATA_DIR / (entry_id + '.yaml')}")


if __name__ == "__main__":
    main()
