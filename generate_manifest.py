#!/usr/bin/env python3
"""
generate_manifest.py — Build tool for blog posts.

Reads all posts/*.md files (sorted newest-first by filename),
parses their YAML frontmatter, and writes posts/manifest.json.

Usage:
    python3 generate_manifest.py

Run this every time you add or edit a post, then commit the
updated manifest.json alongside your .md file.

To preview locally, serve from the repo root:
    python3 -m http.server 8000
then open http://localhost:8000
"""

import os
import re
import json
from datetime import datetime

POSTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posts")


def parse_frontmatter(text):
    """
    Extract YAML-like frontmatter between --- delimiters.
    Returns (data_dict, markdown_content).
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_raw = text[4:end]
    content = text[end + 5:]
    data = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data, content


def format_date(date_str):
    """Format YYYY-MM-DD → '1 March 2026'."""
    try:
        d = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        # %-d is Linux/macOS; use %d and strip leading zero manually for portability
        day = str(d.day)
        return f"{day} {d.strftime('%B %Y')}"
    except ValueError:
        return str(date_str)


def strip_markdown(text):
    """Remove common markdown syntax to produce plain text for search."""
    # Remove headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    # Remove inline code and code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    # Remove links, keep label
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_manifest():
    # Collect all .md files, sort newest-first (relies on YYYY-MM-DD filenames)
    md_files = sorted(
        [f for f in os.listdir(POSTS_DIR) if f.endswith(".md")],
        reverse=True,
    )

    if not md_files:
        print("No .md files found in posts/")
        return

    posts = []
    for filename in md_files:
        slug = filename[:-3]  # strip .md
        filepath = os.path.join(POSTS_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as fh:
            raw = fh.read()

        data, content = parse_frontmatter(raw)
        plain = strip_markdown(content)

        # Excerpt: prefer frontmatter, else first paragraph
        excerpt = data.get("excerpt", "").strip()
        if not excerpt:
            first_para = plain.split("\n\n")[0].strip().replace("\n", " ")
            excerpt = first_para[:300] + ("…" if len(first_para) > 300 else "")

        posts.append({
            "slug": slug,
            "title": data.get("title", slug),
            "date": data.get("date", slug),
            "dateFormatted": format_date(data.get("date", slug)),
            "excerpt": excerpt,
            # First 2000 chars of plain content — used by client-side full-text search
            "text": plain[:2000],
        })

    out_path = os.path.join(POSTS_DIR, "manifest.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(posts, fh, indent=2, ensure_ascii=False)

    print(f"✓  Wrote posts/manifest.json  ({len(posts)} post{'s' if len(posts) != 1 else ''})")
    for p in posts:
        print(f"   [{p['date']}]  {p['title']}")


if __name__ == "__main__":
    build_manifest()
