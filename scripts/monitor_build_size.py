#!/usr/bin/env python3
"""
Monitor the build size of critical assets in the public/ directory.
Warns if file sizes exceed recommended thresholds.
"""

import os
import sys
from pathlib import Path

# Size thresholds in bytes
THRESHOLDS = {
    "public/index.json": 2 * 1024 * 1024,  # 2 MB (Search index)
    "public/js/site-search.js": 50 * 1024, # 50 KB (Search logic)
    "public/css/main.css": 150 * 1024,     # 150 KB (Main stylesheet) - adjusted for inlined assets
    "public/index.html": 150 * 1024,       # 150 KB (Homepage HTML)
}

# Directories to scan for large files
SCAN_DIRS = [
    "public/js",
    "public/css",
    "public/catalogue",
]

def get_file_size(path):
    """Return file size in bytes."""
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return 0

def format_size(size):
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def check_file(path_str, threshold_override=None):
    """Check a specific file against thresholds."""
    path = Path(path_str)
    size = get_file_size(path)
    
    threshold = threshold_override
    if threshold is None:
        threshold = THRESHOLDS.get(path_str)
        
    # If not found, try to match by key content (e.g. for hashed CSS)
    if threshold is None:
        if "css" in path_str and "main" in path_str:
             threshold = THRESHOLDS.get("public/css/main.css")
    
    status = "OK"
    if size == 0:
        status = "MISSING"
        color = "\033[91m" # Red
    elif threshold and size > threshold:
        status = "WARNING"
        color = "\033[93m" # Yellow
    else:
        color = "\033[92m" # Green
    
    reset = "\033[0m"
    threshold_str = f"(Limit: {format_size(threshold)})" if threshold else ""
    
    print(f"{color}[{status}]{reset} {path_str:<30} {format_size(size):<10} {threshold_str}")
    return size

def scan_directory(dir_path):
    """Scan a directory for large files."""
    print(f"\nScanning {dir_path} for large assets (>500KB)...")
    path = Path(dir_path)
    if not path.exists():
        print(f"Directory {dir_path} not found.")
        return

    large_files = []
    for file in path.rglob("*"):
        if file.is_file():
            size = file.stat().st_size
            if size > 500 * 1024: # 500KB
                large_files.append((file, size))
    
    if not large_files:
        print("  No large files found.")
    else:
        for file, size in sorted(large_files, key=lambda x: x[1], reverse=True):
             print(f"  \033[93m{file.relative_to(Path.cwd())}: {format_size(size)}\033[0m")

def main():
    print("=== Build Size Monitor ===\n")
    
    # Check specific files
    check_file("public/index.json")
    
    # Check CSS files (hashed)
    css_dir = Path("public/css")
    if css_dir.exists():
        found_main = False
        for css_file in css_dir.glob("main.min.*.css"):
            check_file(str(css_file))
            found_main = True
        if not found_main:
             # Try just main.css if no hashed version
             check_file("public/css/main.css")
    
    # Check JS files
    js_dir = Path("public/js")
    if js_dir.exists():
        for js_file in js_dir.glob("*.js"):
            # Only check specific JS files if they match expected patterns
            if "search" in js_file.name or "wizard" in js_file.name:
                check_file(str(js_file))
            
    # Check homepage
    check_file("public/index.html")

    # General Scan
    scan_directory("public")

if __name__ == "__main__":
    # Ensure we run from project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    os.chdir(project_root)
    
    main()
