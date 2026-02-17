#!/usr/bin/env python3
"""
collect_evidence.py

Captures timestamped evidence of copyright infringement for DMCA notices
and potential legal proceedings. For each infringing URL, it captures:
  - Full HTTP response headers (proves content is actively being served)
  - Response body (the actual infringing content)
  - SHA-256 hash of the response (proves content integrity)
  - Timestamp of capture (UTC, RFC 3339)
  - WHOIS information for the infringing domain

All evidence is written to a timestamped directory for preservation.

Usage:
    python collect_evidence.py \
        --original https://medium.com/@you/article-slug \
        --infringing https://freedium.cfd/https://medium.com/@you/article-slug \
        --output ./evidence

Requirements:
    pip install requests
    whois (system package: apt install whois / brew install whois)
"""

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(url: str) -> str:
    """Convert a URL into a safe filename component."""
    return (
        url.replace("https://", "")
           .replace("http://", "")
           .replace("/", "_")
           .replace(":", "_")
           [:80]  # Truncate to avoid OS filename limits
    )


def run_whois(domain: str) -> str:
    """Run whois lookup on a domain. Returns output or error message."""
    try:
        result = subprocess.run(
            ["whois", domain],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout or result.stderr
    except FileNotFoundError:
        return "whois command not found. Install with: apt install whois (Linux) or brew install whois (macOS)"
    except subprocess.TimeoutExpired:
        return "whois lookup timed out"
    except Exception as e:
        return f"whois error: {e}"


def capture_http_evidence(url: str, session: requests.Session) -> dict:
    """
    Capture full HTTP evidence for a URL.
    Returns a dict with headers, body hash, status code, etc.
    """
    log.info("Capturing HTTP evidence for: %s", url)
    captured_at = now_utc_iso()

    resp = session.get(url, timeout=30, allow_redirects=True)

    body_bytes = resp.content
    body_hash = sha256_of_bytes(body_bytes)

    return {
        "url": url,
        "final_url": resp.url,  # after redirects
        "captured_at": captured_at,
        "http_status": resp.status_code,
        "response_headers": dict(resp.headers),
        "body_size_bytes": len(body_bytes),
        "body_sha256": body_hash,
        "redirect_history": [
            {"url": r.url, "status": r.status_code}
            for r in resp.history
        ],
        "body_bytes": body_bytes,  # stored separately
    }


def extract_text_content(html: str) -> str:
    """
    Extract readable text from HTML for content comparison.
    Basic extraction without external dependencies.
    """
    import re
    # Remove script and style blocks
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute a rough text similarity score between two documents.
    Returns a value between 0.0 (no overlap) and 1.0 (identical).
    Uses word-level Jaccard similarity.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def save_evidence(
    evidence_dir: Path,
    original: dict,
    infringing: dict,
    similarity: float,
    whois_output: str,
) -> Path:
    """Save all evidence to a structured directory."""
    # Create timestamped evidence subdirectory
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_dir = evidence_dir / f"case_{ts}"
    case_dir.mkdir(parents=True, exist_ok=True)

    # Save original HTML
    (case_dir / "original_response.html").write_bytes(original["body_bytes"])

    # Save infringing HTML
    (case_dir / "infringing_response.html").write_bytes(infringing["body_bytes"])

    # Save WHOIS
    (case_dir / "whois.txt").write_text(whois_output)

    # Build evidence manifest (without the raw bytes — those are in separate files)
    original_manifest = {k: v for k, v in original.items() if k != "body_bytes"}
    infringing_manifest = {k: v for k, v in infringing.items() if k != "body_bytes"}

    manifest = {
        "case_directory": str(case_dir),
        "evidence_collected_at": now_utc_iso(),
        "original": original_manifest,
        "infringing": infringing_manifest,
        "content_similarity_score": round(similarity, 4),
        "similarity_interpretation": (
            "HIGH — strong evidence of content reproduction"
            if similarity > 0.7
            else "MEDIUM — substantial overlap" if similarity > 0.4
            else "LOW — limited overlap (verify manually)"
        ),
        "files": {
            "original_html": "original_response.html",
            "infringing_html": "infringing_response.html",
            "whois": "whois.txt",
            "manifest": "evidence_manifest.json",
        },
    }

    manifest_path = case_dir / "evidence_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return case_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture timestamped DMCA evidence for infringing content"
    )
    parser.add_argument(
        "--original", required=True,
        help="The original Medium article URL (your article)"
    )
    parser.add_argument(
        "--infringing", required=True,
        help="The infringing URL on Freedium or similar site"
    )
    parser.add_argument(
        "--output", default="./evidence",
        help="Directory to save evidence (default: ./evidence)"
    )
    args = parser.parse_args()

    evidence_dir = Path(args.output)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    })

    # Capture both URLs
    try:
        log.info("Fetching original article...")
        original_evidence = capture_http_evidence(args.original, session)
    except requests.RequestException as e:
        log.error("Failed to fetch original URL: %s", e)
        sys.exit(1)

    time.sleep(2)

    try:
        log.info("Fetching infringing copy...")
        infringing_evidence = capture_http_evidence(args.infringing, session)
    except requests.RequestException as e:
        log.error("Failed to fetch infringing URL: %s", e)
        sys.exit(1)

    # Compute similarity
    orig_text = extract_text_content(original_evidence["body_bytes"].decode("utf-8", errors="replace"))
    infr_text = extract_text_content(infringing_evidence["body_bytes"].decode("utf-8", errors="replace"))
    similarity = compute_similarity(orig_text, infr_text)

    # WHOIS lookup for infringing domain
    infringing_domain = urlparse(args.infringing).netloc
    log.info("Running WHOIS for %s...", infringing_domain)
    whois_output = run_whois(infringing_domain)

    # Save everything
    case_dir = save_evidence(
        evidence_dir,
        original_evidence,
        infringing_evidence,
        similarity,
        whois_output,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("EVIDENCE CAPTURE COMPLETE")
    print("=" * 60)
    print(f"Case directory: {case_dir}")
    print()
    print("Original article:")
    print(f"  URL:    {args.original}")
    print(f"  Status: HTTP {original_evidence['http_status']}")
    print(f"  Hash:   {original_evidence['body_sha256']}")
    print()
    print("Infringing copy:")
    print(f"  URL:    {args.infringing}")
    print(f"  Status: HTTP {infringing_evidence['http_status']}")
    print(f"  Hash:   {infringing_evidence['body_sha256']}")
    print(f"  Size:   {infringing_evidence['body_size_bytes']:,} bytes")
    print()
    print(f"Content similarity: {similarity:.1%}")
    if similarity > 0.7:
        print("  → HIGH similarity: strong evidence of content reproduction")
    elif similarity > 0.4:
        print("  → MEDIUM similarity: substantial overlap detected")
    else:
        print("  → LOW similarity: verify content match manually")
    print()
    print("Files saved:")
    for f in sorted(case_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name} ({size:,} bytes)")
    print()
    print("Next steps:")
    print("  1. Review evidence_manifest.json")
    print("  2. Take screenshots of the infringing page for your records")
    print("  3. File DMCA notice using legal/dmca-template.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
