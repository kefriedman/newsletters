#!/usr/bin/env python3
"""
Update archive index pages with links to all archived newsletters.
This script scans the archive folders and regenerates the index.html files.
"""

import os
import re
from datetime import datetime
from pathlib import Path


def get_archive_entries(archive_dir: Path) -> list[dict]:
    """Get all newsletter files in the archive directory."""
    entries = []

    if not archive_dir.exists():
        return entries

    for file in archive_dir.glob("*.html"):
        if file.name == "index.html":
            continue

        # Extract date from filename (expecting YYYY-MM-DD.html)
        match = re.match(r"(\d{4}-\d{2}-\d{2})\.html", file.name)
        if match:
            date_str = match.group(1)
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                entries.append({
                    "filename": file.name,
                    "date": date,
                    "formatted_date": date.strftime("%B %d, %Y"),
                })
            except ValueError:
                continue

    # Sort by date, newest first
    entries.sort(key=lambda x: x["date"], reverse=True)
    return entries


def generate_archive_html(entries: list[dict], newsletter_type: str) -> str:
    """Generate the HTML list items for the archive."""
    if not entries:
        return ""

    items = []
    for entry in entries:
        items.append(f'''                <li>
                    <a href="{entry['filename']}">
                        What You Need to Know: {newsletter_type}
                        <div class="date">{entry['formatted_date']}</div>
                    </a>
                </li>''')

    return "\n".join(items)


def update_archive_index(archive_dir: Path, newsletter_type: str):
    """Update the archive index.html with current entries."""
    entries = get_archive_entries(archive_dir)
    index_path = archive_dir / "index.html"

    if not index_path.exists():
        print(f"Warning: {index_path} does not exist")
        return

    # Read current index
    content = index_path.read_text()

    # Generate new archive list HTML
    archive_html = generate_archive_html(entries, newsletter_type)

    # Replace the archive list content
    if archive_html:
        # Replace empty archive list with populated one
        content = re.sub(
            r'(<ul class="archive-list" id="archive-list">)\s*(</ul>)',
            f'\\1\n{archive_html}\n            \\2',
            content
        )
        # Also replace any existing entries
        content = re.sub(
            r'(<ul class="archive-list" id="archive-list">)\s*(<li>.*?</li>\s*)+\s*(</ul>)',
            f'\\1\n{archive_html}\n            \\3',
            content,
            flags=re.DOTALL
        )
        # Hide empty state
        content = re.sub(
            r'(<div class="empty-state" id="empty-state">)',
            r'<div class="empty-state" id="empty-state" style="display: none;">',
            content
        )
    else:
        # Show empty state
        content = re.sub(
            r'<div class="empty-state" id="empty-state" style="display: none;">',
            r'<div class="empty-state" id="empty-state">',
            content
        )

    # Write updated index
    index_path.write_text(content)
    print(f"Updated {index_path} with {len(entries)} entries")


def main():
    """Update all archive index pages."""
    root = Path(__file__).parent

    # Update AI newsletter archive
    ai_archive = root / "docs" / "ai" / "archive"
    update_archive_index(ai_archive, "AI")

    # Update Economics newsletter archive
    econ_archive = root / "docs" / "economics" / "archive"
    update_archive_index(econ_archive, "Economics")


if __name__ == "__main__":
    main()
