"""
AI summarization module using Claude API.
Generates newsletter content from collected papers and blog posts.
"""

import os
from anthropic import Anthropic
from sources import Paper, BlogPost


def get_client() -> Anthropic:
    """Initialize Anthropic client."""
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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
2. Highlights the 3-5 most interesting/significant papers with:
   - Paper title (as a header)
   - Authors
   - 2-3 sentence summary of key findings in accessible language
   - Why it matters (1 sentence on implications)
3. Briefly mention any other notable papers worth reading

Format the output in clean HTML suitable for an email newsletter. Use:
- <h3> for paper titles
- <p> for paragraphs
- <strong> for emphasis
- <a href="URL"> for paper links

Keep the tone professional but accessible. Total length should be around 400-600 words."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def generate_top_papers(papers: list[Paper]) -> str:
    """Generate the 'Top 3 Papers of the Week' highlight section."""
    if not papers:
        return "<p>No papers available this week.</p>"

    client = get_client()

    # Format all papers
    papers_text = ""
    for i, paper in enumerate(papers[:30], 1):
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

For each of the top 3 papers, provide:
1. An attention-grabbing headline summarizing the key finding
2. Title and authors
3. A compelling 3-4 sentence explanation of what the paper found and why economists should care
4. The source link

Format as clean HTML for an email newsletter highlight box. Use:
- <div class="top-paper"> for each paper
- <h3> for the headline
- <p class="paper-meta"> for title/authors
- <p> for the description
- <a href="URL" class="read-more"> for the link

Make it engaging and accessible to both economists and interested general readers."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


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
2. Highlights 3-5 most interesting discussions with:
   - A catchy description of the topic/debate
   - The blog name
   - 1-2 sentences on the key argument or insight
   - Link to read more

Format as clean HTML for an email newsletter. Use:
- <h3> for each highlight
- <p> for descriptions
- <span class="source"> for blog name
- <a href="URL"> for links

Keep it lively and engaging. Total length around 200-300 words."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


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
