# How Freedium Bypasses Medium's Paywall

## Overview

Freedium (freedium.cfd) is a reverse-proxy service that fetches Medium articles and
re-serves them without the paywall overlay. It exploits a fundamental architectural
weakness in Medium's paywall model rather than breaking any cryptographic protection.

---

## The Root Cause: A Soft Paywall

Medium's paywall is **client-side**. The complete article text is embedded in the
server's HTML response for *every* request — it is simply hidden by JavaScript and CSS
overlays at render time. This is commonly called a "soft" or "metered" paywall.

A **hard paywall**, by contrast, would require an authenticated API call to retrieve
article body content; unauthenticated requests would receive only metadata (title, author,
preview). Medium does not currently do this.

Because the content is always present in the raw response, any HTTP client — a browser
extension, a script, or a proxy like Freedium — can access it without ever authenticating.

---

## Attack Vectors Freedium Uses

### Vector 1: Search Crawler Impersonation

Medium deliberately serves full content to search engine crawlers (Googlebot, Bingbot, etc.)
so articles get indexed — this is what drives organic traffic and writer discoverability.

Freedium exploits this by sending requests with a spoofed `User-Agent` header:

```
User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
```

Medium's servers see this and respond with the full unpaywalled HTML.

**Why Medium doesn't catch this:** Properly verifying Googlebot requires a reverse DNS
lookup of the requesting IP against Google's published crawler IP ranges. Medium
apparently does not perform this check consistently.

Google publishes its crawler IP ranges at:
`https://developers.google.com/search/apis/ipranges/googlebot.json`

Any IP *not* in that list claiming to be Googlebot is an impersonator.

---

### Vector 2: Content Present in Raw HTML (`__NEXT_DATA__`)

Medium is a Next.js application. Next.js embeds server-side rendered state into the
page as a JSON blob inside `<script id="__NEXT_DATA__">`. This blob contains the full
Apollo GraphQL cache — including the complete article body — for hydration purposes.

Example structure (simplified):
```json
{
  "props": {
    "apolloState": {
      "Post:<article-id>": {
        "content": { "bodyModel": { "paragraphs": [...full article text...] } }
      }
    }
  }
}
```

Freedium (and any HTTP client) can parse this JSON directly from the HTML without
any additional requests or authentication.

---

### Vector 3: Friend Link Harvesting

Medium's "Friend Link" feature lets paying subscribers share a special URL that
bypasses the paywall for the recipient. These URLs look like:

```
https://medium.com/story-slug?source=friends_link&...
```

Freedium may harvest Friend Links posted publicly (on social media, forums, etc.)
and cache the corresponding fully-unlocked content. Once cached, anyone can access
it through Freedium regardless of whether the original Friend Link is still valid.

---

### Vector 4: RSS Feed Extraction

Medium publishes RSS feeds for authors and publications. Depending on configuration,
these feeds may contain full article text. Freedium can subscribe to these feeds and
extract content passively without ever touching the paywall.

Example RSS endpoint:
```
https://medium.com/feed/@username
```

---

### Vector 5: Aggressive Content Caching

Once an article has been fetched by any means, Freedium caches it on their servers.
Subsequent requests for that article never hit Medium's servers at all. This means:

- Blocking Freedium at the network level does not remove already-cached content
- Even if Medium patches the crawl vulnerability, historical content remains exposed
- Cache invalidation requires action from Freedium — which they are unlikely to take

---

## The Open Source Problem

Freedium's source code is publicly available on GitHub. This means:

1. The technique is fully documented and reproducible
2. Anyone can fork and run their own instance
3. Taking down Freedium.cfd does not eliminate the threat — forks proliferate

Any effective countermeasure must address the **architectural vulnerability** in
Medium's platform, not just suppress individual instances of this proxy.

---

## Summary of Exploited Weaknesses

| Weakness | Root Cause | Difficulty to Fix |
|---|---|---|
| Soft paywall (content in HTML) | Architecture | High — requires platform rework |
| No real Googlebot verification | Missing validation | Low — IP range check |
| `__NEXT_DATA__` exposure | Next.js default behavior | Medium — requires content splitting |
| Friend Link caching | Feature misuse | Medium — rate limit + expiry |
| RSS full-text exposure | Configuration | Low — truncate RSS feeds |
| No TLS/client fingerprinting | Missing detection | Medium — third-party service |
