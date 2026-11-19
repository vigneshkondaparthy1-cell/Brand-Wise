# The Final Draft — BrandWise

BrandWise is a local content review demo. It checks marketing copy against the claim ledger and guidelines, explains findings with sources, and leaves approval to a person.

## Run locally

1. Use Python 3.10 or newer.
2. Copy `.env.example` to `.env`. To send registration and password-reset codes without Gmail 2-Step Verification, create a Resend API key and set `RESEND_API_KEY` and `RESEND_FROM`. The sender must be permitted by your Resend account; verify a domain for production delivery. Do not paste the API key into chat or commit it. Alternatively configure SMTP; Gmail SMTP requires a Google App Password and enabled 2-Step Verification. Add a `GEMINI_API_KEY` only if you want optional Gemini review. Rule checks work without an AI key. Set `DATABASE_URL` to use Neon PostgreSQL; optionally set `DATABASE_URL_UNPOOLED` for schema migrations.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Run `python server.py` and open `http://127.0.0.1:8765`.

The standard-library HTTP server in `server.py` serves `The-Final-Draft-Hackathon-Updated.html` (also mirrored as `index.html`). With `DATABASE_URL`, account/profile/session/verification records and audits, claims, guidelines, and workspace audit preferences are stored in Neon PostgreSQL. Without it, the local demo continues to use SQLite and JSON files. The first Neon startup applies the checked-in SQL migration and imports local JSON data and account password hashes only when the corresponding Neon tables/documents are empty; sessions and pending OTPs are not copied.

For Render, add `DATABASE_URL` using Neon's pooled connection string. Also add `DATABASE_URL_UNPOOLED` from Neon for the schema migration connection. Keep both values in Render's environment settings and out of source control. The application uses the pooled URL for normal traffic and the direct URL only while applying schema migrations.

## Firebase Authentication

The Firebase CLI project target is `brand-wise-7318f`, with Email/Password authentication declared in `firebase.json`. This config is not deployed automatically. After installing or running the Firebase CLI and signing in with an account that can access the project, apply it with `npx -y firebase-tools@latest deploy --only auth`. The current BrandWise sign-in page and account/session backend still use the existing account system; deploying this provider configuration alone does not migrate users or switch app sign-in to Firebase.

## Local demo sign-ins

These credentials are for this local demo only. Do not reuse them on a public deployment.

| Role | Username | Password |
| --- | --- | --- |
| Admin | `ADMIN` | `221411` |
| Creator | `test_creator` | `TestUser2026!` |
| External Agency | `test_agency` | `TestUser2026!` |
| Reviewer | `test_reviewer` | `TestUser2026!` |
| Brand Manager | `test_brandmanager` | `TestUser2026!` |

Admin accounts are provisioned locally and cannot be created through registration.
New accounts must verify their email with a 6-digit code before registration. Codes expire after 10 minutes; Resend or SMTP settings are required for delivery. New passwords must be at least 4 characters.

## AI and privacy

Deterministic rules run in the app server. When a user enables Gemini review, the draft and approved claims and guidelines used for context are sent to Google Gemini. Account and audit data are stored in Neon when `DATABASE_URL` is configured; otherwise the local SQLite/JSON fallback is used. The OpenAI adapter exists in the codebase but is not currently called by the audit workflow; drafts are not sent to OpenAI. No OCR or pgvector service is part of this running demo.

## Limits and security

The checks are a prototype, not legal advice or a substitute for human review. Scores are deterministic policy-risk scores, not model accuracy. Reading grade is a heuristic estimate (the exact required disclaimer is excluded); heading-order checks only inspect Markdown or HTML headings. Contrast is a manual calculator, not an artwork scan. The 40-case evaluation set is synthetic and only measures current deterministic rules; it does not prove production detection accuracy or source correctness. Login lockout is in-memory and resets when the server restarts. Session cookies are HttpOnly and SameSite=Strict; Secure is enabled when the app is behind HTTPS and the proxy sets `X-Forwarded-Proto`. Origin checks protect state-changing requests. Review GDPR wording with counsel before relying on it.

External Agency accounts can access only audits associated with their registered organization. Review transitions are restricted to Reviewer, Brand Manager, and Admin roles; approval and publish transitions also enforce score, state, and finding-disposition requirements server-side. The supported document imports are TXT, Markdown, CSV, PDF, and DOCX. OCR, image/logo analysis, Google Docs/Slides, Canva/Figma, regional-language support, and SSO are not implemented.

`accounts.sqlite3`, `.env`, audit data, and generated Python files are excluded by `.gitignore`. Keep real credentials in `.env`, never commit them, and rotate a provider key through that provider's console if it has been exposed.
