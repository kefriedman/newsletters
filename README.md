# What You Need to Know - Newsletter System

Automated newsletter system for **What You Need to Know: AI** (Mondays) and **What You Need to Know: Economics** (Tuesdays).

## Overview

This system:
- Fetches content from various sources (arXiv, NBER, blogs, GitHub trending)
- Uses Claude AI to summarize and curate the most interesting content
- Sends HTML newsletters via Gmail
- Manages subscribers via Google Sheets
- Hosts signup pages and archives on GitHub Pages

## Project Structure

```
newsletters/
├── ai_newsletter/           # AI newsletter code
│   ├── newsletter.py        # Main script
│   ├── sources.py           # Content fetching
│   ├── summarizer.py        # AI summarization
│   ├── emailer.py           # Email sending
│   ├── templates/
│   │   └── newsletter.html  # Email template
│   └── requirements.txt
│
├── econ_newsletter/         # Economics newsletter code
│   ├── newsletter.py
│   ├── sources.py
│   ├── summarizer.py
│   ├── emailer.py
│   ├── templates/
│   │   └── newsletter.html
│   └── requirements.txt
│
├── docs/                    # GitHub Pages (signup & archive)
│   ├── ai/
│   │   ├── index.html       # AI signup page
│   │   └── archive/
│   │       └── index.html   # Archive listing
│   └── economics/
│       ├── index.html       # Economics signup page
│       └── archive/
│           └── index.html
│
├── .github/workflows/
│   ├── ai_newsletter.yml    # AI newsletter workflow (Mondays 5 AM ET)
│   └── newsletter.yml       # Economics workflow (Tuesdays 5 AM ET)
│
└── update_archive_index.py  # Script to update archive listings
```

## Live URLs

- **AI Signup**: https://kefriedman.github.io/newsletters/ai/
- **AI Archive**: https://kefriedman.github.io/newsletters/ai/archive/
- **Economics Signup**: https://kefriedman.github.io/newsletters/economics/
- **Economics Archive**: https://kefriedman.github.io/newsletters/economics/archive/

## How It Works

### 1. Content Fetching

**AI Newsletter** pulls from:
- arXiv (cs.AI, cs.LG, cs.CL categories)
- Company blogs (Anthropic, Google DeepMind)
- Newsletters (Import AI, Ahead of AI)
- GitHub trending repos

**Economics Newsletter** pulls from:
- NBER working papers
- Top journals (AER, QJE, Econometrica, JPE, REStud)
- Finance journals (JF, RFS, JFE)
- Economics blogs (Marginal Revolution, EconLog)

### 2. AI Summarization

Content is sent to Claude API which:
- Selects the most interesting/impactful items
- Writes concise summaries
- Organizes content by category

### 3. Email Sending

- Reads active subscribers from Google Sheets
- Renders HTML template with personalized unsubscribe links
- Sends via Gmail SMTP with App Password

### 4. Subscriber Management

- **Signup**: Web form → Google Apps Script → Google Sheets
- **Welcome Email**: Sent automatically on signup
- **Unsubscribe**: Link in emails → Apps Script → Updates sheet status

## GitHub Actions Workflows

### Scheduled Runs
- **AI Newsletter**: Every Monday at 5:00 AM ET
- **Economics Newsletter**: Every Tuesday at 5:00 AM ET

### Manual Runs
Both workflows support manual triggering with mode selection:
- `test`: Sends only to TEST_EMAIL, skips archive
- `production`: Sends to all subscribers, saves to archive

### Workflow Steps
1. Checkout code
2. Setup Python
3. Install dependencies
4. Run newsletter script
5. Copy output to archive (production only)
6. Update archive index
7. Commit and push archive changes

## Setup Guide

### Prerequisites
- Python 3.11+
- Google Cloud project with Sheets API enabled
- Gmail account with App Password
- Anthropic API key
- GitHub repository with Pages enabled

### 1. Google Cloud Setup

1. Create project at https://console.cloud.google.com
2. Enable Google Sheets API
3. Create service account (IAM & Admin → Service Accounts)
4. Download JSON key
5. Base64 encode: `base64 -i credentials.json | tr -d '\n'`

### 2. Google Sheets Setup

Create two spreadsheets with columns:
| Email | Status | Date Added | Source |
|-------|--------|------------|--------|

Share each spreadsheet with the service account email (Editor access).

### 3. Google Apps Script Setup

1. Create new Apps Script project at https://script.google.com
2. Add the subscribe/unsubscribe handling code
3. Set up `appsscript.json` with required OAuth scopes:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/script.send_mail`
4. Deploy as Web App (Execute as: Me, Access: Anyone)

### 4. GitHub Repository Setup

**Enable GitHub Pages:**
1. Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /docs

**Enable Workflow Permissions:**
1. Settings → Actions → General
2. Workflow permissions: Read and write permissions

### 5. GitHub Secrets

Add these secrets in Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `GOOGLE_SHEETS_CREDENTIALS` | Base64-encoded service account JSON |
| `AI_GMAIL_ADDRESS` | Gmail for AI newsletter |
| `AI_GMAIL_APP_PASSWORD` | Gmail App Password |
| `AI_SPREADSHEET_ID` | Google Sheet ID for AI subscribers |
| `GMAIL_ADDRESS` | Gmail for Economics newsletter |
| `GMAIL_APP_PASSWORD` | Gmail App Password |
| `ECON_SPREADSHEET_ID` | Google Sheet ID for Econ subscribers |
| `APPS_SCRIPT_URL` | Deployed Apps Script URL |
| `TEST_EMAIL` | Email for test mode |

### 6. Gmail App Password

1. Enable 2-Factor Authentication on Gmail
2. Go to Google Account → Security → App passwords
3. Generate password for "Mail"

## Local Development

```bash
# Clone repository
git clone https://github.com/kefriedman/newsletters.git
cd newsletters

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Install dependencies
cd ai_newsletter
pip install -r requirements.txt

# Run in test mode
TEST_MODE=true python newsletter.py
```

## Troubleshooting

### "No recipients found"
- Check that the service account has access to the spreadsheet
- Verify there are subscribers with Status = "active"
- Check that column headers match exactly: "Email", "Status"

### "Permission denied" on git push
- Enable write permissions in Settings → Actions → General

### Unsubscribe not working
- Verify Apps Script has correct OAuth scopes
- Create new deployment after code changes
- Update APPS_SCRIPT_URL secret with new deployment URL

### Welcome email not sending
- Check Apps Script execution logs
- Verify MailApp permissions in appsscript.json
- Re-authorize the script

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐
│  GitHub Pages   │────▶│  Google Apps     │
│  (Signup Form)  │     │  Script          │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌──────────────────┐
│  GitHub Actions │     │  Google Sheets   │
│  (Scheduled)    │◀───▶│  (Subscribers)   │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Content        │────▶│  Claude AI       │
│  Sources        │     │  (Summarize)     │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Gmail SMTP      │
                        │  (Send Emails)   │
                        └──────────────────┘
```

## License

Private project - not for redistribution.
