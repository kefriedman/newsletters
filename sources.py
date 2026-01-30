"""
Data collection module for economics newsletter.
Highly selective - only the best papers from elite economists and top journals.
Quality over quantity.
"""

import feedparser
import requests
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import TypedDict
import xml.etree.ElementTree as ET


# Common headers for HTTP requests (some sites block default user-agents)
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EconNewsletter/1.0; +mailto:newsletter@example.com)"
}


class Paper(TypedDict):
    title: str
    authors: str
    abstract: str
    url: str
    source: str
    category: str
    published: str
    citation_score: int  # For ranking by impact


class BlogPost(TypedDict):
    title: str
    url: str
    summary: str
    source: str
    published: str


# RSS Feed URLs
FEEDS = {
    "nber": "https://www.nber.org/rss/new.xml",
    "marginal_revolution": "https://marginalrevolution.com/feed",
    "econlog": "https://www.econlib.org/feed/",
}

# OpenAlex API for journal articles
OPENALEX_API = "https://api.openalex.org/works"

# ELITE journals only - the Top 5 economics + top finance
ELITE_JOURNAL_IDS = [
    # The Top 5 Economics Journals
    "S23254222",   # American Economic Review
    "S95464858",   # Econometrica
    "S203860005",  # Quarterly Journal of Economics
    "S51782672",   # Journal of Political Economy
    "S4210234146", # Review of Economic Studies
    # Top 3 Finance
    "S182848088",  # Journal of Finance
    "S84095945",   # Review of Financial Studies
    "S36663441",   # Journal of Financial Economics
]

# Minimum author citation threshold for inclusion (highly cited = influential economist)
MIN_AUTHOR_CITATIONS = 5000  # Only include if at least one author has 5000+ citations

# Category keywords for classification
MICRO_KEYWORDS = [
    "microeconomic", "consumer", "firm", "market structure", "game theory",
    "auction", "labor", "industrial organization", "behavioral", "household",
    "price", "demand", "supply", "welfare", "incentive", "contract"
]
MACRO_KEYWORDS = [
    "macroeconomic", "gdp", "inflation", "monetary", "fiscal", "growth",
    "business cycle", "unemployment", "central bank", "interest rate",
    "aggregate", "recession", "policy", "federal reserve", "trade"
]
ECONOMETRICS_KEYWORDS = [
    "econometric", "causal", "regression", "instrumental", "difference-in-difference",
    "panel data", "time series", "identification", "estimation", "inference",
    "statistical", "machine learning", "prediction", "forecast"
]


def categorize_paper(title: str, abstract: str) -> str:
    """Categorize a paper based on title and abstract keywords."""
    text = (title + " " + abstract).lower()

    micro_score = sum(1 for kw in MICRO_KEYWORDS if kw in text)
    macro_score = sum(1 for kw in MACRO_KEYWORDS if kw in text)
    metrics_score = sum(1 for kw in ECONOMETRICS_KEYWORDS if kw in text)

    scores = {
        "Microeconomics": micro_score,
        "Macroeconomics": macro_score,
        "Econometrics": metrics_score
    }

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "General Economics"
    return best_category


def is_within_past_month(date_str: str) -> bool:
    """Check if a date string is within the past 28 days."""
    try:
        pub_date = date_parser.parse(date_str, ignoretz=True)
        month_ago = datetime.now() - timedelta(days=28)
        return pub_date >= month_ago
    except (ValueError, TypeError):
        return True  # Include if we can't parse the date


def is_within_past_week(date_str: str) -> bool:
    """Check if a date string is within the past 7 days (for blog posts)."""
    try:
        pub_date = date_parser.parse(date_str, ignoretz=True)
        week_ago = datetime.now() - timedelta(days=7)
        return pub_date >= week_ago
    except (ValueError, TypeError):
        return True


def fetch_nber_papers() -> list[Paper]:
    """
    Fetch recent NBER working papers.
    NBER papers are already selective - they're invited contributions from leading economists.
    """
    papers = []

    try:
        response = requests.get(FEEDS["nber"], headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except requests.RequestException as e:
        print(f"Error fetching NBER: {e}")
        return papers

    for entry in feed.entries:
        pub_date = entry.get("published", entry.get("updated", ""))
        if not is_within_past_month(pub_date):
            continue

        title = entry.get("title", "")
        abstract = entry.get("summary", entry.get("description", ""))

        paper: Paper = {
            "title": title,
            "authors": entry.get("author", "NBER"),
            "abstract": abstract[:1000] if abstract else "",
            "url": entry.get("link", ""),
            "source": "NBER Working Paper",
            "category": categorize_paper(title, abstract),
            "published": pub_date,
            "citation_score": 500,  # NBER = invited, pre-vetted, high quality
        }
        papers.append(paper)

    return papers


def fetch_elite_journal_articles() -> list[Paper]:
    """
    Fetch recent articles ONLY from elite economics journals (Top 5 + Top Finance).
    These are the gold standard of economics research.
    """
    papers = []

    # Past 28 days
    four_weeks_ago = datetime.now() - timedelta(days=28)
    from_date = four_weeks_ago.strftime("%Y-%m-%d")

    # Elite journals only
    source_filter = "|".join(ELITE_JOURNAL_IDS)

    params = {
        "filter": f"from_publication_date:{from_date},type:article,has_abstract:true,primary_location.source.id:{source_filter}",
        "sort": "publication_date:desc",
        "per_page": 50,
        "select": "id,doi,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count",
        "mailto": "newsletter@example.com",
    }

    try:
        response = requests.get(OPENALEX_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching elite journals: {e}")
        return papers

    for work in data.get("results", []):
        primary_location = work.get("primary_location", {})
        source = primary_location.get("source", {}) if primary_location else {}
        journal_name = source.get("display_name", "") if source else "Top Journal"

        # Reconstruct abstract
        abstract = ""
        abstract_inv = work.get("abstract_inverted_index", {})
        if abstract_inv:
            word_positions = []
            for word, positions in abstract_inv.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract = " ".join(word for _, word in word_positions)

        # Get authors
        authorships = work.get("authorships", [])
        authors = []
        max_author_citations = 0
        for authorship in authorships[:4]:
            author_info = authorship.get("author", {})
            if author_info:
                authors.append(author_info.get("display_name", ""))
                author_cited = author_info.get("cited_by_count", 0)
                if author_cited and author_cited > max_author_citations:
                    max_author_citations = author_cited
        author_str = ", ".join(authors)
        if len(authorships) > 4:
            author_str += "..."

        doi = work.get("doi", "")
        url = doi if doi else work.get("id", "")
        title = work.get("title", "")
        pub_date = work.get("publication_date", "")
        cited_by = work.get("cited_by_count", 0) or 0

        # Elite journal papers get high base score
        citation_score = 1000 + cited_by * 10 + (max_author_citations // 100)

        paper: Paper = {
            "title": title,
            "authors": author_str,
            "abstract": abstract[:1000] if abstract else "",
            "url": url,
            "source": journal_name,
            "category": categorize_paper(title, abstract),
            "published": pub_date,
            "citation_score": citation_score,
        }
        papers.append(paper)

    return papers


def fetch_papers_from_top_economists() -> list[Paper]:
    """
    Fetch recent papers from highly cited economists - ANY venue.
    The key filter is author reputation, not journal prestige.
    This captures what the best minds are working on, regardless of where it's published.
    """
    papers = []

    # Past 28 days
    four_weeks_ago = datetime.now() - timedelta(days=28)
    from_date = four_weeks_ago.strftime("%Y-%m-%d")

    # Query for economics papers
    params = {
        "filter": f"from_publication_date:{from_date},has_abstract:true,concepts.id:C162324750",
        "sort": "publication_date:desc",
        "per_page": 200,  # Get more to filter down by author quality
        "select": "id,doi,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,concepts",
        "mailto": "newsletter@example.com",
    }

    try:
        response = requests.get(OPENALEX_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching papers from top economists: {e}")
        return papers

    for work in data.get("results", []):
        # Check economics relevance (must be >= 40% economics)
        concepts = work.get("concepts", [])
        econ_score = 0
        for concept in concepts:
            if concept.get("id") == "https://openalex.org/C162324750":
                econ_score = concept.get("score", 0)
                break
        if econ_score < 0.4:
            continue

        # Check if any author meets the citation threshold
        authorships = work.get("authorships", [])
        authors = []
        max_author_citations = 0
        for authorship in authorships[:5]:
            author_info = authorship.get("author", {})
            if author_info:
                authors.append(author_info.get("display_name", ""))
                author_cited = author_info.get("cited_by_count", 0) or 0
                if author_cited > max_author_citations:
                    max_author_citations = author_cited

        # ONLY include if at least one author has MIN_AUTHOR_CITATIONS
        # This is the key filter - we want work from top economists
        if max_author_citations < MIN_AUTHOR_CITATIONS:
            continue

        author_str = ", ".join(authors[:4])
        if len(authors) > 4:
            author_str += "..."

        primary_location = work.get("primary_location", {})
        source = primary_location.get("source", {}) if primary_location else {}
        journal_name = source.get("display_name", "Working Paper") if source else "Working Paper"

        # Reconstruct abstract
        abstract = ""
        abstract_inv = work.get("abstract_inverted_index", {})
        if abstract_inv:
            word_positions = []
            for word, positions in abstract_inv.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract = " ".join(word for _, word in word_positions)

        doi = work.get("doi", "")
        url = doi if doi else work.get("id", "")
        title = work.get("title", "")
        pub_date = work.get("publication_date", "")
        cited_by = work.get("cited_by_count", 0) or 0

        # Score based on author influence (primary) + paper citations
        citation_score = (max_author_citations // 50) + cited_by * 10

        paper: Paper = {
            "title": title,
            "authors": author_str,
            "abstract": abstract[:1000] if abstract else "",
            "url": url,
            "source": journal_name,
            "category": categorize_paper(title, abstract),
            "published": pub_date,
            "citation_score": citation_score,
        }
        papers.append(paper)

    return papers


def fetch_blog_posts() -> list[BlogPost]:
    """Fetch recent posts from economics blogs."""
    posts = []

    blog_feeds = [
        ("Marginal Revolution", FEEDS["marginal_revolution"]),
        ("EconLog", FEEDS["econlog"]),
    ]

    for source_name, feed_url in blog_feeds:
        try:
            # Fetch with custom headers (some sites block default feedparser user-agent)
            response = requests.get(feed_url, headers=HTTP_HEADERS, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:10]:  # Limit to 10 per blog
                pub_date = entry.get("published", entry.get("updated", ""))
                if not is_within_past_week(pub_date):
                    continue

                summary = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags for cleaner summary
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
            print(f"Error fetching {source_name}: {e}")

    return posts


def fetch_all_papers() -> list[Paper]:
    """
    Fetch papers from elite sources only.
    Highly selective - quality over quantity.
    """
    all_papers = []

    print("Fetching from elite journals (Top 5 + Finance)...")
    all_papers.extend(fetch_elite_journal_articles())

    print("Fetching recent work from top economists...")
    all_papers.extend(fetch_papers_from_top_economists())

    print("Fetching NBER working papers...")
    all_papers.extend(fetch_nber_papers())

    # Remove duplicates by title (case-insensitive)
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)

    # Sort by citation score (high impact first)
    unique_papers.sort(key=lambda p: p.get("citation_score", 0), reverse=True)

    print(f"Total papers from elite sources: {len(unique_papers)}")
    return unique_papers


def get_papers_by_category(papers: list[Paper]) -> dict[str, list[Paper]]:
    """Group papers by category."""
    categories = {
        "Microeconomics": [],
        "Macroeconomics": [],
        "Econometrics": [],
        "General Economics": [],
    }

    for paper in papers:
        cat = paper.get("category", "General Economics")
        if cat in categories:
            categories[cat].append(paper)
        else:
            categories["General Economics"].append(paper)

    return categories


if __name__ == "__main__":
    # Test the data fetching
    papers = fetch_all_papers()
    posts = fetch_blog_posts()

    print(f"\nPapers by category:")
    for cat, cat_papers in get_papers_by_category(papers).items():
        print(f"  {cat}: {len(cat_papers)}")

    print(f"\nBlog posts: {len(posts)}")
