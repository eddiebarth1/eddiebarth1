# TLS Fingerprinting for Bot Detection

## What Is TLS Fingerprinting?

When an HTTP client establishes a TLS connection, it sends a "ClientHello" message
that contains a list of supported cipher suites, extensions, and compression methods.
Different HTTP client libraries produce detectably different ClientHello signatures.

**JA3** (and the newer **JA4**) are standardized methods for hashing these signatures
into a short fingerprint. Real browsers (Chrome, Firefox, Safari) produce consistent,
well-known fingerprints. Automated HTTP clients produce different fingerprints:

| Client | JA3 Fingerprint |
|---|---|
| Chrome 121 (Mac) | `cd08e31494f9531f560d64c695473da4` |
| Firefox 121 | `b32309a26951912be7dba376398abc3b` |
| Python `requests` 2.31 | `6734f37431670b3ab4292b8f60f29984` |
| Go `net/http` 1.21 | `b56e0d4a3f0...` (varies slightly) |
| curl 7.88 | `e7d705a3286e19ea42f587b344ee6865` |

Freedium is likely built in Go or Python. Its TLS fingerprint will differ from
any real browser unless the developers went to significant effort to mimic browser TLS.

---

## Detection Approach

### Option 1: Cloudflare Bot Management

Cloudflare automatically collects JA3/JA4 fingerprints and uses them as one signal
in their bot scoring model. Medium already uses Cloudflare as a CDN — enabling
Bot Management (a paid add-on) would add this signal with zero engineering effort.

**Pros:** Immediate, no code changes, maintained by Cloudflare
**Cons:** Cost; Cloudflare sees all traffic (already the case if they're the CDN)

### Option 2: HAProxy / Nginx with JA3

If Medium terminates TLS at their own load balancers, they can add JA3 computation
at the edge and forward it as a request header.

**HAProxy example:**
```
# haproxy.cfg
frontend https_in
    bind *:443 ssl crt /etc/ssl/medium.pem alpn h2,http/1.1

    # Capture JA3 fingerprint (requires HAProxy 2.5+ with OpenSSL)
    http-request capture req.fhdr(X-JA3-Fingerprint) len 32

    default_backend app_servers

backend app_servers
    server app1 127.0.0.1:3000 check
    # Forward JA3 to application
    http-request set-header X-JA3-Fingerprint %[fc_ssl_fc_session_id]
```

**Nginx with ngx_http_ssl_fingerprint_module:**
```nginx
server {
    listen 443 ssl;
    ssl_ja3 on;
    ssl_ja3_header X-JA3-Fingerprint;

    proxy_pass http://app_servers;
    proxy_set_header X-JA3-Fingerprint $http_ssl_ja3;
}
```

The application then receives the JA3 fingerprint as `X-JA3-Fingerprint` header.

### Option 3: Application-Level Scoring

Use JA3 as one signal in a request scoring system:

```python
# Pseudocode — integrate into Medium's request middleware
KNOWN_BOT_JA3 = {
    "6734f37431670b3ab4292b8f60f29984",  # Python requests
    # Add more as identified from logs
}

KNOWN_BROWSER_JA3 = {
    "cd08e31494f9531f560d64c695473da4",  # Chrome 121
    "b32309a26951912be7dba376398abc3b",  # Firefox 121
    # etc.
}

def compute_bot_score(request) -> float:
    score = 0.0
    ja3 = request.headers.get("X-JA3-Fingerprint")
    user_agent = request.headers.get("User-Agent", "")

    # JA3 mismatch with claimed browser
    if "Chrome" in user_agent and ja3 not in KNOWN_BROWSER_JA3:
        score += 0.4  # Claiming to be Chrome but not using Chrome TLS

    if ja3 in KNOWN_BOT_JA3:
        score += 0.6  # Known automated client fingerprint

    # Datacenter IP
    if is_datacenter_ip(request.remote_addr):
        score += 0.3

    # Missing typical browser headers
    if "Accept-Language" not in request.headers:
        score += 0.2

    # Claimed Googlebot from non-Google IP
    if "googlebot" in user_agent.lower():
        if not is_verified_googlebot_ip(request.remote_addr):
            score += 0.9  # Near-certain bot

    return min(score, 1.0)


def handle_request(request):
    score = compute_bot_score(request)
    if score >= 0.8:
        # High confidence bot — serve preview only
        return serve_article_preview(request)
    elif score >= 0.5:
        # Uncertain — CAPTCHA challenge
        return serve_captcha_challenge(request)
    else:
        # Likely legitimate user
        return serve_normal_response(request)
```

---

## Limitations

TLS fingerprinting is **not a complete solution** — it raises the cost of attacks:

1. **Mimicry:** A sophisticated attacker can configure their HTTP client to mimic
   browser TLS parameters. Go's `tls` package is configurable; Python has `httpx`
   with TLS configuration. Freedium could update to mimic Chrome's JA3.

2. **Legitimate variety:** Browser updates change JA3 fingerprints. An allowlist
   of known-good fingerprints requires maintenance.

3. **Not a replacement for authentication:** TLS fingerprinting is a heuristic.
   The hard paywall (authenticated content API) is the durable fix.

**Use TLS fingerprinting as defense-in-depth, not as the primary defense.**

---

## JA4 (Improved Standard)

JA4 is a newer, more stable fingerprinting standard that is less sensitive to
implementation quirks. Consider adopting JA4 over JA3:

- **JA4:** https://github.com/FoxIO-LLC/ja4
- More stable across minor TLS library updates
- Better distinguishes between browser versions
- Cloudflare Bot Management supports JA4 natively

---

## Relevant Tools

- **JA3 database:** https://ja3er.com — community database of known JA3 fingerprints
- **Cloudflare Bot Management:** https://developers.cloudflare.com/bots/
- **DataDome:** https://datadome.co — bot protection with TLS fingerprinting
- **HUMAN Security (PerimeterX):** https://www.humansecurity.com
