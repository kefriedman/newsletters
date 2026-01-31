# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains automated newsletter generators using Claude AI:

| Newsletter | Directory | Schedule | Recipients |
|------------|-----------|----------|------------|
| **Economics Newsletter** | `econ_newsletter/` | Tuesday 8 AM ET | Single |
| **AI Newsletter** | `ai_newsletter/` | Monday 8 AM ET | Multiple |

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

---

## Environment Variables

### Economics Newsletter (`.env`)
- `ANTHROPIC_API_KEY` - Claude API key
- `GMAIL_ADDRESS` - Gmail sender
- `GMAIL_APP_PASSWORD` - Gmail app password
- `RECIPIENT_EMAIL` - Single recipient

### AI Newsletter (`.env`)
- `ANTHROPIC_API_KEY` - Claude API key
- `AI_GMAIL_ADDRESS` - Gmail sender
- `AI_GMAIL_APP_PASSWORD` - Gmail app password
- `AI_RECIPIENT_EMAILS` - Comma-separated recipient list

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
