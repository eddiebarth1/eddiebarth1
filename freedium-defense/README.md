# Freedium Defense

A research and tooling repository documenting how Freedium (freedium.cfd) bypasses
Medium's paywall, the harm this causes to writers, and a multi-pronged strategy to
address it — from individual writer protections to platform-level architectural fixes.

> **Important:** All tools in this repository are defensive in nature. They are designed
> to help writers monitor and protect their own content, collect evidence for legal action,
> and inform Medium's platform team about technical countermeasures. No tools here are
> designed to attack or disrupt any third-party service.

---

## The Problem

Medium writers choose to monetize their work through Medium's Partner Program. The paywall
is the mechanism that ensures readers pay for access and writers earn from their work.

Freedium is a reverse-proxy service that re-serves paywalled Medium articles without
authentication, stripping writers' revenue and violating Medium's Terms of Service and
individual writers' copyright.

Freedium works not by "hacking" Medium, but by exploiting an architectural weakness:
**Medium's paywall is enforced client-side (in the browser), not server-side.**
The complete article text is present in every HTTP response — Freedium simply serves
that response without running the JavaScript that displays the paywall overlay.

See `analysis/how-freedium-works.md` for the full technical breakdown.

---

## Repository Structure

```
freedium-defense/
│
├── analysis/                          Technical analysis of the vulnerability
│   ├── how-freedium-works.md          How Freedium bypasses the paywall (all vectors)
│   ├── vulnerability-assessment.md    Severity ratings for each vulnerability
│   └── medium-paywall-architecture.md Current vs. recommended architecture diagrams
│
├── detection/                         Tools for writers to monitor their content
│   ├── monitor_articles.py            Check if your articles appear on proxy sites
│   ├── friend_link_audit.py           Find publicly leaked Friend Links
│   └── content_fingerprint.py         Embed/detect invisible watermarks in articles
│
├── legal/                             Legal action resources
│   ├── dmca-template.md               DMCA notice templates (hosting, Cloudflare, Google)
│   ├── collect_evidence.py            Capture timestamped HTTP evidence for DMCA notices
│   └── hosting-provider-contacts.md   Abuse contacts for common hosting providers
│
└── countermeasures/
    ├── platform/                      For Medium's engineering team
    │   ├── hard-paywall-design.md     Full specification for a hard paywall migration
    │   ├── bot-verification.py        Googlebot IP verification (closes crawler spoof vector)
    │   └── tls-fingerprinting.md      Bot detection via TLS handshake fingerprinting
    │
    └── writer/
        └── writer-guide.md            Step-by-step guide for writers protecting their work
```

---

## Quickstart for Writers

**1. Check if your articles are on Freedium:**
```bash
pip install requests beautifulsoup4
echo "https://medium.com/@yourusername/your-article-slug" > articles.txt
python detection/monitor_articles.py --articles articles.txt
```

**2. Audit Friend Link leakage:**
```bash
python detection/friend_link_audit.py --username yourusername
```

**3. Collect evidence for a DMCA notice:**
```bash
pip install requests
python legal/collect_evidence.py \
    --original "https://medium.com/@you/article" \
    --infringing "https://freedium.cfd/https://medium.com/@you/article" \
    --output ./evidence
```

**4. File a DMCA notice:**
See `legal/dmca-template.md` for templates and `legal/hosting-provider-contacts.md`
for where to send them.

For the full guide, see `countermeasures/writer/writer-guide.md`.

---

## The Structural Fix

Writer-level tools slow the damage but cannot close the root vulnerability.
**The permanent fix requires Medium to implement a hard paywall:**

1. Article body content must only be served via an authenticated API call
2. Unauthenticated requests should receive metadata and preview only
3. Real Googlebot (verified by IP) should receive full content for SEO continuity

The complete engineering specification is in `countermeasures/platform/hard-paywall-design.md`.

---

## Contributing

If you discover new proxy domains serving Medium content, please open a pull request
to add them to `KNOWN_PROXY_DOMAINS` in `detection/monitor_articles.py`.

If you successfully obtain a DMCA takedown, please document the timeline and response
in an issue — this data helps establish patterns for future actions.

---

## Legal Disclaimer

The tools in this repository are provided for defensive, informational, and legal
evidence-collection purposes. This repository does not constitute legal advice.
Consult a qualified attorney before filing DMCA notices or taking legal action.

Knowingly submitting a false DMCA notice carries legal consequences under
17 U.S.C. § 512(f).
