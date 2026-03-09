#!/usr/bin/env python3
"""Shared helpers for CollabAtlas dataset import and enrichment scripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATASET_DATA_DIR = ROOT / "data" / "entries" / "datasets"
DATASET_CONTENT_DIR = ROOT / "content" / "catalogue" / "datasets"
TAXONOMY_DIR = ROOT / "data" / "taxonomies"

PRESERVED_DATASET_FIELDS = {
	"id",
	"type",
	"domains",
	"collaboration-types",
	"scales",
	"modalities",
	"maturity",
	"contributors",
	"status",
	"created",
	"last_reviewed",
	"research_methods",
	"related_entries",
	"notes",
}


def slugify(value: str) -> str:
	"""Create a URL-safe identifier from a title."""
	value = value.lower().strip()
	value = re.sub(r"[^a-z0-9]+", "-", value)
	return value.strip("-") or "dataset"


def merge_unique(values_a: list[str] | None, values_b: list[str] | None) -> list[str]:
	"""Merge two string lists while preserving order and uniqueness."""
	merged: list[str] = []
	for value in (values_a or []) + (values_b or []):
		if value and value not in merged:
			merged.append(value)
	return merged


def load_taxonomy_records(name: str) -> list[dict[str, Any]]:
	"""Load taxonomy records from a YAML file in `data/taxonomies`."""
	path = TAXONOMY_DIR / f"{name}.yaml"
	if not path.exists():
		return []

	with open(path, encoding="utf-8") as f:
		data = yaml.safe_load(f) or []
	return data if isinstance(data, list) else []


def load_taxonomy_ids(name: str) -> list[str]:
	"""Return the ordered list of valid taxonomy identifiers for a taxonomy file."""
	return [record.get("id") for record in load_taxonomy_records(name) if record.get("id")]


def load_dataset_entry(entry_id: str) -> dict[str, Any] | None:
	"""Load a dataset YAML entry by its identifier if it exists."""
	path = DATASET_DATA_DIR / f"{entry_id}.yaml"
	if not path.exists():
		return None

	with open(path, encoding="utf-8") as f:
		return yaml.safe_load(f) or {}


def load_markdown_body(entry_id: str) -> str:
	"""Load the content body after front matter for an existing dataset page."""
	path = DATASET_CONTENT_DIR / f"{entry_id}.md"
	if not path.exists():
		return ""

	text = path.read_text(encoding="utf-8")
	if not text.startswith("---\n"):
		return text

	parts = text.split("---\n", 2)
	if len(parts) < 3:
		return ""
	return parts[2].lstrip("\n")


def build_front_matter(data: dict[str, Any]) -> str:
	"""Build the Hugo front matter for a dataset page."""
	def escape_string(value: str) -> str:
		return value.replace('\\', '\\\\').replace('"', '\\"')

	def format_list(values: list[str]) -> str:
		return "[" + ", ".join(f'"{escape_string(value)}"' for value in values) + "]"

	lines = ["---"]
	lines.append(f'title: "{escape_string(data.get("title") or "")}"')
	lines.append(f'tagline: "{escape_string(data.get("tagline") or "")}"')
	lines.append(f'data_id: "{data["id"]}"')

	for field in ("domains", "collaboration-types", "scales", "modalities"):
		values = data.get(field) or []
		if values:
			lines.append(f"{field}: {format_list(values)}")

	for field in ("maturity", "status", "platform"):
		value = data.get(field)
		if value:
			lines.append(f'{field}: "{value}"')

	lines.append("---")
	return "\n".join(lines) + "\n"


def write_dataset_files(data: dict[str, Any], body: str = "") -> None:
	"""Write both the dataset YAML file and its matching Hugo content file."""
	DATASET_DATA_DIR.mkdir(parents=True, exist_ok=True)
	DATASET_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

	yaml_path = DATASET_DATA_DIR / f"{data['id']}.yaml"
	markdown_path = DATASET_CONTENT_DIR / f"{data['id']}.md"

	with open(yaml_path, "w", encoding="utf-8") as f:
		yaml.dump(
			data,
			f,
			allow_unicode=True,
			sort_keys=False,
			default_flow_style=False,
		)

	front_matter = build_front_matter(data)
	with open(markdown_path, "w", encoding="utf-8") as f:
		f.write(front_matter)
		if body:
			f.write("\n" + body.rstrip() + "\n")


def merge_dataset_metadata(
	existing: dict[str, Any] | None,
	fetched: dict[str, Any],
) -> dict[str, Any]:
	"""Merge fetched dataset metadata with an existing entry."""
	existing = dict(existing or {})
	merged = dict(existing)
	merged.update(fetched)

	for field in ("tags", "source_services"):
		merged[field] = merge_unique(existing.get(field), fetched.get(field))

	if existing.get("external_links") or fetched.get("external_links"):
		merged_links = []
		seen = set()
		for link in (existing.get("external_links") or []) + (fetched.get("external_links") or []):
			key = (link.get("type"), link.get("url"), link.get("title"))
			if key in seen:
				continue
			seen.add(key)
			merged_links.append(link)
		merged["external_links"] = merged_links

	for field in PRESERVED_DATASET_FIELDS:
		if field in existing:
			merged[field] = existing[field]

	return {k: v for k, v in merged.items() if v not in (None, [], "")}
