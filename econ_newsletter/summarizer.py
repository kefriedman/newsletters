"""
AI summarization module using Claude API.
Generates newsletter content from collected papers and blog posts.
"""

import os
import re
from anthropic import Anthropic
from sources import Paper, BlogPost


def get_client() -> Anthropic:
    """Initialize Anthropic client."""
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences and headers from Claude's response."""
    text = re.sub(r'^```(?:html)?\s*\n?', '', text.strip())
    text = re.sub(r'\n?```\s*$', '', text.strip())
    # Remove markdown headers at the start (## Title, # Title, etc.)
    text = re.sub(r'^#{1,3}\s+[^\n]+\n*', '', text.strip())
    return text


def summarize_papers(papers: list[Paper], category: str) -> str:
    """Generate a summary of papers in a category using Claude."""
    if not papers:
        return f"No new {category.lower()} papers this week."

    client = get_client()

    # Format papers for the prompt
    papers_text = ""
    for i, paper in enumerate(papers[:15], 1):  # Limit to 15 papers per category
        papers_text += f"""
Paper {i}:
Title: {paper['title']}
Authors: {paper['authors']}
Source: {paper['source']}
Abstract: {paper['abstract'][:800]}
URL: {paper['url']}
---
"""

    prompt = f"""You are an expert economics research assistant creating a weekly newsletter section on {category}.

Here are the new working papers published this week:

{papers_text}

Create an engaging newsletter section that:
1. Starts with a brief (1-2 sentence) overview of what's notable in {category} this week
2. Highlights the 3-5 most interesting/significant papers
3. Briefly mention any other notable papers worth reading

Format as clean HTML for an email newsletter. Each paper should be structured like this:

<p><em>Overview sentence about this week in {category}.</em></p>

<h3><a href="URL">Paper Title</a></h3>
<p><strong>Authors:</strong> Author names</p>
<p>2-3 sentence summary of key findings in accessible language. Why it matters: one sentence on implications.</p>

<h3><a href="URL">Another Paper</a></h3>
<p><strong>Authors:</strong> Author names</p>
<p>Summary here.</p>

Keep the tone professional but accessible. Total length should be around 400-600 words."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def generate_top_papers(papers: list[Paper]) -> str:
    """Generate the 'Top 3 Papers of the Week' highlight section."""
    if not papers:
        return "<p>No papers available this week.</p>"

    client = get_client()

    # Format all papers - include more to ensure elite journal papers aren't missed
    papers_text = ""
    for i, paper in enumerate(papers[:50], 1):
        papers_text += f"""
Paper {i}:
Title: {paper['title']}
Authors: {paper['authors']}
Source: {paper['source']}
Category: {paper['category']}
Abstract: {paper['abstract'][:600]}
URL: {paper['url']}
---
"""

    prompt = f"""You are a senior economics editor selecting the most important papers of the week.

From these papers, select the TOP 3 most significant, interesting, or impactful papers across all categories:

{papers_text}

For each of the top 3 papers, provide an attention-grabbing headline, the paper details, and why it matters.

Format as clean HTML for an email newsletter. Each paper should be structured like this:

<div class="top-paper">
<h3>Attention-Grabbing Headline About Key Finding</h3>
<p class="paper-meta"><strong>Title:</strong> Paper Title | <strong>Authors:</strong> Author names</p>
<p>A compelling 3-4 sentence explanation of what the paper found and why economists should care.</p>
<p><a href="URL" class="read-more">Read the paper →</a></p>
</div>

<div class="top-paper">
<h3>Second Paper Headline</h3>
<p class="paper-meta"><strong>Title:</strong> Paper Title | <strong>Authors:</strong> Author names</p>
<p>Description here.</p>
<p><a href="URL" class="read-more">Read the paper →</a></p>
</div>

Make it engaging and accessible to both economists and interested general readers."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def summarize_blog_discussions(posts: list[BlogPost]) -> str:
    """Generate a summary of economics blog discussions."""
    if not posts:
        return "<p>No blog discussions to highlight this week.</p>"

    client = get_client()

    posts_text = ""
    for i, post in enumerate(posts[:15], 1):
        posts_text += f"""
Post {i}:
Title: {post['title']}
Source: {post['source']}
Summary: {post['summary']}
URL: {post['url']}
---
"""

    prompt = f"""You are curating the week's most interesting economics blog discussions.

Here are recent posts from top economics blogs:

{posts_text}

Create a "Discussion Highlights" section that:
1. Opens with a 1-sentence overview of what economists are debating this week
2. Highlights 3-5 most interesting discussions

Format as clean HTML for an email newsletter. Each discussion should be its own block:

<p><em>Overview sentence about this week's debates.</em></p>

<h3>Catchy Topic Title</h3>
<p><span class="source">Blog Name</span> — 1-2 sentences on the key argument or insight. <a href="URL">Read more</a></p>

<h3>Another Topic</h3>
<p><span class="source">Blog Name</span> — Description here. <a href="URL">Read more</a></p>

Keep it lively and engaging. Total length around 200-300 words."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def generate_newsletter_content(
    papers_by_category: dict[str, list[Paper]],
    blog_posts: list[BlogPost]
) -> dict[str, str]:
    """Generate all newsletter content sections."""

    # Flatten papers for top picks
    all_papers = []
    for papers in papers_by_category.values():
        all_papers.extend(papers)

    print("Generating top papers highlight...")
    top_papers = generate_top_papers(all_papers)

    print("Summarizing Microeconomics papers...")
    micro_section = summarize_papers(
        papers_by_category.get("Microeconomics", []),
        "Microeconomics"
    )

    print("Summarizing Macroeconomics papers...")
    macro_section = summarize_papers(
        papers_by_category.get("Macroeconomics", []),
        "Macroeconomics"
    )

    print("Summarizing Econometrics papers...")
    metrics_section = summarize_papers(
        papers_by_category.get("Econometrics", []),
        "Econometrics"
    )

    print("Summarizing blog discussions...")
    discussions = summarize_blog_discussions(blog_posts)

    return {
        "top_papers": top_papers,
        "microeconomics": micro_section,
        "macroeconomics": macro_section,
        "econometrics": metrics_section,
        "discussions": discussions,
    }
