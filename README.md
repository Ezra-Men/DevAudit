# DevAudit
Instant developer credibility powered by Gemini AI.


# DevAudit — Proof-of-Work & Skill Intelligence for Engineers

[DevAudit CI Pipeline](https://github.com/Ezra-Men/DevAudit/actions/workflows/ci.yml/badge.svg)(https://github.com/Ezra-Men/DevAudit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-Apache-2.0-yellow.svg)](LICENSE)
[Framework](https://img.shields.io/badge/Django-5.x-darkgreen.svg) (https://www.djangoproject.com/)

DevAudit audits public engineering activity to generate verifiable skill intelligence passports and dynamic status badges for engineers and recruiters using Google Gemini.

---

## Features
1. Sanitized Ingestion: Automatically filters out forked and cloned repositories to inspect original work.
2. AI Skill Intelligence: Assesses architecture depth, commit cadence, and code patterns via Gemini structured outputs.
3. Dynamic Profile Badges: Renders real-time SVG badges embeddable into any GitHub README.
4. 1-Click Passport Export: Client-side PNG generation for sharing on LinkedIn and Twitter/X.
5. 24-Hour Smart Cache: Caches candidate profiles in SQLite to prevent duplicate API hits and rate limits.
6. Automated CI/CD: Continuous Integration that runs 11 unit test cases from test.py via GitHub Actions running on every commit and pull request.

---

## Tech Stack
1. Backend: Python 3.11+, Django 5.x, Gunicorn, WhiteNoise
2. AI & Data: Google Gemini API (`gemini-3.5-flash`), Pydantic v2, `httpx`
3. Frontend: Django Templates, Tailwind CSS, `html2canvas`
4. CI/CD & Hosting: GitHub Actions (`ubuntu-latest`), Render