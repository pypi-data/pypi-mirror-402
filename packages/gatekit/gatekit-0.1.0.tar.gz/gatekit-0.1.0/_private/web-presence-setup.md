# Gatekit Web Presence Setup Guide

## Overview
- **Domain**: gatekit.ai (at Namecheap)
- **Email**: Google Workspace (Gmail with @gatekit.ai)
- **Website**: GitHub Pages with custom domain
- **DNS**: Namecheap (keep it simple)

---

## Step 1: Set Up Google Workspace (~15 min)

1. Go to https://workspace.google.com/
2. Click "Get Started" → Choose "Business Starter" ($7.20/mo)
3. Enter business name: "Gatekit"
4. Enter your info, create admin account: dbright@gatekit.ai
5. When prompted for domain, enter: gatekit.ai
6. Choose "I have a domain" (not buying a new one)

**Verify domain ownership** (Google will guide you):
- Google gives you a TXT record to add
- Go to Namecheap → Domain List → gatekit.ai → Manage → Advanced DNS
- Add TXT record with the verification string Google provides
- Wait a few minutes, click Verify in Google

**Set up MX records** (for email delivery):
- In Namecheap Advanced DNS, add these MX records:

| Type | Host | Value | Priority |
|------|------|-------|----------|
| MX | @ | aspmx.l.google.com | 1 |
| MX | @ | alt1.aspmx.l.google.com | 5 |
| MX | @ | alt2.aspmx.l.google.com | 5 |
| MX | @ | alt3.aspmx.l.google.com | 10 |
| MX | @ | alt4.aspmx.l.google.com | 10 |

**Create email alias**:
- In Google Admin Console → Users → dbright@gatekit.ai → User Information
- Add alias: hello@gatekit.ai
- Now both addresses deliver to same inbox

---

## Step 2: Set Up GitHub Pages with Custom Domain (~10 min)

**In your GitHub repo** (gatekit-public):

1. Go to Settings → Pages
2. Source: Deploy from branch → main → / (root) or /docs
3. Custom domain: enter `gatekit.ai`
4. Check "Enforce HTTPS" (after DNS propagates)

**In Namecheap DNS**, add these records:

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | your-username.github.io |

**In your repo**, create file `CNAME` in root:
```
gatekit.ai
```

Wait 10-30 min for DNS propagation. GitHub will auto-provision HTTPS.

---

## Step 3: Create Simple Landing Page (optional for v0.1.0)

For now, you can either:

**Option A**: Redirect to GitHub repo
- In Namecheap, use URL Redirect Record to point to your GitHub repo

**Option B**: Simple index.html in repo root
```html
<!DOCTYPE html>
<html>
<head>
  <title>Gatekit</title>
  <meta http-equiv="refresh" content="0; url=https://github.com/YOUR-ORG/gatekit">
</head>
<body>
  <p>Redirecting to <a href="https://github.com/YOUR-ORG/gatekit">GitHub</a>...</p>
</body>
</html>
```

**Option C**: Build a proper landing page later with MkDocs

---

## Step 4: Email Security Records (recommended)

Add these TXT records in Namecheap for better email deliverability:

**SPF Record**:
| Type | Host | Value |
|------|------|-------|
| TXT | @ | v=spf1 include:_spf.google.com ~all |

**DMARC Record**:
| Type | Host | Value |
|------|------|-------|
| TXT | _dmarc | v=DMARC1; p=none; rua=mailto:dbright@gatekit.ai |

**DKIM**: Set up in Google Admin Console → Apps → Google Workspace → Gmail → Authenticate email. Google generates a TXT record for you to add.

---

## Final DNS Records Summary

After setup, your Namecheap DNS should have:

| Type | Host | Value | Purpose |
|------|------|-------|---------|
| A | @ | 185.199.108.153 | GitHub Pages |
| A | @ | 185.199.109.153 | GitHub Pages |
| A | @ | 185.199.110.153 | GitHub Pages |
| A | @ | 185.199.111.153 | GitHub Pages |
| CNAME | www | your-username.github.io | GitHub Pages |
| MX | @ | aspmx.l.google.com (pri 1) | Gmail |
| MX | @ | alt1.aspmx.l.google.com (pri 5) | Gmail |
| MX | @ | alt2.aspmx.l.google.com (pri 5) | Gmail |
| MX | @ | alt3.aspmx.l.google.com (pri 10) | Gmail |
| MX | @ | alt4.aspmx.l.google.com (pri 10) | Gmail |
| TXT | @ | v=spf1 include:_spf.google.com ~all | Email auth |
| TXT | @ | google-site-verification=... | Domain verify |
| TXT | _dmarc | v=DMARC1; p=none; ... | Email auth |
| TXT | google._domainkey | (from Google Admin) | DKIM |

---

## Cost Summary

| Service | Cost |
|---------|------|
| Domain (Namecheap, prepaid) | $0 for now |
| Google Workspace | $7.20/mo (~$86/yr) |
| GitHub Pages | Free |
| **Total ongoing** | ~$7.20/mo |

---

## Verification Checklist

- [ ] Can send email as dbright@gatekit.ai
- [ ] Can receive email at dbright@gatekit.ai
- [ ] Can receive email at hello@gatekit.ai
- [ ] gatekit.ai loads (GitHub Pages or redirect)
- [ ] https://gatekit.ai works (HTTPS enabled)
- [ ] www.gatekit.ai redirects properly
