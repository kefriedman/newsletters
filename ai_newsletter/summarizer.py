"""
AI summarization module using Claude API.
Generates newsletter content focused on practical AI news and highlights.
"""

import os
import re
from anthropic import Anthropic
from sources import Paper, BlogPost, Tool


def get_client() -> Anthropic:
    """Initialize Anthropic client."""
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences and headers from Claude's response."""
    # Remove ```html ... ``` or ``` ... ``` wrappers
    text = re.sub(r'^```(?:html)?\s*\n?', '', text.strip())
    text = re.sub(r'\n?```\s*$', '', text.strip())
    # Remove markdown headers at the start (## Title, # Title, etc.)
    text = re.sub(r'^#{1,3}\s+[^\n]+\n*', '', text.strip())
    return text


def summarize_news(posts: list[BlogPost]) -> str:
    """Generate the main news section from company updates and newsletters."""
    if not posts:
        return "<p>No major AI news this week.</p>"

    client = get_client()

    posts_text = ""
    for i, post in enumerate(posts[:15], 1):
        posts_text += f"""
{i}. {post['title']}
   Source: {post['source']}
   Summary: {post['summary']}
   URL: {post['url']}
---
"""

    prompt = f"""You are writing the main section of a weekly AI newsletter for practitioners who want to stay current.

Here are this week's updates from major AI companies and newsletters:

{posts_text}

Write a "This Week in AI" section that:
1. Opens with 2-3 sentences summarizing the biggest AI news this week
2. Covers 4-6 key stories, each with:
   - A bold headline capturing what happened
   - 2-3 sentences explaining what it is and why it matters for practitioners
   - Link to read more
3. Prioritize: new model releases, product launches, major capability updates, important policy/safety news

Focus on practical implications - what do readers need to know to stay current and apply AI effectively?

Format as clean HTML:
- <h3> for story headlines
- <p> for descriptions
- <a href="URL"> for links
- <strong> for emphasis

Keep it scannable. Around 300-400 words total."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def summarize_tools(tools: list[Tool]) -> str:
    """Generate a summary of trending AI/ML tools."""
    if not tools:
        return "<p>No trending tools this week.</p>"

    client = get_client()

    tools_text = ""
    for i, tool in enumerate(tools[:10], 1):
        tools_text += f"""
{i}. {tool['name']}
   Description: {tool['description']}
   Language: {tool['language']}
   Stars: {tool['stars']} ({tool['stars_gained']})
   URL: {tool['url']}
---
"""

    prompt = f"""You are curating trending AI/ML tools for practitioners.

Here are this week's trending GitHub repositories:

{tools_text}

Highlight 3-5 useful tools. Do NOT include any section headers or titles - just the tool entries.

Format as HTML with each tool as its own <p> tag:
<p><strong><a href="URL">Tool Name</a></strong> — Description of what it does. Good for [who should use it].</p>
<p><strong><a href="URL">Another Tool</a></strong> — Description here. Good for [audience].</p>

Keep each tool description to 2-3 sentences max. Output ONLY the <p> tags, nothing else."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def summarize_research(papers: list[Paper]) -> str:
    """Generate a brief research highlights section - only the most impactful papers."""
    if not papers:
        return "<p>No notable research this week.</p>"

    client = get_client()

    # Only include top 20 papers for consideration
    papers_text = ""
    for i, paper in enumerate(papers[:20], 1):
        papers_text += f"""
{i}. {paper['title']}
   Authors: {paper['authors']}
   Abstract: {paper['abstract'][:500]}
   URL: {paper['url']}
---
"""

    prompt = f"""You are selecting research highlights for AI practitioners (not academics).

From these recent papers, pick the 2-3 most important ones that practitioners should know about:

{papers_text}

Write a "Research Worth Knowing" section that:
1. Only includes papers with clear practical implications
2. For each paper:
   - A plain-English headline (not the academic title)
   - 2-3 sentences on what they found and why it matters for applied AI
   - Link to the paper
3. Skip highly theoretical papers - focus on work that could impact how people build or use AI

Format as clean HTML:
- <h3> for headlines
- <p> for descriptions
- <a href="URL"> for links

Keep it brief - around 150-200 words total. Quality over quantity."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return strip_markdown_fences(response.content[0].text)


def generate_newsletter_content(
    papers_by_category: dict[str, list[Paper]],
    blog_posts: list[BlogPost],
    tools: list[Tool]
) -> dict[str, str]:
    """Generate all newsletter content sections."""

    # Flatten papers
    all_papers = []
    for papers in papers_by_category.values():
        all_papers.extend(papers)

    print("Generating news section...")
    news = summarize_news(blog_posts)

    print("Generating tools section...")
    tools_section = summarize_tools(tools)

    print("Generating research highlights...")
    research = summarize_research(all_papers)

    return {
        "news": news,
        "tools": tools_section,
        "research": research,
    }
