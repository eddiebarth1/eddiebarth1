#!/usr/bin/env python3
"""
bot-verification.py

Reference implementation: verifying that a request claiming to be from
Googlebot (or other major crawlers) is actually from that crawler's
legitimate infrastructure.

Medium serves full article content to Googlebot for SEO indexing.
Freedium exploits this by spoofing the Googlebot User-Agent header.
This module shows how to correctly verify crawler identity, closing
the impersonation vector.

This is a REFERENCE IMPLEMENTATION for Medium's engineering team.
It is not a deployable service on its own — it demonstrates the
verification logic that should be incorporated into Medium's
request handling middleware.

Usage example (as a library):
    from bot_verification import is_verified_crawler
    if is_verified_crawler(request_ip, request_user_agent):
        # serve full content
    else:
        # serve metered/paywalled content

Requirements:
    pip install requests dnspython
"""

import ipaddress
import json
import logging
import re
import socket
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from urllib.request import urlopen

log = logging.getLogger(__name__)

# URLs where major search engines publish their crawler IP ranges
CRAWLER_IP_RANGE_SOURCES = {
    "googlebot": "https://developers.google.com/search/apis/ipranges/googlebot.json",
    "google-special-crawlers": "https://developers.google.com/search/apis/ipranges/special-crawlers.json",
    "bingbot": None,  # Bing does not publish a machine-readable IP range list; use rDNS only
}

# User-Agent pattern → expected reverse DNS suffix for verification
# Source: https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers
CRAWLER_RDNS_PATTERNS = {
    "googlebot": [
        r"googlebot\.com$",
        r"google\.com$",
    ],
    "bingbot": [
        r"search\.msn\.com$",
    ],
    "applebot": [
        r"applebot\.apple\.com$",
    ],
    "yandexbot": [
        r"yandex\.(?:ru|net|com)$",
    ],
    "duckduckbot": [
        r"duckduckgo\.com$",
    ],
    "baiduspider": [
        r"crawl\.baidu\.(?:com|jp)$",
    ],
}

# User-Agent strings → crawler identity key
UA_TO_CRAWLER_KEY = {
    "googlebot": "googlebot",
    "google-inspectiontool": "googlebot",
    "google-read-aloud": "googlebot",
    "mediapartners-google": "googlebot",
    "bingbot": "bingbot",
    "msnbot": "bingbot",
    "applebot": "applebot",
    "yandexbot": "yandexbot",
    "yandex": "yandexbot",
    "duckduckbot": "duckduckbot",
    "baiduspider": "baiduspider",
}

# Cache TTL for IP range lists (4 hours)
IP_RANGE_CACHE_TTL = 4 * 3600

_ip_range_cache: dict[str, tuple[list, float]] = {}


@dataclass
class CrawlerVerificationResult:
    ip_address: str
    user_agent: str
    claimed_crawler: Optional[str]   # what the UA claims to be
    rdns_hostname: Optional[str]      # actual reverse DNS result
    rdns_verified: bool               # rDNS + forward DNS match confirmed
    ip_range_verified: bool           # IP is in published range (where available)
    is_legitimate: bool               # final verdict
    reason: str                       # human-readable explanation


def extract_crawler_identity(user_agent: str) -> Optional[str]:
    """
    Determine which crawler (if any) a User-Agent string claims to be.
    Returns the crawler key or None if not a known crawler UA.
    """
    ua_lower = user_agent.lower()
    for ua_fragment, crawler_key in UA_TO_CRAWLER_KEY.items():
        if ua_fragment in ua_lower:
            return crawler_key
    return None


def reverse_dns_lookup(ip: str) -> Optional[str]:
    """
    Perform a reverse DNS (PTR) lookup for an IP address.
    Returns the hostname or None if lookup fails.
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError) as e:
        log.debug("rDNS lookup failed for %s: %s", ip, e)
        return None


def forward_dns_lookup(hostname: str) -> list[str]:
    """
    Perform a forward DNS (A/AAAA) lookup for a hostname.
    Returns list of IP addresses.
    """
    try:
        results = socket.getaddrinfo(hostname, None)
        return list(set(r[4][0] for r in results))
    except (socket.gaierror, OSError) as e:
        log.debug("Forward DNS lookup failed for %s: %s", hostname, e)
        return []


def verify_rdns(ip: str, crawler_key: str) -> tuple[bool, Optional[str]]:
    """
    Verify crawler identity via reverse + forward DNS.

    Algorithm (as documented by Google):
    1. Perform rDNS lookup on the IP → get hostname
    2. Check that the hostname matches expected crawler domain patterns
    3. Perform forward DNS on that hostname → get IPs
    4. Confirm the original IP appears in the forward DNS results

    Returns (is_verified, hostname)
    """
    hostname = reverse_dns_lookup(ip)
    if not hostname:
        return False, None

    # Check hostname against expected patterns for this crawler
    patterns = CRAWLER_RDNS_PATTERNS.get(crawler_key, [])
    hostname_matches = any(
        re.search(pattern, hostname, re.IGNORECASE) for pattern in patterns
    )
    if not hostname_matches:
        log.debug(
            "rDNS hostname %r does not match expected patterns for %s",
            hostname, crawler_key
        )
        return False, hostname

    # Forward DNS confirmation
    forward_ips = forward_dns_lookup(hostname)
    if ip in forward_ips:
        log.debug("Crawler %s verified via rDNS: %s → %s", crawler_key, ip, hostname)
        return True, hostname
    else:
        log.debug(
            "Forward DNS for %s returned %s, does not include %s",
            hostname, forward_ips, ip
        )
        return False, hostname


def fetch_ip_ranges(crawler_key: str) -> list[str]:
    """
    Fetch the published IP ranges for a crawler that provides them.
    Results are cached for IP_RANGE_CACHE_TTL seconds.
    Returns list of CIDR strings.
    """
    now = time.time()
    if crawler_key in _ip_range_cache:
        ranges, cached_at = _ip_range_cache[crawler_key]
        if now - cached_at < IP_RANGE_CACHE_TTL:
            return ranges

    source_url = CRAWLER_IP_RANGE_SOURCES.get(crawler_key)
    if not source_url:
        return []

    try:
        with urlopen(source_url, timeout=10) as resp:
            data = json.loads(resp.read())
        # Google's format: {"prefixes": [{"ipv4Prefix": "..."}, {"ipv6Prefix": "..."}]}
        ranges = []
        for prefix_entry in data.get("prefixes", []):
            cidr = prefix_entry.get("ipv4Prefix") or prefix_entry.get("ipv6Prefix")
            if cidr:
                ranges.append(cidr)
        _ip_range_cache[crawler_key] = (ranges, now)
        log.debug("Fetched %d IP ranges for %s", len(ranges), crawler_key)
        return ranges
    except Exception as e:
        log.warning("Failed to fetch IP ranges for %s: %s", crawler_key, e)
        return []


def verify_ip_range(ip: str, crawler_key: str) -> bool:
    """
    Check whether an IP falls within the published IP ranges for a crawler.
    Returns False (not verified) if ranges are not available for this crawler.
    """
    ranges = fetch_ip_ranges(crawler_key)
    if not ranges:
        return False  # Can't verify via IP range; fall back to rDNS only

    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in ranges:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                if ip_obj in network:
                    return True
            except ValueError:
                continue
    except ValueError as e:
        log.warning("Invalid IP address %r: %s", ip, e)

    return False


def is_verified_crawler(
    ip_address: str,
    user_agent: str,
    require_both_checks: bool = False,
) -> CrawlerVerificationResult:
    """
    Verify whether a request is from a legitimate search engine crawler.

    Parameters:
        ip_address: The client IP address from the request
        user_agent: The User-Agent header value
        require_both_checks: If True, require BOTH rDNS AND IP range verification.
                            If False (default), either check passing is sufficient.
                            rDNS-only is appropriate for crawlers that don't publish
                            IP ranges (e.g., Bingbot).

    Returns a CrawlerVerificationResult with full details and a final verdict.
    """
    claimed_crawler = extract_crawler_identity(user_agent)

    if not claimed_crawler:
        return CrawlerVerificationResult(
            ip_address=ip_address,
            user_agent=user_agent,
            claimed_crawler=None,
            rdns_hostname=None,
            rdns_verified=False,
            ip_range_verified=False,
            is_legitimate=False,
            reason="User-Agent does not claim to be a known search crawler",
        )

    # Run rDNS verification
    rdns_verified, rdns_hostname = verify_rdns(ip_address, claimed_crawler)

    # Run IP range verification (where available)
    ip_range_verified = verify_ip_range(ip_address, claimed_crawler)

    # Determine final verdict
    if require_both_checks:
        has_ip_ranges = bool(CRAWLER_IP_RANGE_SOURCES.get(claimed_crawler))
        if has_ip_ranges:
            is_legitimate = rdns_verified and ip_range_verified
            reason = (
                "Verified via rDNS and IP range"
                if is_legitimate
                else "Failed one or both verification checks"
            )
        else:
            # Can only do rDNS for this crawler
            is_legitimate = rdns_verified
            reason = (
                f"Verified via rDNS (no published IP ranges for {claimed_crawler})"
                if is_legitimate
                else "rDNS verification failed"
            )
    else:
        is_legitimate = rdns_verified or ip_range_verified
        if rdns_verified and ip_range_verified:
            reason = "Verified via rDNS and IP range"
        elif rdns_verified:
            reason = "Verified via rDNS"
        elif ip_range_verified:
            reason = "Verified via IP range"
        else:
            reason = f"Impersonation detected: claims to be {claimed_crawler} but verification failed"

    return CrawlerVerificationResult(
        ip_address=ip_address,
        user_agent=user_agent,
        claimed_crawler=claimed_crawler,
        rdns_hostname=rdns_hostname,
        rdns_verified=rdns_verified,
        ip_range_verified=ip_range_verified,
        is_legitimate=is_legitimate,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Example usage and CLI demonstration
# ---------------------------------------------------------------------------

def demo() -> None:
    """Demonstrate the verifier with a few test cases."""
    test_cases = [
        {
            "description": "Legitimate Googlebot (Google IP range)",
            # This is a real Googlebot IP — safe to use in examples
            "ip": "66.249.66.1",
            "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        },
        {
            "description": "Spoofed Googlebot from datacenter IP (Freedium-style)",
            "ip": "5.9.0.1",  # Hetzner IP range
            "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        },
        {
            "description": "Legitimate browser (Chrome)",
            "ip": "1.2.3.4",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
        },
    ]

    for case in test_cases:
        print(f"\n{'─' * 60}")
        print(f"Test: {case['description']}")
        print(f"  IP: {case['ip']}")
        print(f"  UA: {case['ua'][:80]}...")
        result = is_verified_crawler(case["ip"], case["ua"])
        verdict = "LEGITIMATE CRAWLER" if result.is_legitimate else "NOT VERIFIED / BLOCKED"
        print(f"  Result: {verdict}")
        print(f"  Reason: {result.reason}")
        if result.rdns_hostname:
            print(f"  rDNS:   {result.rdns_hostname}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    demo()
