# Hard Paywall Design: Engineering Specification

## Executive Summary

Medium's current soft paywall places article body content in the server's HTML
response for every request. Freedium exploits this by acting as a reverse proxy.
The permanent solution is migrating to a hard paywall: article body content is
only delivered via an authenticated API call that verifies subscription status
server-side.

This document is a technical specification for that migration, intended for
Medium's engineering team.

---

## Current Data Flow (Vulnerable)

```
1. User visits https://medium.com/@author/article-slug
2. Next.js SSR runs getServerSideProps
3. Apollo fetches FULL article data (including body) from Medium's internal API
4. Body is embedded in __NEXT_DATA__ JSON in the HTML response
5. Browser receives HTML with complete article text
6. JavaScript shows/hides paywall overlay based on subscription state
   (content already present in DOM — overlay is purely cosmetic)
```

**Freedium's attack:** Skip step 6. Parse `__NEXT_DATA__` directly. Content retrieved.

---

## Target Data Flow (Hard Paywall)

```
1. User visits https://medium.com/@author/article-slug
2. Next.js SSR runs getServerSideProps
3. Apollo fetches ONLY article METADATA (title, author, preview, tags)
   from Medium's internal API — NO body content
4. Body is NOT in __NEXT_DATA__
5. Browser receives HTML with preview only
6. Client-side: check subscription status via /api/session
7a. If subscribed:
    → POST /api/v1/content/{articleId}
       Authorization: Bearer <session_jwt>
    → Server verifies JWT + subscription status
    → Returns article body paragraphs as JSON
    → Client renders article
7b. If not subscribed:
    → Show paywall CTA (nothing to hide — body was never transmitted)
```

**Freedium's attack surface:** None. The body is never transmitted without auth.

---

## API Specification

### Authenticated Content Endpoint

```
POST /api/v1/content/{articleId}

Request Headers:
    Authorization: Bearer <session_jwt>
    Content-Type: application/json
    X-Medium-Client: web/1.0   (client version for deprecation tracking)

Request Body: (empty or optional preferences)
    {}

Response (200 OK — subscribed user):
    {
      "articleId": "abc123def456",
      "content": {
        "paragraphs": [
          { "id": "p1", "type": "P", "text": "First paragraph..." },
          { "id": "p2", "type": "H3", "text": "Section heading" },
          { "id": "p3", "type": "P", "text": "..." }
        ],
        "sections": [...],
        "images": [...]
      },
      "servedAt": "2025-01-01T00:00:00Z"
    }

Response (401 Unauthorized — no valid session):
    { "error": "authentication_required" }

Response (403 Forbidden — valid session but not subscribed):
    { "error": "subscription_required", "upgradeUrl": "https://medium.com/membership" }

Response (429 Too Many Requests):
    { "error": "rate_limit_exceeded", "retryAfter": 60 }
```

### Rate Limiting

- Per-account: 200 article body requests per hour (generous for normal reading)
- Per-IP (unauthenticated): 0 — endpoint requires auth
- Anomaly detection: flag accounts requesting >50 unique articles/hour

### Session JWT Requirements

The session JWT must:
- Be signed with a secret not accessible to the browser (HttpOnly cookie approach)
- Include `subscriptionStatus` claim, refreshed on subscription state changes
- Have a short expiry (e.g., 1 hour) with silent refresh via refresh token
- Be bound to the user agent and IP subnet to limit token theft utility

---

## Frontend Implementation Notes

### Next.js / Apollo Changes

**Current (remove this):**
```javascript
// pages/[...slug].js
export async function getServerSideProps(context) {
  const apolloClient = initializeApollo();
  // ❌ This fetches full article including body — visible in __NEXT_DATA__
  await apolloClient.query({
    query: GET_FULL_ARTICLE,
    variables: { id: articleId },
  });
  return { props: { apolloState: apolloClient.cache.extract() } };
}
```

**Target (replace with):**
```javascript
// pages/[...slug].js
export async function getServerSideProps(context) {
  const apolloClient = initializeApollo();
  // ✅ Only fetch metadata — safe to include in __NEXT_DATA__
  await apolloClient.query({
    query: GET_ARTICLE_METADATA,  // title, author, preview, tags — NO body
    variables: { id: articleId },
  });
  return { props: { apolloState: apolloClient.cache.extract() } };
}
```

**Client-side body fetch:**
```javascript
// components/ArticleBody.js
useEffect(() => {
  if (!isSubscribed) return;  // Don't even attempt if not subscribed

  fetch(`/api/v1/content/${articleId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${sessionJwt}`,
      'Content-Type': 'application/json',
    },
  })
  .then(res => {
    if (res.status === 403) { showPaywall(); return null; }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then(data => {
    if (data) renderArticleBody(data.content);
  });
}, [articleId, isSubscribed, sessionJwt]);
```

---

## SEO Continuity Plan

The primary reason Medium uses a soft paywall is SEO — Google needs to see full
article content to index and rank it. A hard paywall breaks this.

**Solution: Verified Crawler Access**

Allow verified Googlebot (confirmed via rDNS + IP range check — see
`countermeasures/platform/bot-verification.py`) to access full content
via a separate, rate-limited endpoint that does not require a session token.

```
GET /api/v1/content/{articleId}/search-index
X-Crawler-Verified: googlebot   (set by your middleware after rDNS check)

Response (only accessible from verified crawler IPs):
    { "paragraphs": [...full content...] }
```

Alternative/supplement: Use Google's Indexing API to push article content directly.

---

## Friend Link Migration

Replace permanent Friend Link URL parameters with short-lived signed tokens:

**Current (vulnerable):**
```
https://medium.com/article-slug?source=friends_link&sk=<permanent-token>
```

**Target:**
```
https://medium.com/article-slug?friend_token=<jwt>
```

JWT claims:
```json
{
  "articleId": "abc123",
  "issuedAt": 1704067200,
  "expiresAt": 1704240000,   // 48 hours
  "issuerId": "subscriber-user-id",
  "singleUse": false,         // allow multiple reads within TTL
  "maxReads": 50              // prevent viral public sharing
}
```

Friend Link content delivery:
- Browser presents `friend_token` JWT to `/api/v1/content/{articleId}`
- Server validates token signature, expiry, and read count
- Returns article body if valid
- Logs each access for anomaly detection

---

## Rollout Strategy

**Phase 1 — Quick wins (no user impact):**
- Deploy Googlebot IP verification middleware
- Truncate RSS feeds to preview text for paywalled articles
- Add datacenter ASN detection + aggressive CAPTCHA challenge

**Phase 2 — Body content isolation:**
- Remove article body from `__NEXT_DATA__` for unauthenticated/unsubscribed sessions
- Deploy authenticated body API endpoint
- Update Next.js page to client-fetch body
- A/B test on 5% of traffic; validate no subscriber experience regression

**Phase 3 — Friend Link hardening:**
- Migrate Friend Links to expiring signed tokens
- Enforce read limits and anomaly detection
- Deprecate old `?source=friends_link` format (30-day transition)

**Phase 4 — Full hard paywall:**
- Roll out to 100% of traffic
- Retire soft paywall JavaScript
- Monitor SEO metrics closely for 60 days
