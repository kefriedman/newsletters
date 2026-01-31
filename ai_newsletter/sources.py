"""
Data collection module for AI newsletter.
Fetches papers from arXiv, company updates, newsletters, and trending GitHub repos.
"""

import feedparser
import requests
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import TypedDict
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup


# Common headers for HTTP requests
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AINewsletter/1.0; +mailto:newsletter@example.com)"
}


class Paper(TypedDict):
    title: str
    authors: str
    abstract: str
    url: str
    source: str
    category: str
    published: str
    citation_score: int


class BlogPost(TypedDict):
    title: str
    url: str
    summary: str
    source: str
    published: str


class Tool(TypedDict):
    name: str
    description: str
    url: str
    stars: int
    language: str
    stars_gained: str


# arXiv API endpoint
ARXIV_API = "http://export.arxiv.org/api/query"

# arXiv categories for AI/ML
ARXIV_CATEGORIES = [
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language (NLP)
    "cs.CV",   # Computer Vision
]

# Semantic Scholar API for citation data
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"

# RSS feeds for AI blogs and newsletters
FEEDS = {
    # Company blogs (RSS where available)
    "deepmind": "https://deepmind.google/blog/rss.xml",
    # AI newsletters (Substack feeds work reliably)
    "import_ai": "https://importai.substack.com/feed",
    "ahead_of_ai": "https://magazine.sebastianraschka.com/feed",
}

# Company pages to scrape (no RSS available)
COMPANY_PAGES = {
    "Anthropic": "https://www.anthropic.com/news",
}

# Category keywords for classification
LLM_KEYWORDS = [
    "language model", "llm", "transformer", "gpt", "bert", "attention",
    "text generation", "prompt", "fine-tuning", "instruction", "chat",
    "dialogue", "nlp", "natural language", "token", "embedding"
]
VISION_KEYWORDS = [
    "image", "vision", "visual", "diffusion", "generative", "gan",
    "object detection", "segmentation", "recognition", "video",
    "multimodal", "clip", "stable diffusion", "dalle", "midjourney"
]
RL_KEYWORDS = [
    "reinforcement learning", "rl", "agent", "reward", "policy",
    "q-learning", "actor-critic", "environment", "decision", "planning",
    "robotics", "control", "autonomous"
]
INFRA_KEYWORDS = [
    "inference", "optimization", "quantization", "distillation",
    "deployment", "serving", "training", "distributed", "gpu",
    "efficient", "speed", "latency", "throughput", "benchmark"
]


def categorize_paper(title: str, abstract: str) -> str:
    """Categorize a paper based on title and abstract keywords."""
    text = (title + " " + abstract).lower()

    llm_score = sum(1 for kw in LLM_KEYWORDS if kw in text)
    vision_score = sum(1 for kw in VISION_KEYWORDS if kw in text)
    rl_score = sum(1 for kw in RL_KEYWORDS if kw in text)
    infra_score = sum(1 for kw in INFRA_KEYWORDS if kw in text)

    scores = {
        "LLMs & Language Models": llm_score,
        "Computer Vision": vision_score,
        "RL & Agents": rl_score,
        "ML Infrastructure": infra_score
    }

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "General AI"
    return best_category


def is_within_past_week(date_str: str) -> bool:
    """Check if a date string is within the past 7 days."""
    try:
        pub_date = date_parser.parse(date_str, ignoretz=True)
        week_ago = datetime.now() - timedelta(days=7)
        return pub_date >= week_ago
    except (ValueError, TypeError):
        return True


def get_author_citations(author_name: str) -> int:
    """Get citation count for an author from Semantic Scholar."""
    try:
        # Search for author
        search_url = f"{SEMANTIC_SCHOLAR_API}/author/search"
        params = {"query": author_name, "limit": 1}
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("data"):
            author_id = data["data"][0].get("authorId")
            if author_id:
                # Get author details
                author_url = f"{SEMANTIC_SCHOLAR_API}/author/{author_id}"
                params = {"fields": "citationCount"}
                response = requests.get(author_url, params=params, timeout=10)
                response.raise_for_status()
                author_data = response.json()
                return author_data.get("citationCount", 0)
    except Exception:
        pass
    return 0


def fetch_arxiv_papers() -> list[Paper]:
    """
    Fetch recent AI/ML papers from arXiv.
    Uses arXiv API to get papers from relevant categories.
    """
    papers = []

    # Build query for AI/ML categories
    category_query = " OR ".join([f"cat:{cat}" for cat in ARXIV_CATEGORIES])

    # Past 7 days
    one_week_ago = datetime.now() - timedelta(days=7)

    params = {
        "search_query": f"({category_query})",
        "start": 0,
        "max_results": 50,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        response = requests.get(ARXIV_API, params=params, headers=HTTP_HEADERS, timeout=30)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        for entry in root.findall("atom:entry", ns):
            # Get publication date
            published = entry.find("atom:published", ns)
            if published is not None:
                pub_date = published.text
                if not is_within_past_week(pub_date):
                    continue
            else:
                pub_date = ""

            # Get title
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            # Get abstract
            abstract_elem = entry.find("atom:summary", ns)
            abstract = abstract_elem.text.strip().replace("\n", " ")[:1000] if abstract_elem is not None else ""

            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)
            author_str = ", ".join(authors[:4])
            if len(authors) > 4:
                author_str += "..."

            # Get URL
            url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "text/html":
                    url = link.get("href", "")
                    break
            if not url:
                id_elem = entry.find("atom:id", ns)
                url = id_elem.text if id_elem is not None else ""

            # Get primary category
            primary_cat = entry.find("arxiv:primary_category", ns)
            source = primary_cat.get("term", "arXiv") if primary_cat is not None else "arXiv"

            # Simple citation score based on category (cs.LG and cs.CL tend to be higher impact)
            base_score = 100
            if "cs.LG" in source or "cs.CL" in source:
                base_score = 150

            paper: Paper = {
                "title": title,
                "authors": author_str,
                "abstract": abstract,
                "url": url,
                "source": f"arXiv {source}",
                "category": categorize_paper(title, abstract),
                "published": pub_date,
                "citation_score": base_score,
            }
            papers.append(paper)

    except requests.RequestException as e:
        print(f"Error fetching arXiv papers: {e}")

    print(f"  arXiv: {len(papers)} papers")
    return papers


def fetch_company_updates() -> list[BlogPost]:
    """Fetch updates from major AI company blogs via RSS or scraping."""
    posts = []

    # Fetch from RSS feeds that work
    rss_feeds = [
        ("Google DeepMind", FEEDS.get("deepmind")),
    ]

    for source_name, feed_url in rss_feeds:
        if not feed_url:
            continue

        try:
            response = requests.get(feed_url, headers=HTTP_HEADERS, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:10]:
                pub_date = entry.get("published", entry.get("updated", ""))
                if not is_within_past_week(pub_date):
                    continue

                summary = entry.get("summary", entry.get("description", ""))
                summary = re.sub(r'<[^>]+>', '', summary)[:500]

                post: BlogPost = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": summary,
                    "source": source_name,
                    "published": pub_date,
                }
                posts.append(post)

            print(f"  {source_name}: {len([p for p in posts if p['source'] == source_name])} posts")

        except Exception as e:
            print(f"  {source_name}: error - {e}")

    # Scrape company news pages
    for source_name, page_url in COMPANY_PAGES.items():
        try:
            response = requests.get(page_url, headers=HTTP_HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Find article links - look for common patterns
            articles = []

            # Try finding article cards/links
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                # Look for news/research article links
                if any(x in href for x in ["/news/", "/research/", "/blog/"]):
                    title = a.get_text(strip=True)
                    if title and len(title) > 10 and len(title) < 200:
                        full_url = href if href.startswith("http") else f"https://{page_url.split('/')[2]}{href}"
                        articles.append((title, full_url))

            # Deduplicate and limit
            seen = set()
            count = 0
            for title, url in articles:
                if title not in seen and count < 5:
                    seen.add(title)
                    post: BlogPost = {
                        "title": title,
                        "url": url,
                        "summary": "",
                        "source": source_name,
                        "published": "",
                    }
                    posts.append(post)
                    count += 1

            print(f"  {source_name}: {count} posts")

        except Exception as e:
            print(f"  {source_name}: error - {e}")

    return posts


def fetch_newsletter_posts() -> list[BlogPost]:
    """Fetch posts from AI newsletters."""
    posts = []

    newsletter_feeds = [
        ("Import AI", FEEDS.get("import_ai")),
        ("Ahead of AI", FEEDS.get("ahead_of_ai")),
    ]

    for source_name, feed_url in newsletter_feeds:
        if not feed_url:
            continue

        try:
            response = requests.get(feed_url, headers=HTTP_HEADERS, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:5]:
                pub_date = entry.get("published", entry.get("updated", ""))
                if not is_within_past_week(pub_date):
                    continue

                summary = entry.get("summary", entry.get("description", ""))
                summary = re.sub(r'<[^>]+>', '', summary)[:500]

                post: BlogPost = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": summary,
                    "source": source_name,
                    "published": pub_date,
                }
                posts.append(post)

            print(f"  {source_name}: {len([p for p in posts if p['source'] == source_name])} posts")

        except Exception as e:
            print(f"  {source_name}: error - {e}")

    return posts


def fetch_github_trending() -> list[Tool]:
    """Fetch trending ML/AI repositories from GitHub."""
    tools = []

    # GitHub trending page for machine-learning topic
    trending_url = "https://github.com/trending?since=weekly&spoken_language_code=en"

    try:
        response = requests.get(trending_url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article", class_="Box-row")

        ai_keywords = ["ai", "ml", "llm", "gpt", "transformer", "neural", "deep-learning",
                       "machine-learning", "nlp", "vision", "diffusion", "model", "inference"]

        for article in articles[:30]:
            try:
                # Get repo name and URL
                h2 = article.find("h2")
                if not h2:
                    continue
                a_tag = h2.find("a")
                if not a_tag:
                    continue

                repo_path = a_tag.get("href", "").strip("/")
                repo_name = repo_path.split("/")[-1] if "/" in repo_path else repo_path
                repo_url = f"https://github.com/{repo_path}"

                # Get description
                p_tag = article.find("p")
                description = p_tag.text.strip() if p_tag else ""

                # Check if it's AI/ML related
                text_to_check = (repo_name + " " + description).lower()
                if not any(kw in text_to_check for kw in ai_keywords):
                    continue

                # Get language
                lang_span = article.find("span", itemprop="programmingLanguage")
                language = lang_span.text.strip() if lang_span else ""

                # Get stars
                stars_text = ""
                for span in article.find_all("span", class_="d-inline-block"):
                    svg = span.find("svg", class_="octicon-star")
                    if svg:
                        stars_text = span.text.strip().replace(",", "")
                        break

                stars = int(stars_text) if stars_text.isdigit() else 0

                # Get stars gained this week
                stars_gained = ""
                gain_span = article.find("span", class_="d-inline-block float-sm-right")
                if gain_span:
                    stars_gained = gain_span.text.strip()

                tool: Tool = {
                    "name": repo_name,
                    "description": description[:300],
                    "url": repo_url,
                    "stars": stars,
                    "language": language,
                    "stars_gained": stars_gained,
                }
                tools.append(tool)

            except Exception:
                continue

    except requests.RequestException as e:
        print(f"Error fetching GitHub trending: {e}")

    print(f"  GitHub trending: {len(tools)} AI/ML repos")
    return tools


def fetch_all_papers() -> list[Paper]:
    """Fetch papers from all sources."""
    print("Fetching arXiv papers...")
    papers = fetch_arxiv_papers()

    # Sort by citation score
    papers.sort(key=lambda p: p.get("citation_score", 0), reverse=True)

    # Remove duplicates by title
    seen_titles = set()
    unique_papers = []
    for paper in papers:
        title_lower = paper["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)

    print(f"Total papers: {len(unique_papers)}")
    return unique_papers


def fetch_all_blog_posts() -> list[BlogPost]:
    """Fetch blog posts from all sources."""
    posts = []

    print("Fetching company updates...")
    posts.extend(fetch_company_updates())

    print("Fetching newsletter posts...")
    posts.extend(fetch_newsletter_posts())

    print(f"Total blog posts: {len(posts)}")
    return posts


def fetch_all_tools() -> list[Tool]:
    """Fetch trending AI/ML tools."""
    print("Fetching GitHub trending repos...")
    tools = fetch_github_trending()
    return tools


def get_papers_by_category(papers: list[Paper]) -> dict[str, list[Paper]]:
    """Group papers by category."""
    categories = {
        "LLMs & Language Models": [],
        "Computer Vision": [],
        "RL & Agents": [],
        "ML Infrastructure": [],
        "General AI": [],
    }

    for paper in papers:
        cat = paper.get("category", "General AI")
        if cat in categories:
            categories[cat].append(paper)
        else:
            categories["General AI"].append(paper)

    return categories


if __name__ == "__main__":
    # Test the data fetching
    print("=" * 60)
    print("AI Newsletter Data Collection Test")
    print("=" * 60)
    print()

    papers = fetch_all_papers()
    posts = fetch_all_blog_posts()
    tools = fetch_all_tools()

    print()
    print("Papers by category:")
    for cat, cat_papers in get_papers_by_category(papers).items():
        print(f"  {cat}: {len(cat_papers)}")

    print(f"\nBlog posts: {len(posts)}")
    print(f"Trending tools: {len(tools)}")
