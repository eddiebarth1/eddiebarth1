# DMCA Takedown Notice Templates

These templates are provided for informational purposes. Before sending a DMCA notice,
consult with a qualified attorney. Knowingly submitting a false DMCA notice carries
legal consequences under 17 U.S.C. § 512(f).

---

## Template 1: Notice to Freedium's Hosting Provider

Send this to the abuse contact of Freedium's current hosting provider.
To find their hosting provider: `dig freedium.cfd` then look up the IP at https://ipinfo.io

---

**Subject:** DMCA Takedown Notice — Copyright Infringement by freedium.cfd

To Whom It May Concern,

I am writing pursuant to the Digital Millennium Copyright Act (DMCA), 17 U.S.C. § 512,
to notify you of copyright infringement occurring on a site hosted on your infrastructure.

**My Information (Copyright Owner):**
- Name: [YOUR FULL LEGAL NAME]
- Address: [YOUR ADDRESS]
- Email: [YOUR EMAIL]
- Phone: [YOUR PHONE] *(optional but recommended)*

**Description of Copyrighted Work:**
I am the original author and copyright owner of the following articles published on
Medium.com:

| Article Title | Original URL | Date Published |
|---|---|---|
| [ARTICLE TITLE 1] | [https://medium.com/@you/article-slug] | [DATE] |
| [ARTICLE TITLE 2] | [https://medium.com/@you/article-slug] | [DATE] |

These works are protected by copyright under 17 U.S.C. § 102 and applicable
international copyright law. I have not licensed or authorized freedium.cfd to
reproduce, distribute, or publicly display these works.

**Location of Infringing Material:**
The following URLs on your hosted service (freedium.cfd) are reproducing my
copyrighted works in their entirety without authorization:

| Infringing URL | Corresponding Original |
|---|---|
| [https://freedium.cfd/https://medium.com/@you/article-slug] | [original URL] |

**Good Faith Statement:**
I have a good faith belief that the use of the copyrighted material described above
is not authorized by the copyright owner, its agent, or the law.

**Accuracy Statement:**
I swear, under penalty of perjury, that the information in this notification is accurate
and that I am the copyright owner or am authorized to act on behalf of the copyright owner.

**Electronic Signature:**
/s/ [YOUR FULL NAME]
[DATE]

---

## Template 2: Notice to Cloudflare (if Freedium uses Cloudflare)

If Freedium uses Cloudflare, submit to: https://www.cloudflare.com/abuse/

Use the "DMCA Copyright Infringement" category.

Key points to include:
- Cloudflare is a "service provider" under DMCA § 512
- Their safe harbor protection depends on responding expeditiously to valid notices
- Request they terminate service to freedium.cfd under their repeat infringer policy

---

## Template 3: Notice to Domain Registrar

To find the registrar: `whois freedium.cfd`

Most registrars have an abuse contact listed in the WHOIS record.

**Subject:** Copyright Infringement — Domain freedium.cfd

While domain registrars are not typically liable for hosted content, many have
abuse policies that allow suspension of domains used for systematic copyright
infringement. Reference your jurisdiction's applicable law.

---

## Template 4: Google DMCA Removal (De-indexing)

To remove infringing Freedium URLs from Google Search results:

1. Visit: https://reportcontent.google.com/forms/dmca
2. Select "Web Search"
3. Enter the Freedium URL(s) as the "infringing URL"
4. Enter your original Medium URL as the "original work"

This does not remove the content from Freedium but prevents it from appearing
in search results, which significantly reduces traffic to the infringing copies.

---

## Evidence to Collect Before Filing

Use `legal/collect_evidence.py` to capture timestamped evidence of infringement.
You will need:

1. **Screenshots** of the infringing page (timestamped)
2. **HTTP response headers** (proves the content is being served)
3. **Side-by-side comparison** of original and infringing content
4. **Proof of authorship** (your Medium account, publication date)

Keep all evidence in original digital form — do not crop, edit, or alter screenshots.

---

## After Filing

- **Hosting provider response time:** Typically 10–14 business days under DMCA safe harbor
- **If no response:** Escalate to the upstream network provider (transit ASN)
- **If content persists:** Consult an attorney about a John Doe lawsuit to subpoena
  Freedium's hosting records and identify operators
- **Monitor for re-upload:** Freedium may restore content; document and re-file

---

## Jurisdiction Notes

- **DMCA (USA):** Applies if hosting provider or operator is US-based or serves US users
- **EU (DSA/Copyright Directive):** If provider is EU-based, Article 17 of the EU
  Copyright Directive may provide additional grounds for removal
- **International:** Contact a local IP attorney for non-US/EU hosting providers

---

## Important Caveats

Freedium's public defense is that they are providing a "reading tool" for content
users have already paid to access. This argument has weaknesses:

1. The user visiting Freedium has NOT paid — Freedium serves arbitrary users
2. Even if a subscriber uses Freedium, re-publishing the full text to the public
   is reproduction and distribution, not personal use
3. Freedium strips Medium's paywall mechanism, actively interfering with Medium's
   business model and harming author revenue

These are arguments your attorney can develop. This document is not legal advice.
