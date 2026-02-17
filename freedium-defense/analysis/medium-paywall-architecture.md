# Medium Paywall Architecture: Current State vs. Recommended State

## Current Architecture (Soft Paywall)

```
                    ┌─────────────────────────────────────────────┐
                    │              Medium Server                   │
                    │                                              │
  Any HTTP request  │   Next.js SSR renders FULL article HTML     │
  ────────────────► │   including article body in __NEXT_DATA__   │
  (no auth needed)  │                                              │
                    │   Returns: complete HTML with body text      │
                    └──────────────────┬──────────────────────────┘
                                       │ Full HTML response
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │              Browser                         │
                    │                                              │
                    │   JavaScript runs → checks subscription      │
                    │   status → shows/hides paywall overlay       │
                    │                                              │
                    │   ⚠ Content is ALREADY IN THE DOM           │
                    └─────────────────────────────────────────────┘

Freedium's attack surface: fetch the raw HTML, parse the body, serve it.
No authentication bypass required — the paywall never existed server-side.
```

---

## Recommended Architecture (Hard Paywall)

```
                    ┌─────────────────────────────────────────────┐
                    │              Medium Server                   │
                    │                                              │
  Any HTTP request  │   SSR renders article SHELL only:           │
  ────────────────► │   - Title, author, hero image, first 3 ¶   │
  (no auth needed)  │   - NO body text in __NEXT_DATA__           │
                    │                                              │
                    │   Returns: partial HTML (safe to cache/CDN) │
                    └──────────────────┬──────────────────────────┘
                                       │ Partial HTML
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │              Browser                         │
                    │                                              │
                    │   Client checks subscription status          │
                    │   via authenticated session                  │
                    │                                              │
                    │   If subscribed:                             │
                    │   ─────────────────────────────────────     │
                    │   POST /api/article/{id}/body               │
                    │   Authorization: Bearer <jwt>               │
                    │   ────────────────────────────────────►     │
                    │                                ┌────────┐   │
                    │                                │ Auth   │   │
                    │                                │ check  │   │
                    │                                └───┬────┘   │
                    │   ◄──────────────── article body  │        │
                    │                                              │
                    │   If not subscribed:                         │
                    │   → Show paywall overlay (no body to hide)  │
                    └─────────────────────────────────────────────┘

Freedium's attack surface: none. The body is never transmitted without auth.
```

---

## Migration Considerations for Medium Engineering

### What changes:

1. **Next.js data fetching layer**
   - `getServerSideProps` / `getStaticProps` must not include article body for
     unauthenticated sessions
   - Apollo cache preloading must be scoped by auth state

2. **New authenticated API endpoint**
   - `POST /api/v1/article/{id}/content`
   - Requires valid session JWT
   - Returns article body paragraphs as JSON
   - Rate-limited per account

3. **CDN/caching implications**
   - The article shell page (title, preview) becomes fully cacheable — good for performance
   - The authenticated body call cannot be cached at the CDN layer — accept this tradeoff

4. **SEO impact**
   - Google's crawler will no longer see full content → potential ranking impact
   - Mitigations:
     a. Use Google's [Flexible Sampling](https://developers.google.com/search/docs/appearance/flexible-sampling)
        program — allow Googlebot (verified by IP) to access full content
     b. Serve full content to verified Googlebot IPs only (see `countermeasures/platform/bot-verification.py`)
     c. Submit article text directly via Google's Indexing API for time-sensitive content

5. **Friend Links**
   - Should use short-lived signed tokens, not permanent URL parameters
   - Token grants temporary access via the authenticated body endpoint
   - Tokens expire after 72 hours; cached copies on Freedium become stale

---

## Transition Strategy (Phased Approach)

**Phase 1 (Low risk, quick wins):**
- Truncate RSS feeds for paywalled content
- Implement real Googlebot IP verification
- Block/challenge datacenter ASNs aggressively

**Phase 2 (Medium complexity):**
- Migrate article body out of `__NEXT_DATA__` for unauthenticated sessions
- Add authenticated body API endpoint
- Implement Friend Link token expiry

**Phase 3 (Full hard paywall):**
- Complete migration of all article body delivery to authenticated endpoint
- Retire soft paywall logic
- Enable verified Googlebot full-content access for SEO continuity
