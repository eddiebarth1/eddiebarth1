#!/usr/bin/env python3
"""
friend_link_audit.py

Scans public sources (social media search results, Google, forums) for your
Medium Friend Links being shared publicly. Public Friend Links are a direct
vector for Freedium to permanently cache your paywalled content.

This tool helps you identify which of your articles have had Friend Links
leaked publicly so you can request Medium to invalidate those links.

Usage:
    python friend_link_audit.py --username yourmediumhandle --output audit.json

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
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

REQUEST_DELAY_SECONDS = 3.0

# Patterns that indicate a Medium Friend Link
FRIEND_LINK_PATTERNS = [
    "source=friends_link",
    "sk=",  # older Medium friend link format
    "source=friend_link",
]

# Search engines and platforms where Friend Links might be publicly posted
SEARCH_TARGETS = [
    {
        "name": "Google (site search)",
        "url_template": (
            "https://www.google.com/search?q=site%3Amedium.com+%22{username}%22"
            "+%22friends_link%22&num=20"
        ),
    },
    {
        "name": "Google (friend link pattern)",
        "url_template": (
            "https://www.google.com/search?q=%22medium.com%2F{username}%22"
            "+%22source%3Dfriends_link%22&num=20"
        ),
    },
]


@dataclass
class FriendLinkLeak:
    article_url: str
    friend_link: str
    found_on_page: str
    source: str
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class AuditResult:
    username: str
    leaks: list[FriendLinkLeak] = field(default_factory=list)
    pages_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    audited_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def leak_count(self) -> int:
        return len(self.leaks)


def contains_friend_link(text: str) -> bool:
    """Check whether a string contains a Medium Friend Link pattern."""
    return any(pattern in text for pattern in FRIEND_LINK_PATTERNS)


def extract_friend_links_from_html(html: str, username: str) -> list[str]:
    """
    Extract Medium Friend Links from an HTML page.
    Returns list of Friend Link URLs found.
    """
    soup = BeautifulSoup(html, "html.parser")
    found_links = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "medium.com" in href and contains_friend_link(href):
            if username.lower() in href.lower():
                found_links.append(href)

    # Also search plain text (some pages render links as text)
    for text_node in soup.find_all(string=True):
        text = str(text_node)
        if "medium.com" in text and contains_friend_link(text) and username.lower() in text.lower():
            # Try to extract the URL
            import re
            urls = re.findall(
                r"https?://[^\s\"\'>]+medium\.com[^\s\"\'>]+(?:friends_link|sk=)[^\s\"\'>]*",
                text,
            )
            found_links.extend(urls)

    # Deduplicate
    return list(set(found_links))


def scan_search_results(
    username: str,
    session: requests.Session,
    result: AuditResult,
) -> None:
    """
    Scan search engine results pages for publicly visible Friend Links.
    Note: Search engines may block automated requests. This is best-effort.
    """
    for target in SEARCH_TARGETS:
        url = target["url_template"].format(username=quote_plus(username))
        log.info("Scanning: %s", target["name"])
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 429:
                log.warning(
                    "Rate limited by %s. Try running this tool less frequently "
                    "or use a search API key.",
                    target["name"],
                )
                result.errors.append(f"Rate limited: {target['name']}")
                time.sleep(REQUEST_DELAY_SECONDS * 3)
                continue
            if resp.status_code != 200:
                log.warning("HTTP %s from %s", resp.status_code, target["name"])
                continue

            result.pages_scanned += 1
            links = extract_friend_links_from_html(resp.text, username)
            for link in links:
                # Extract the base article URL (strip friend link params)
                base_url = link.split("?")[0]
                leak = FriendLinkLeak(
                    article_url=base_url,
                    friend_link=link,
                    found_on_page=url,
                    source=target["name"],
                )
                result.leaks.append(leak)
                log.warning("FRIEND LINK FOUND IN PUBLIC: %s", link)

        except requests.exceptions.RequestException as e:
            log.error("Error scanning %s: %s", target["name"], e)
            result.errors.append(f"{target['name']}: {e}")

        time.sleep(REQUEST_DELAY_SECONDS)


def check_social_platforms(
    username: str,
    session: requests.Session,
    result: AuditResult,
) -> None:
    """
    Check Twitter/X and Reddit for publicly shared Friend Links.
    These are common places where authors share Friend Links, sometimes
    not realizing they're publicly indexable.
    """
    social_searches = [
        {
            "name": "Twitter/X (via Nitter)",
            # Nitter is a Twitter front-end that allows search without login
            "url": f"https://nitter.net/search?q=medium.com+{username}+friends_link&f=tweets",
        },
        {
            "name": "Reddit (via search)",
            "url": f"https://www.reddit.com/search/?q=medium.com+{username}+friends_link",
        },
    ]

    for target in social_searches:
        log.info("Checking %s...", target["name"])
        try:
            resp = session.get(target["url"], timeout=20)
            if resp.status_code != 200:
                log.debug("HTTP %s from %s", resp.status_code, target["name"])
                continue

            result.pages_scanned += 1
            links = extract_friend_links_from_html(resp.text, username)
            for link in links:
                base_url = link.split("?")[0]
                leak = FriendLinkLeak(
                    article_url=base_url,
                    friend_link=link,
                    found_on_page=target["url"],
                    source=target["name"],
                )
                result.leaks.append(leak)
                log.warning("FRIEND LINK FOUND IN PUBLIC: %s", link)

        except Exception as e:
            log.debug("Error checking %s: %s", target["name"], e)

        time.sleep(REQUEST_DELAY_SECONDS)


def print_summary(result: AuditResult) -> None:
    print("\n" + "=" * 60)
    print("FRIEND LINK AUDIT SUMMARY")
    print("=" * 60)
    print(f"Username:       @{result.username}")
    print(f"Pages scanned:  {result.pages_scanned}")
    print(f"Leaks found:    {result.leak_count}")

    if result.errors:
        print(f"\nWarnings ({len(result.errors)}):")
        for e in result.errors:
            print(f"  - {e}")

    if result.leaks:
        print("\nEXPOSED FRIEND LINKS:")
        for leak in result.leaks:
            print(f"\n  Article:     {leak.article_url}")
            print(f"  Friend Link: {leak.friend_link}")
            print(f"  Found on:    {leak.source}")
            print(f"  Page:        {leak.found_on_page}")
        print()
        print("RECOMMENDED ACTIONS:")
        print("  1. Log into Medium and navigate to each affected article")
        print("  2. Disable or regenerate Friend Links for these articles")
        print("  3. File a DMCA notice for any cached copies (see legal/dmca-template.md)")
    else:
        print("\nNo publicly visible Friend Links found.")
        print("This does not guarantee no leaks exist — Freedium may have cached")
        print("content from links shared in private channels.")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit Medium Friend Links for public exposure"
    )
    parser.add_argument(
        "--username", required=True,
        help="Your Medium username (without @)"
    )
    parser.add_argument(
        "--output", default="friend_link_audit.json",
        help="Path to write JSON report (default: friend_link_audit.json)"
    )
    args = parser.parse_args()

    result = AuditResult(username=args.username)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    log.info("Starting Friend Link audit for @%s", args.username)
    scan_search_results(args.username, session, result)
    check_social_platforms(args.username, session, result)

    # Write report
    report = asdict(result)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    log.info("Report written to %s", args.output)

    print_summary(result)

    if result.leak_count > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
