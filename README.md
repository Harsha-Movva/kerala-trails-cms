# Kerala Trails

A responsive South India travel website and staff CMS built around a practical core: public package pages, seasonal package pricing, versioned package editing, private draft previews, traveller enquiries, AI-assisted extraction, and human review.

## Stack

- **Web:** Next.js App Router, React, Tailwind CSS
- **API:** FastAPI, Pydantic, SQLAlchemy
- **Database:** PostgreSQL (SQLite supported for local development)
- **Authentication:** signed JWT access tokens and scrypt password hashes
- **AI:** OpenAI structured JSON extraction with a conservative local fallback
- **Tests:** Pytest and FastAPI TestClient

## Implemented workflows

1. Travellers browse and search published packages.
2. Package pages show day-wise itineraries, inclusions, hotel category and seasonal prices.
3. Staff sign in to the protected CMS.
4. Staff create and edit packages, save drafts, publish, preview privately, inspect version snapshots and restore an earlier version.
5. Travellers submit enquiries without creating an account.
6. The API acknowledges enquiries and processes extraction and package suggestions.
7. Staff inspect original messages, extracted JSON, confidence signals, suggested packages and draft replies; corrections are saved with an activity record.
8. Package changes, restores and enquiry reviews/status updates are recorded in the activity log.

## Local setup

Follow [deployment.md](deployment.md) for prerequisites, environment variables, demo credentials, local run commands, tests and hosting setup.

## Repository layout

- `backend/app`: FastAPI routes, SQLAlchemy models, schemas, security, seed data and enquiry extraction.
- `backend/tests`: API and core logic tests.
- `frontend/app`: public pages, package detail pages, enquiry form, staff CMS and SEO routes.
- `frontend/lib`: API client and shared types.
- `render.yaml`: backend and PostgreSQL deployment blueprint.
- `backend/Dockerfile`: API container image.

## Test

```bash
cd backend
python -m pytest -q
```

The backend test suite covers seed data, fallback extraction, published-only search, anonymous access restrictions, private draft preview, version history and restore, activity logging, enquiry validation, package suggestions and staff correction.

## Demo data

The repository seeds fictional package and staff data for evaluation. The demo login is documented in [deployment.md](deployment.md). Change or disable the demo credentials before production use.

## Scope and limitations

The current core slice does not include a full blog CMS, quote PDF generation, external email/WhatsApp delivery, multi-role consultant/editor workflows, image uploads, or the 140 legacy URL redirects. The legacy URL map and redirect destinations were not supplied, so redirects have not been fabricated.

Without `OPENAI_API_KEY`, the local parser is a deterministic fallback, not a generative model. It flags extracted fields for human review. With an API key, provider-backed extraction is enabled. AI output does not set or invent package prices; displayed prices come from package records.

No live application URL is claimed until hosting is configured and smoke-tested.