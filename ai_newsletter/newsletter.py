#!/usr/bin/env python3
"""
Weekly AI Newsletter Generator

This script:
1. Fetches recent AI papers from arXiv
2. Fetches updates from major AI companies (Anthropic, OpenAI, DeepMind)
3. Fetches trending AI/ML tools from GitHub
4. Uses Claude AI to summarize and highlight the most interesting content
5. Sends a formatted HTML newsletter via Gmail to multiple recipients
"""

import os
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

from jinja2 import Environment, FileSystemLoader

from sources import fetch_all_papers, fetch_all_blog_posts, fetch_all_tools, get_papers_by_category
from summarizer import generate_newsletter_content
from emailer import send_newsletter


def render_newsletter(content: dict[str, str]) -> str:
    """Render the newsletter HTML template with content."""
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("newsletter.html")

    # Format the date
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    return template.render(
        date=date_str,
        news=content["news"],
        tools=content["tools"],
        research=content["research"],
    )


def main():
    """Generate and send the weekly AI newsletter."""
    print("=" * 60)
    print("Weekly AI Newsletter Generator")
    print("=" * 60)
    print()

    # Step 1: Fetch data from all sources
    print("Step 1: Fetching papers, updates, and tools...")
    print("-" * 40)
    papers = fetch_all_papers()
    blog_posts = fetch_all_blog_posts()
    tools = fetch_all_tools()
    papers_by_category = get_papers_by_category(papers)

    print(f"\nPapers by category:")
    for category, cat_papers in papers_by_category.items():
        print(f"  {category}: {len(cat_papers)}")
    print(f"Blog posts: {len(blog_posts)}")
    print(f"Trending tools: {len(tools)}")
    print()

    # Step 2: Generate AI summaries
    print("Step 2: Generating AI summaries...")
    print("-" * 40)
    content = generate_newsletter_content(papers_by_category, blog_posts, tools)
    print()

    # Step 3: Render HTML template
    print("Step 3: Rendering newsletter template...")
    print("-" * 40)
    html = render_newsletter(content)
    print(f"Generated HTML: {len(html)} characters")
    print()

    # Step 4: Send email
    print("Step 4: Sending newsletter...")
    print("-" * 40)
    today = datetime.now()
    subject = f"Weekly AI Briefing - {today.strftime('%B %d, %Y')}"

    success = send_newsletter(html, subject)

    print()
    print("=" * 60)
    if success:
        print("Newsletter sent successfully!")
    else:
        print("Failed to send newsletter. Check the error messages above.")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
