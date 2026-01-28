#!/usr/bin/env python3
"""
Fetch publications from Google Scholar and generate data_prefetched.json.

Usage:
    source /Users/rafaelvalle/VirtualEnvironments/dl-ml/venv/bin/activate
    python fetch_scholar.py

This script:
1. Loads ALL existing entries from data.json (your hand-curated data)
2. Fetches publications from Google Scholar
3. Adds ONLY NEW publications (those not already in data.json, matched by title)
4. Outputs everything to data_prefetched.json

Your data.json entries are NEVER overwritten - they take priority.
New Scholar entries use placeholder fields (media, bibtex, etc.).
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

try:
    from scholarly import scholarly
except ImportError:
    print("Error: 'scholarly' library not installed.")
    print("Install it with: pip install scholarly")
    exit(1)


# Configuration
SCHOLAR_ID = "SktxU8IAAAAJ"  # Rafael Valle's Google Scholar ID
OUTPUT_FILE = "data_prefetched.json"
DATA_FILE = "data.json"  # Existing curated data file


def generate_id(title: str) -> str:
    """
    Generate a short ID from a paper title.

    Examples:
        "Fugatto: Foundational Generative..." -> "FUGATTO"
        "Audio Flamingo 2: An Audio-Language..." -> "AUDIOFLAMINGO2"
        "WaveGlow: a Flow-based..." -> "WAVEGLOW"
    """
    # Take the first part before colon if exists
    main_title = title.split(":")[0].strip()

    # Remove special characters and keep alphanumeric
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", main_title)

    # Take first word(s) that seem like the model/project name
    words = clean.split()

    if len(words) == 1:
        return words[0].upper()

    # Check if first word looks like an acronym or model name
    first_word = words[0]
    if first_word.isupper() or any(c.isdigit() for c in first_word):
        return first_word.upper()

    # Otherwise, create acronym from first few significant words
    # Skip common words
    skip_words = {"a", "an", "the", "of", "for", "with", "and", "to", "in", "on"}
    significant = [w for w in words[:4] if w.lower() not in skip_words]

    if len(significant) == 1:
        return significant[0].upper()

    # If the title starts with a proper name/acronym, use it
    if significant[0][0].isupper():
        return significant[0].upper()

    # Create acronym
    return "".join(w[0] for w in significant).upper()


def parse_authors(author_string: str) -> List[str]:
    """Parse author string into a list of author names."""
    if not author_string:
        return []

    # Split by comma or "and"
    authors = re.split(r",\s*|\s+and\s+", author_string)
    return [a.strip() for a in authors if a.strip()]


def extract_arxiv_id(url: str) -> Optional[str]:
    """Extract arXiv ID from a URL if present."""
    if not url:
        return None
    match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", url)
    if match:
        return match.group(1)
    return None


def load_existing_data() -> Dict[str, Any]:
    """Load existing publications from data.json if it exists."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, DATA_FILE)

    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("publications", {})
    return {}


def normalize_title(title: str) -> str:
    """Normalize a title for comparison (lowercase, alphanumeric only)."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def find_matching_entry(title: str, existing_data: Dict[str, Any]) -> Optional[str]:
    """Find if a title matches any existing entry in data.json.

    Returns the matching ID if found, None otherwise.
    """
    normalized_new = normalize_title(title)

    for pub_id, pub_data in existing_data.items():
        existing_title = pub_data.get("title", "")
        normalized_existing = normalize_title(existing_title)

        # Check for exact match after normalization
        if normalized_new == normalized_existing:
            return pub_id

        # Check if one title contains the other (handles subtitle differences)
        # e.g., "Audio Flamingo 2" matches "Audio Flamingo 2: An Audio-Language Model..."
        if normalized_new.startswith(normalized_existing) or normalized_existing.startswith(normalized_new):
            # Require at least 20 chars to match to avoid false positives
            min_len = min(len(normalized_new), len(normalized_existing))
            if min_len >= 20:
                return pub_id

    return None


def fetch_publications(existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch all publications from Google Scholar profile.

    Args:
        existing_data: Publications from data.json. Entries here take precedence
                      over Google Scholar data when titles match.

    Strategy:
        1. Start with ALL entries from data.json (preserving your curated data)
        2. For each Google Scholar publication, check if title matches existing entry
        3. If match found, skip (data.json version is already included)
        4. If no match, add as new publication from Scholar
    """
    print(f"Fetching profile for scholar ID: {SCHOLAR_ID}")

    # Get author profile
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    print(f"Found {len(author['publications'])} publications on Google Scholar")

    # Start with ALL existing data.json entries
    publications = dict(existing_data)
    print(f"Starting with {len(publications)} entries from data.json")

    new_ids = []  # Track IDs of new publications from Scholar
    skipped_count = 0

    for i, pub in enumerate(author["publications"]):
        # Fetch full publication details (includes abstract, etc.)
        print(f"  [{i+1}/{len(author['publications'])}] Fetching: {pub['bib'].get('title', 'Unknown')[:50]}...")

        try:
            pub_filled = scholarly.fill(pub)
            time.sleep(1)  # Be respectful to Google Scholar
        except Exception as e:
            print(f"    Warning: Could not fetch details: {e}")
            pub_filled = pub

        bib = pub_filled.get("bib", {})
        title = bib.get("title", "Unknown Title")

        # Check if this title matches any existing entry in data.json (by title similarity)
        matching_id = find_matching_entry(title, existing_data)
        if matching_id:
            print(f"    -> Skipped (matches '{matching_id}' in data.json)")
            skipped_count += 1
            continue

        # Generate ID for new publication
        pub_id = generate_id(title)

        # Handle duplicate IDs by appending year
        if pub_id in publications:
            year = bib.get("pub_year", "")
            pub_id = f"{pub_id}{year}"

        # Still duplicate? Append counter
        counter = 2
        original_id = pub_id
        while pub_id in publications:
            pub_id = f"{original_id}_{counter}"
            counter += 1

        # Extract authors
        authors = parse_authors(bib.get("author", ""))

        # Build links
        links = {}
        pub_url = pub_filled.get("pub_url", "")
        if pub_url:
            if "arxiv.org" in pub_url:
                links["arxiv"] = pub_url
            else:
                links["paper"] = pub_url

        # Check for arXiv in eprint field
        eprint = bib.get("eprint", "")
        if eprint and "arxiv" not in links:
            links["arxiv"] = f"https://arxiv.org/abs/{eprint}"

        # Build publication entry
        entry = {
            "title": title,
            "authors": authors,
            "venue": bib.get("venue", bib.get("journal", bib.get("booktitle", ""))),
            "year": int(bib.get("pub_year")) if bib.get("pub_year") and str(bib.get("pub_year")).isdigit() else None,
            "links": links,
            "media": {
                "type": "image",
                "src": "images/placeholder.png"
            },
            "abstract": bib.get("abstract", ""),
            "bibtex": "",
            "_citations": pub_filled.get("num_citations", 0),  # Bonus: citation count
        }

        publications[pub_id] = entry
        new_ids.append(pub_id)
        print(f"    -> ID: {pub_id} (NEW from Google Scholar)")

    print(f"\nSummary: {skipped_count} matched data.json, {len(new_ids)} new from Scholar")

    return publications, new_ids


def sort_publications_by_year(publications: Dict[str, Any]) -> Dict[str, Any]:
    """Sort publications by year (most recent first).

    Publications with None/null year are placed at the end.
    """
    def sort_key(item):
        pub_id, pub_data = item
        year = pub_data.get("year")
        # Put None years at the end by using a very small number
        return (year is None, -(year or 0))

    sorted_items = sorted(publications.items(), key=sort_key)
    return dict(sorted_items)


def main():
    print("=" * 60)
    print("Google Scholar Publication Fetcher")
    print("=" * 60)
    print()

    # Load existing curated data from data.json
    existing_data = load_existing_data()
    if existing_data:
        print(f"Loaded {len(existing_data)} existing entries from {DATA_FILE}")
        print("  (These will take precedence over Google Scholar data)")
        print()

    publications, new_ids = fetch_publications(existing_data)

    # Sort publications by year (most recent first)
    publications = sort_publications_by_year(publications)
    print()
    print("Sorted publications by year (most recent first)")

    # Get the sorted order (by year) for all IDs
    sorted_ids = list(publications.keys())

    # Sort summary lists by year (using the same order as publications)
    from_data_json_sorted = [pid for pid in sorted_ids if pid in existing_data]
    new_from_scholar_sorted = [pid for pid in sorted_ids if pid in new_ids]

    # Build output structure with summary for easy review
    output = {
        "_summary": {
            "_comment": "Quick reference of all publication IDs (sorted by year, most recent first)",
            "from_data_json": from_data_json_sorted,
            "new_from_scholar": new_from_scholar_sorted,
            "all_ids": sorted_ids
        },
        "publications": publications
    }

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print(f"Done! Wrote {len(publications)} publications to {OUTPUT_FILE}")
    print()
    print("Data sources:")
    print(f"  - {len(existing_data)} entries preserved from data.json (your curated data)")
    print(f"  - {len(new_ids)} new entries from Google Scholar")
    print()
    if new_ids:
        print("NEW publications from Google Scholar:")
        for pub_id in new_ids:
            title = publications[pub_id].get("title", "")[:60]
            print(f"  - {pub_id}: {title}...")
        print()
    print("Quick review: Open data_prefetched.json and check '_summary' at the top")
    print("  - 'from_data_json': your curated entries (preserved)")
    print("  - 'new_from_scholar': new entries to review")
    print()
    print("To add new publications to your site:")
    print("  1. Copy desired entries from 'publications' to data.json")
    print("  2. Curate them (add media, bibtex, website links)")
    print("  3. Add IDs to site.json sections")
    print("  4. Run: python build_site.py --data data.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
