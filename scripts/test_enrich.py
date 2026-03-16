"""Tests for enrich_catalogue.py — pure function tests (no network access)."""

import pytest

from enrich_catalogue import extract_repo_slug


# ---------------------------------------------------------------------------
# extract_repo_slug
# ---------------------------------------------------------------------------

class TestExtractRepoSlug:
    """Tests for GitHub repo slug extraction from entry data."""

    def test_explicit_github_repo_field(self):
        """When github_repo is set directly, return it as-is."""
        entry = {"github_repo": "owner/repo"}
        assert extract_repo_slug(entry) == "owner/repo"

    def test_github_repo_takes_priority_over_urls(self):
        """github_repo field should be returned even if URLs also contain GitHub links."""
        entry = {
            "github_repo": "preferred/repo",
            "website_url": "https://github.com/other/repo",
        }
        assert extract_repo_slug(entry) == "preferred/repo"

    def test_extracts_from_website_url(self):
        """Should extract slug from website_url containing a GitHub link."""
        entry = {"website_url": "https://github.com/owner/my-project"}
        assert extract_repo_slug(entry) == "owner/my-project"

    def test_extracts_from_source_url(self):
        """Should extract slug from source_url containing a GitHub link."""
        entry = {"source_url": "https://github.com/org/tool"}
        assert extract_repo_slug(entry) == "org/tool"

    def test_extracts_from_external_links(self):
        """Should extract slug from external_links entries."""
        entry = {
            "external_links": [
                {"url": "https://github.com/ext-owner/ext-repo", "type": "repository"}
            ]
        }
        assert extract_repo_slug(entry) == "ext-owner/ext-repo"

    def test_strips_git_suffix(self):
        """URLs ending with .git should have the suffix removed."""
        entry = {"website_url": "https://github.com/owner/repo.git"}
        assert extract_repo_slug(entry) == "owner/repo"

    def test_ignores_extra_path_segments(self):
        """Paths like /issues or /blob/main should not be part of the slug."""
        entry = {"website_url": "https://github.com/owner/repo/issues/42"}
        assert extract_repo_slug(entry) == "owner/repo"

    def test_returns_none_when_no_github_info(self):
        """Should return None when there is no GitHub info anywhere."""
        entry = {"title": "Some Tool", "website_url": "https://example.com"}
        assert extract_repo_slug(entry) is None

    def test_returns_none_for_empty_entry(self):
        """Should return None for a completely empty entry dict."""
        assert extract_repo_slug({}) is None

    def test_empty_github_repo_field_falls_through(self):
        """An empty-string github_repo should fall through to URL extraction."""
        entry = {
            "github_repo": "",
            "website_url": "https://github.com/fallback/repo",
        }
        # empty string is falsy, so it should fall through
        assert extract_repo_slug(entry) == "fallback/repo"

    def test_non_github_urls_ignored(self):
        """Non-GitHub URLs should not produce a slug."""
        entry = {
            "website_url": "https://gitlab.com/owner/repo",
            "source_url": "https://bitbucket.org/owner/repo",
        }
        assert extract_repo_slug(entry) is None

    def test_malformed_external_links_handled(self):
        """External links that are not dicts or lack 'url' should be skipped."""
        entry = {
            "external_links": [
                "just-a-string",
                {"type": "docs"},  # missing url key
                {"url": "https://github.com/good/repo", "type": "repository"},
            ]
        }
        assert extract_repo_slug(entry) == "good/repo"
