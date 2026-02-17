#!/usr/bin/env python3
"""
content_fingerprint.py

Embeds invisible, unique fingerprints (watermarks) into article text.
When your content appears on Freedium or similar sites, the watermark
lets you identify the source copy and confirm it is your work.

This is a steganographic text watermark — it uses Unicode homoglyphs,
zero-width characters, and subtle whitespace variations that are invisible
to readers but detectable programmatically.

Usage:
    # Fingerprint an article (adds invisible watermark)
    python content_fingerprint.py fingerprint \
        --input article.txt \
        --output article_watermarked.txt \
        --article-id "my-article-abc123" \
        --author "yourname"

    # Detect and decode fingerprint from scraped content
    python content_fingerprint.py detect \
        --input scraped_content.txt

Requirements:
    pip install hashlib  # stdlib, no extra deps needed
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# Zero-width Unicode characters used for binary encoding.
# These are invisible in most renderers (browsers, Medium editor, etc.)
ZWS = "\u200b"   # Zero-width space  → binary 0
ZWNJ = "\u200c"  # Zero-width non-joiner → binary 1
SEPARATOR = "\u200d"  # Zero-width joiner → separator between bytes

# Maximum fingerprint payload in bits
FINGERPRINT_BITS = 32


def text_to_bits(text: str) -> str:
    """Convert text to a binary string."""
    return "".join(format(ord(c), "08b") for c in text)


def bits_to_text(bits: str) -> str:
    """Convert a binary string back to text."""
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return "".join(chr(int(c, 2)) for c in chars if len(c) == 8)


def encode_fingerprint(payload: str) -> str:
    """
    Encode a short string payload as invisible Unicode characters.
    Returns a string of zero-width characters to be injected into text.
    """
    bits = text_to_bits(payload)
    encoded = SEPARATOR
    for bit in bits:
        encoded += ZWS if bit == "0" else ZWNJ
    encoded += SEPARATOR
    return encoded


def decode_fingerprint(text: str) -> str | None:
    """
    Extract and decode a fingerprint payload from text containing
    zero-width characters. Returns the payload string or None.
    """
    if SEPARATOR not in text:
        return None

    # Extract content between separators
    parts = text.split(SEPARATOR)
    if len(parts) < 3:
        return None

    # The fingerprint payload is between the first and last separator
    encoded_bits = parts[1]
    bits = ""
    for char in encoded_bits:
        if char == ZWS:
            bits += "0"
        elif char == ZWNJ:
            bits += "1"

    if not bits:
        return None

    try:
        return bits_to_text(bits)
    except Exception:
        return None


def create_payload(article_id: str, author: str) -> str:
    """
    Create a short fingerprint payload that fits within FINGERPRINT_BITS.
    Format: first 4 chars of author + first 4 chars of hash of article_id
    """
    article_hash = hashlib.sha256(article_id.encode()).hexdigest()[:4]
    author_short = author.replace(" ", "")[:4].lower()
    return f"{author_short}{article_hash}"


def inject_fingerprint(text: str, fingerprint: str) -> str:
    """
    Inject invisible fingerprint into article text.
    Places the fingerprint after the first sentence to avoid detection
    via simple prefix inspection.
    """
    # Find a natural injection point — after the first period
    injection_point = text.find(". ")
    if injection_point == -1:
        # Fall back to after the first line
        injection_point = text.find("\n")
    if injection_point == -1:
        # Last resort: prepend
        return fingerprint + text

    # Inject after the period + space
    return (
        text[: injection_point + 2]
        + fingerprint
        + text[injection_point + 2:]
    )


def strip_zero_width(text: str) -> str:
    """Remove all zero-width characters from text."""
    for char in [ZWS, ZWNJ, SEPARATOR]:
        text = text.replace(char, "")
    return text


def cmd_fingerprint(args: argparse.Namespace) -> None:
    """Subcommand: embed a fingerprint into an article."""
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    article_text = input_path.read_text(encoding="utf-8")
    payload = create_payload(args.article_id, args.author)
    fingerprint = encode_fingerprint(payload)
    watermarked = inject_fingerprint(article_text, fingerprint)

    output_path.write_text(watermarked, encoding="utf-8")

    # Write fingerprint record for later detection/verification
    record = {
        "article_id": args.article_id,
        "author": args.author,
        "payload": payload,
        "fingerprinted_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
    }
    record_path = output_path.with_suffix(".fingerprint.json")
    record_path.write_text(json.dumps(record, indent=2))

    print(f"Fingerprint embedded successfully.")
    print(f"  Payload: {payload!r}")
    print(f"  Output:  {output_path}")
    print(f"  Record:  {record_path}")
    print()
    print("IMPORTANT: Copy the watermarked output (not the original) to Medium.")
    print("The watermark is invisible to readers but detectable in scraped copies.")


def cmd_detect(args: argparse.Namespace) -> None:
    """Subcommand: detect and decode a fingerprint from scraped text."""
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    scraped_text = input_path.read_text(encoding="utf-8")

    # Check for zero-width characters
    has_zws = ZWS in scraped_text
    has_zwnj = ZWNJ in scraped_text
    has_separator = SEPARATOR in scraped_text

    print("Zero-width character analysis:")
    print(f"  Zero-width space (U+200B):        {'FOUND' if has_zws else 'not found'}")
    print(f"  Zero-width non-joiner (U+200C):   {'FOUND' if has_zwnj else 'not found'}")
    print(f"  Zero-width joiner (U+200D):        {'FOUND' if has_separator else 'not found'}")

    payload = decode_fingerprint(scraped_text)
    if payload:
        print(f"\nFingerprint DETECTED.")
        print(f"  Decoded payload: {payload!r}")
        print()
        print("This payload can be matched against your fingerprint records.")
        print("Check *.fingerprint.json files in your fingerprinted article outputs.")

        # Try to match against local fingerprint records
        records = list(Path(".").glob("**/*.fingerprint.json"))
        if records:
            print(f"\nChecking {len(records)} local fingerprint record(s)...")
            for record_path in records:
                try:
                    record = json.loads(record_path.read_text())
                    if record.get("payload") == payload:
                        print(f"\nMATCH FOUND:")
                        print(f"  Article ID:  {record['article_id']}")
                        print(f"  Author:      {record['author']}")
                        print(f"  Fingerprinted: {record['fingerprinted_at']}")
                        print(f"  Record file: {record_path}")
                except Exception:
                    pass
    else:
        print("\nNo fingerprint detected in this content.")
        print("Possible reasons:")
        print("  - Content was not fingerprinted with this tool")
        print("  - The proxy stripped zero-width characters (some do)")
        print("  - Content was reformatted before reaching the proxy")

    # Count occurrences as a rough measure of fingerprint preservation
    zws_count = scraped_text.count(ZWS)
    zwnj_count = scraped_text.count(ZWNJ)
    sep_count = scraped_text.count(SEPARATOR)
    print(f"\nRaw counts: ZWS={zws_count}, ZWNJ={zwnj_count}, SEP={sep_count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed and detect invisible fingerprints in Medium article text"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fingerprint subcommand
    fp_parser = subparsers.add_parser(
        "fingerprint", help="Embed a fingerprint into an article"
    )
    fp_parser.add_argument("--input", required=True, help="Path to article text file")
    fp_parser.add_argument(
        "--output", required=True, help="Path to write fingerprinted article"
    )
    fp_parser.add_argument(
        "--article-id", required=True,
        help="Your Medium article slug or ID (e.g. my-article-abc123def)"
    )
    fp_parser.add_argument(
        "--author", required=True,
        help="Your Medium username or name"
    )

    # detect subcommand
    det_parser = subparsers.add_parser(
        "detect", help="Detect a fingerprint in scraped article text"
    )
    det_parser.add_argument(
        "--input", required=True,
        help="Path to scraped text file to analyze"
    )

    args = parser.parse_args()

    if args.command == "fingerprint":
        cmd_fingerprint(args)
    elif args.command == "detect":
        cmd_detect(args)


if __name__ == "__main__":
    main()
