#!/usr/bin/env python3
"""
monitor_articles.py

Checks whether your Medium articles are being served by Freedium or similar
paywall-bypass proxies. Designed to run as a scheduled job (cron, GitHub Action, etc.)

Usage:
    python monitor_articles.py --articles articles.txt --output report.json

articles.txt format (one Medium URL per line):
    https://medium.com/@yourname/your-article-slug-abc123
    https://yourpublication.medium.com/article-slug-def456

Requirements:
    pip install requests beautifulsoup4
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urlencode

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Known paywall-bypass proxy domains. Add new instances here as they are discovered.
KNOWN_PROXY_DOMAINS = [
    "freedium.cfd",
    "readmedium.com",
    "scribe.rip",
    "archive.ph",          # not Medium-specific but commonly used to bypass paywalls
    "12ft.io",             # generic paywall bypass
]

# Delay between requests to avoid rate-limiting
REQUEST_DELAY_SECONDS = 2.0


@dataclass
class ArticleCheckResult:
    original_url: str
    article_title: Optional[str] = None
    slug: Optional[str] = None
    proxy_hits: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def is_exposed(self) -> bool:
        return len(self.proxy_hits) > 0


def extract_medium_slug(url: str) -> Optional[str]:
    """Extract the article slug/ID from a Medium URL."""
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        # Medium slugs end with a hex ID like 'my-article-title-abc123def456'
        return path_parts[-1]
    return None


def fetch_article_title(url: str, session: requests.Session) -> Optional[str]:
    """Fetch the title of a Medium article from its Open Graph metadata."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content")
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.text.strip()
    except Exception as e:
        log.warning("Could not fetch title for %s: %s", url, e)
    return None


def build_proxy_url(proxy_domain: str, original_url: str) -> str:
    """Construct the expected URL for an article on a given proxy domain."""
    if proxy_domain == "freedium.cfd":
        return f"https://freedium.cfd/{original_url}"
    if proxy_domain == "12ft.io":
        return f"https://12ft.io/proxy?q={original_url}"
    if proxy_domain == "archive.ph":
        # archive.ph requires a search; we construct the search URL
        return f"https://archive.ph/{original_url}"
    # Generic: proxy.domain/original_url
    return f"https://{proxy_domain}/{original_url}"


def check_proxy(
    proxy_domain: str,
    original_url: str,
    slug: str,
    session: requests.Session,
) -> Optional[dict]:
    """
    Check whether a specific proxy domain is serving this article.

    Returns a dict with evidence if found, None otherwise.
    """
    proxy_url = build_proxy_url(proxy_domain, original_url)
    try:
        resp = session.get(proxy_url, timeout=20, allow_redirects=True)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            log.debug("%s → HTTP %s for %s", proxy_domain, resp.status_code, slug)
            return None

        # Check whether the response body contains the article slug,
        # which strongly suggests the article is being served
        if slug.lower() in resp.text.lower():
            log.warning("EXPOSED: %s found on %s", slug, proxy_domain)
            return {
                "proxy_domain": proxy_domain,
                "proxy_url": proxy_url,
                "http_status": resp.status_code,
                "response_length_bytes": len(resp.content),
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }

    except requests.exceptions.Timeout:
        log.debug("Timeout checking %s for %s", proxy_domain, slug)
    except requests.exceptions.RequestException as e:
        log.debug("Request error checking %s: %s", proxy_domain, e)
    return None


def check_article(url: str, session: requests.Session) -> ArticleCheckResult:
    """Run all proxy checks for a single Medium article URL."""
    result = ArticleCheckResult(original_url=url)

    slug = extract_medium_slug(url)
    if not slug:
        result.errors.append(f"Could not extract slug from URL: {url}")
        return result
    result.slug = slug

    log.info("Checking article: %s", slug)

    result.article_title = fetch_article_title(url, session)
    if result.article_title:
        log.info("  Title: %s", result.article_title)

    time.sleep(REQUEST_DELAY_SECONDS)

    for proxy_domain in KNOWN_PROXY_DOMAINS:
        hit = check_proxy(proxy_domain, url, slug, session)
        if hit:
            result.proxy_hits.append(hit)
        time.sleep(REQUEST_DELAY_SECONDS)

    return result


def load_article_urls(filepath: str) -> list[str]:
    """Load article URLs from a text file, one URL per line."""
    urls = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def print_summary(results: list[ArticleCheckResult]) -> None:
    exposed = [r for r in results if r.is_exposed]
    clean = [r for r in results if not r.is_exposed]

    print("\n" + "=" * 60)
    print("MONITORING SUMMARY")
    print("=" * 60)
    print(f"Total articles checked: {len(results)}")
    print(f"Exposed on proxy sites: {len(exposed)}")
    print(f"Clean:                  {len(clean)}")

    if exposed:
        print("\nEXPOSED ARTICLES:")
        for r in exposed:
            title = r.article_title or r.slug
            print(f"\n  {title}")
            print(f"  Original: {r.original_url}")
            for hit in r.proxy_hits:
                print(f"  ⚠  Found on {hit['proxy_domain']}: {hit['proxy_url']}")

    if not exposed:
        print("\nNo articles found on known proxy sites.")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor Medium articles for paywall-bypass proxy exposure"
    )
    parser.add_argument(
        "--articles",
        required=True,
        help="Path to text file with Medium article URLs (one per line)",
    )
    parser.add_argument(
        "--output",
        default="report.json",
        help="Path to write JSON report (default: report.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    urls = load_article_urls(args.articles)
    if not urls:
        log.error("No article URLs found in %s", args.articles)
        sys.exit(1)

    log.info("Loaded %d article URLs", len(urls))

    session = requests.Session()
    # Use a realistic browser User-Agent for our own monitoring requests
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        }
    )

    results: list[ArticleCheckResult] = []
    for url in urls:
        result = check_article(url, session)
        results.append(result)

    # Write JSON report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_checked": len(results),
        "total_exposed": sum(1 for r in results if r.is_exposed),
        "articles": [asdict(r) for r in results],
    }
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    log.info("Report written to %s", args.output)

    print_summary(results)

    # Exit with non-zero code if any articles are exposed (useful for CI)
    if any(r.is_exposed for r in results):
        sys.exit(2)


if __name__ == "__main__":
    main()
