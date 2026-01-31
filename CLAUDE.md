# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains automated newsletter generators using Claude AI:

| Newsletter | Directory | Schedule | Signup Page |
|------------|-----------|----------|-------------|
| **What You Need to Know: AI** | `ai_newsletter/` | Monday 5 AM ET | `/docs/ai/` |
| **What You Need to Know: Economics** | `econ_newsletter/` | Tuesday 5 AM ET | `/docs/economics/` |

---

## Commands

### Economics Newsletter
```bash
cd econ_newsletter
pip install -r requirements.txt
python newsletter.py
```

### AI Newsletter
```bash
cd ai_newsletter
pip install -r requirements.txt
python newsletter.py
```

### Test individual modules
```bash
python sources.py   # Test data fetching
python emailer.py   # Test email sending
```

### Update archive index manually
```bash
python update_archive_index.py ai
python update_archive_index.py economics
```

---

## Environment Variables

### Shared
- `ANTHROPIC_API_KEY` - Claude API key
- `GOOGLE_SHEETS_CREDENTIALS` - Base64-encoded service account JSON
- `TEST_EMAIL` - Email address for test mode
- `TEST_MODE` - Set to "true" for test mode (sends only to TEST_EMAIL)

### Economics Newsletter
- `GMAIL_ADDRESS` - Gmail sender
- `GMAIL_APP_PASSWORD` - Gmail app password
- `ECON_SPREADSHEET_ID` - Google Sheet ID for subscribers
- `ECON_UNSUBSCRIBE_URL` - URL for unsubscribe page/form

### AI Newsletter
- `AI_GMAIL_ADDRESS` - Gmail sender
- `AI_GMAIL_APP_PASSWORD` - Gmail app password
- `AI_SPREADSHEET_ID` - Google Sheet ID for subscribers
- `AI_UNSUBSCRIBE_URL` - URL for unsubscribe page/form

---

## GitHub Pages (Signup & Archives)

The `docs/` folder is served via GitHub Pages:

```
docs/
  ai/
    index.html              # AI signup page
    archive/
      index.html            # Archive listing
      YYYY-MM-DD.html       # Past newsletters
  economics/
    index.html              # Economics signup page
    archive/
      index.html            # Archive listing
      YYYY-MM-DD.html       # Past newsletters
```

**Enable GitHub Pages**: Settings → Pages → Source: Deploy from branch → main → /docs

---

## Subscriber Management

Subscribers are stored in Google Sheets with this structure:

| Email | Name | Status | Date Added | Source |
|-------|------|--------|------------|--------|
| user@example.com | | active | 2024-01-15 | signup |

- **Status**: `active` or `unsubscribed`
- Only rows with `Status = active` receive emails

### Google Apps Script for Subscribe/Unsubscribe

Deploy a Google Apps Script as a web app to handle form submissions. The script should:
1. Accept POST requests with email and action (subscribe/unsubscribe)
2. Add new rows for subscriptions
3. Update Status to "unsubscribed" for unsubscribes

---

## Test Mode vs Production Mode

### Manual Workflow Trigger
When triggering workflows manually via GitHub Actions:
- **test** (default): Sends only to `TEST_EMAIL`, skips archiving
- **production**: Sends to all active subscribers, archives newsletter

### Scheduled Runs
Scheduled runs always run in production mode.

---

## Architecture

Both newsletters follow the same pipeline: **sources.py** → **summarizer.py** → **newsletter.py** → **emailer.py**

### Economics Newsletter (`econ_newsletter/`)
- **Sources**: NBER RSS, OpenAlex API (Top 5 econ + Top 3 finance journals), economics blogs
- **Categories**: Microeconomics, Macroeconomics, Econometrics, General Economics
- **Scoring**: Elite journals (10000+), top economists (5000+ citations), NBER working papers

### AI Newsletter (`ai_newsletter/`)
- **Sources**: arXiv (cs.AI, cs.LG, cs.CL, cs.CV), company blogs (Anthropic, OpenAI, DeepMind), AI newsletters (The Batch, Import AI), GitHub trending
- **Categories**: LLMs & Language Models, Computer Vision, RL & Agents, ML Infrastructure, General AI
- **Features**: Multi-recipient support, trending tools section

### Deployment
- `.github/workflows/newsletter.yml` - Economics newsletter (Tuesdays)
- `.github/workflows/ai_newsletter.yml` - AI newsletter (Mondays)

---

## Setup Checklist

### Google Cloud Setup
1. Create project at console.cloud.google.com
2. Enable Google Sheets API
3. Create service account → Download JSON key
4. Base64 encode: `base64 -i credentials.json`
5. Add as `GOOGLE_SHEETS_CREDENTIALS` secret

### Google Sheets Setup
6. Create spreadsheet for each newsletter
7. Add columns: Email, Name, Status, Date Added, Source
8. Share with service account email (Editor access)
9. Add sheet IDs as `ECON_SPREADSHEET_ID` and `AI_SPREADSHEET_ID` secrets

### GitHub Secrets Required
| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `GOOGLE_SHEETS_CREDENTIALS` | Base64-encoded service account JSON |
| `ECON_SPREADSHEET_ID` | Google Sheet ID for econ subscribers |
| `AI_SPREADSHEET_ID` | Google Sheet ID for AI subscribers |
| `TEST_EMAIL` | Your email for test sends |
| `GMAIL_ADDRESS` | Economics newsletter sender |
| `GMAIL_APP_PASSWORD` | Economics newsletter app password |
| `AI_GMAIL_ADDRESS` | AI newsletter sender |
| `AI_GMAIL_APP_PASSWORD` | AI newsletter app password |
| `ECON_UNSUBSCRIBE_URL` | Unsubscribe URL for economics |
| `AI_UNSUBSCRIBE_URL` | Unsubscribe URL for AI |

### GitHub Pages Setup
10. Go to repo Settings → Pages
11. Set source to "Deploy from branch" → main → /docs
12. Save and wait for deployment

### Workflow Permissions
13. Go to repo Settings → Actions → General
14. Under "Workflow permissions", select "Read and write permissions"
