#!/usr/bin/env python3
"""Check external links in CollabAtlas YAML entries for broken URLs."""

import sys
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "data" / "entries"
TIMEOUT = 10
MAX_WORKERS = 5
SKIP_DOMAINS = {"doi.org", "dx.doi.org"}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) CollabAtlas-LinkChecker/1.0"


def check_url(url: str) -> tuple[str, bool, str]:
    """Check if a URL is reachable. Returns (url, ok, message)."""
    hostname = urlparse(url).hostname or ""
    if hostname in SKIP_DOMAINS:
        return url, True, "SKIPPED (DOI)"

    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", USER_AGENT)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status < 400:
                return url, True, f"{resp.status}"
            return url, False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        # Some servers return 403/404/405 for HEAD but serve GET fine
        if e.code in (403, 404, 405):
            try:
                req = urllib.request.Request(url, method="GET")
                req.add_header("User-Agent", USER_AGENT)
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    return url, resp.status < 400, f"{resp.status}"
            except Exception as e2:
                return url, False, str(e2)
        return url, False, f"HTTP {e.code}"
    except Exception as e:
        return url, False, str(e)


def main():
    urls_to_check: dict[str, list[str]] = {}  # url -> [source files]

    for yaml_file in sorted(ENTRIES_DIR.rglob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        source = str(yaml_file.relative_to(ROOT))
        for link in data.get("external_links", []):
            url = link.get("url", "")
            if url:
                urls_to_check.setdefault(url, []).append(source)

    if not urls_to_check:
        print("No external links found to check.")
        return

    print(f"Checking {len(urls_to_check)} unique URLs...")
    broken = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_url, url): url for url in urls_to_check
        }
        for future in as_completed(futures):
            url, ok, msg = future.result()
            if ok:
                print(f"  OK: {url}")
            else:
                print(f"  BROKEN: {url} ({msg})")
                broken.append((url, msg, urls_to_check[url]))

    print(f"\n{'='*50}")
    print(f"Checked {len(urls_to_check)} URLs, {len(broken)} broken")

    if broken:
        print("\nBroken links:")
        for url, msg, sources in broken:
            print(f"  {url} ({msg})")
            for src in sources:
                print(f"    referenced in: {src}")
        sys.exit(1)


if __name__ == "__main__":
    main()
