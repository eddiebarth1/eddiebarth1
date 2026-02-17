# Writer's Guide: Protecting Your Medium Content

This guide is for Medium writers who want to monitor and protect their paywalled
articles from unauthorized distribution on Freedium and similar proxy sites.

---

## Step 1: Check if Your Articles Are Exposed

Use the monitoring script to check whether your articles are currently being
served on Freedium or other known proxy sites.

**Setup:**
```bash
cd detection/
pip install requests beautifulsoup4

# Create a list of your article URLs
cat > my_articles.txt << 'EOF'
https://medium.com/@yourusername/article-title-abc123
https://medium.com/@yourusername/another-article-def456
# Add all your paywalled articles here
EOF

# Run the check
python monitor_articles.py --articles my_articles.txt --output report.json
```

The script will tell you which articles are currently indexed on proxy sites
and generate a JSON report you can use when filing DMCA notices.

**Set it up to run automatically (weekly check):**
```bash
# Add to your crontab (crontab -e)
0 9 * * 1 cd /path/to/freedium-defense/detection && \
    python monitor_articles.py --articles my_articles.txt --output report.json
```

---

## Step 2: Watermark Your Articles

Content fingerprinting embeds an invisible mark in your article text. If your
content appears on Freedium, the watermark:

1. Confirms it is definitively your work (not a coincidental similarity)
2. Provides a technical trail for DMCA notices and legal proceedings

**How to use:**
```bash
cd detection/

# Save your article text to a file
# (copy-paste from Medium editor, or use their export feature)
cat > my_article.txt << 'EOF'
[paste your article text here]
EOF

# Embed the fingerprint
python content_fingerprint.py fingerprint \
    --input my_article.txt \
    --output my_article_watermarked.txt \
    --article-id "article-title-abc123def" \
    --author "yourusername"

# Copy the watermarked text back into Medium
# The watermark is invisible — readers will see nothing different
```

**To verify a scraped copy contains your watermark:**
```bash
# Save the scraped content to a file
python content_fingerprint.py detect --input scraped_article.txt
```

Note: Some proxy sites strip zero-width Unicode characters. This method works
best when combined with monitoring and legal action, not as a standalone defense.

---

## Step 3: Audit Your Friend Links

Medium's Friend Links are a major exposure vector. If you've ever shared a
Friend Link publicly (on Twitter, in a newsletter, in a blog comment), that
link may be cached by Freedium.

```bash
cd detection/
python friend_link_audit.py --username yourusername --output audit.json
```

**If leaks are found:**
1. Log into Medium → go to the affected article → Settings
2. Find the "Friend Link" section and click "Disable" or "Generate new link"
3. The old link is now invalid, but Freedium may have cached the content already
4. Proceed to Step 4 (DMCA filing) for cached copies

**Best practices going forward:**
- Only share Friend Links in private messages (DM, email) — not public posts
- Generate a new Friend Link for each sharing occasion if possible
- Avoid sharing Friend Links on platforms that index posts publicly

---

## Step 4: File a DMCA Notice

If your article is found on Freedium:

1. **Collect evidence** using the evidence collector:
   ```bash
   cd legal/
   pip install requests

   python collect_evidence.py \
       --original "https://medium.com/@you/article-slug" \
       --infringing "https://freedium.cfd/https://medium.com/@you/article-slug" \
       --output ./evidence
   ```
   This creates a timestamped package with HTTP response headers, body hashes,
   content similarity scores, and WHOIS data.

2. **Identify the hosting provider:**
   ```bash
   dig freedium.cfd          # get the IP
   curl https://ipinfo.io/<IP>/json  # identify the provider
   ```

3. **File the DMCA notice** using the template in `legal/dmca-template.md`
   - Send to the hosting provider's abuse contact
   - CC the domain registrar if applicable
   - Submit a Google de-indexing request (Template 4 in the DMCA doc)

4. **Follow up** if no response within 14 business days

---

## Step 5: Report to Medium

Medium's support team should be aware when their platform's content is being
systematically scraped. File a report through:

- **Medium Help Center:** https://help.medium.com/hc/en-us/requests/new
- **Subject:** "Unauthorized redistribution of my paywalled content via Freedium"
- Include: article URLs, Freedium URLs, evidence from the collect_evidence.py output

Medium has greater legal standing to pursue platform-level action against Freedium
than individual writers do — your report builds their case.

---

## Realistic Expectations

Be aware of the limitations:

| Action | What it achieves | What it doesn't achieve |
|---|---|---|
| DMCA to hosting provider | Removes article from Freedium (if they comply) | Doesn't prevent future caching |
| Google de-indexing | Removes Freedium URL from search results | Content still accessible via direct URL |
| Watermarking | Proves ownership; supports legal action | Doesn't prevent scraping |
| Friend Link audit | Identifies and closes leakage vectors | Doesn't recover already-cached content |
| Reporting to Medium | Builds Medium's case for legal action | No immediate effect |

**The structural fix is Medium implementing a hard paywall.** Writer-level tools
are valuable for documentation, legal action, and reducing ongoing exposure, but
they cannot permanently close the vulnerability that Freedium exploits.

---

## Keeping the Proxy Domain List Updated

As Freedium forks proliferate, new proxy domains will emerge. You can help:

1. When you discover a new proxy domain serving Medium content, open an issue
   or pull request adding it to `KNOWN_PROXY_DOMAINS` in `detection/monitor_articles.py`
2. Note the discovery date and the domain registrar/hosting provider
3. File DMCA notices against new instances as they appear

---

## Quick Reference

```bash
# Check if articles are exposed
python detection/monitor_articles.py --articles articles.txt

# Watermark an article
python detection/content_fingerprint.py fingerprint --input article.txt \
    --output article_watermarked.txt --article-id SLUG --author USERNAME

# Detect watermark in scraped content
python detection/content_fingerprint.py detect --input scraped.txt

# Audit Friend Links
python detection/friend_link_audit.py --username USERNAME

# Collect DMCA evidence
python legal/collect_evidence.py \
    --original ORIGINAL_URL \
    --infringing INFRINGING_URL \
    --output ./evidence
```
