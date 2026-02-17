# Hosting Provider & Infrastructure Contacts

This document lists known infrastructure providers commonly used by paywall-bypass
proxy services, along with their abuse reporting contacts.

**Note:** Infrastructure changes frequently. Always verify with a fresh `dig` / WHOIS
lookup before filing. Use `legal/collect_evidence.py` to confirm current hosting.

---

## How to Identify Current Hosting

```bash
# 1. Find the IP address
dig freedium.cfd

# 2. Look up the hosting provider for that IP
curl https://ipinfo.io/<IP-ADDRESS>/json

# 3. Find WHOIS / abuse contact
whois <IP-ADDRESS>

# 4. Find the domain registrar
whois freedium.cfd
```

---

## Common Hosting Providers (Abuse Contacts)

### Hetzner Online GmbH (Germany)
- **Abuse email:** abuse@hetzner.com
- **Abuse form:** https://www.hetzner.com/legal/abuse
- **Notes:** Generally responsive to DMCA/copyright complaints. EU-based, also subject to DSA.

### OVHcloud (France / Canada / USA)
- **Abuse form:** https://www.ovhcloud.com/en/public-cloud/aup/
- **Abuse email:** abuse@ovh.net
- **Notes:** Response time varies. May need follow-up.

### DigitalOcean (USA)
- **Abuse form:** https://www.digitalocean.com/company/contact/#abuse
- **Abuse email:** abuse@digitalocean.com
- **Notes:** US-based, subject to DMCA. Generally responsive.

### Vultr (USA)
- **Abuse email:** abuse@vultr.com
- **Notes:** US-based, subject to DMCA.

### Cloudflare (USA) — CDN/Proxy Layer
- **DMCA form:** https://www.cloudflare.com/abuse/
- **Notes:** Cloudflare is a proxy — they may claim they do not host content.
  Cloudflare's DMCA policy allows them to terminate service for repeat infringers.
  If content passes through Cloudflare, also contact the origin hosting provider.

### Fastly (USA) — CDN
- **Abuse form:** https://www.fastly.com/abuse
- **Abuse email:** abuse@fastly.com

---

## Domain Registrars (Abuse Contacts)

### Namecheap
- **Abuse form:** https://www.namecheap.com/support/knowledgebase/article.aspx/9715/

### GoDaddy
- **Abuse form:** https://supportcenter.godaddy.com/AbuseReport

### Porkbun
- **Abuse email:** abuse@porkbun.com

### Cloudflare Registrar
- **Abuse:** Submit through Cloudflare's general abuse form

---

## Search Engine De-indexing (Reduce Traffic to Infringing Copies)

Even if hosting providers don't act immediately, removing infringing URLs from
search indexes significantly reduces traffic.

### Google
- **DMCA form:** https://reportcontent.google.com/forms/dmca
- **Effect:** Removes specific URLs from Google Search results
- **Timeline:** Usually processed within 1–7 days

### Bing / Microsoft
- **DMCA form:** https://www.microsoft.com/en-us/concern/dmca
- **Timeline:** Usually processed within 5–10 business days

### DuckDuckGo
- Uses Bing's index; removing from Bing usually affects DDG as well

---

## Escalation Path

If a hosting provider does not respond within 14 business days:

1. **Contact the upstream network provider (transit ASN)**
   - Find the upstream ASN: use `traceroute <IP>` or BGP looking glass tools
   - Large transit providers (e.g., Hurricane Electric, Cogent, Lumen) take abuse seriously

2. **File a complaint with ICANN**
   - For domain policy violations: https://www.icann.org/resources/pages/ucdrp-2012-02-25-en

3. **Contact payment processors**
   - If the infringing site runs ads or accepts donations, contact their payment processor
   - Visa, Mastercard, PayPal, and Stripe all have content policy teams

4. **Consult an attorney**
   - Consider a DMCA subpoena to identify the site operator
   - Consider sending a cease-and-desist letter via counsel
