# Kerala Trails — local setup and deployment

## Current live demo

- **Website:** https://kerala-trails-live.vercel.app
- **Staff CMS:** https://kerala-trails-live.vercel.app/admin
- **API:** https://kerala-trails-api-app.onrender.com
- **API health route:** https://kerala-trails-api-app.onrender.com/api/health
- **GitHub:** https://github.com/Harsha-Movva/kerala-trails-cms

Vercel and Render both report successful production deployments. The API is currently running with a temporary SQLite database file on the Render service filesystem. That file is not durable across instance replacement and is not suitable for real customer data. A Render PostgreSQL instance has been provisioned separately but is not yet attached to the running web service. Complete the database connection steps under “Before production use” below.

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- Docker Desktop (for local PostgreSQL)
- A GitHub account with access to `https://github.com/Harsha-Movva/kerala-trails-cms`

## 1. Get the source

```bash
git clone https://github.com/Harsha-Movva/kerala-trails-cms.git
cd kerala-trails-cms
```

## 2. Start PostgreSQL locally

```bash
docker compose up -d db
```

The Compose credentials are for local development only. Do not reuse them in a hosted environment.

## 3. Configure and run the API

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
Copy-Item .env.example .env
```

macOS/Linux:

```bash
source .venv/bin/activate
cp .env.example .env
```

Edit `backend/.env` and replace `JWT_SECRET` with a long random value. For local PostgreSQL, keep the `DATABASE_URL` from `.env.example` and start the Compose database. `OPENAI_API_KEY` is optional for local use. With no key, the conservative local parser extracts a subset of the sample enquiry, marks all fields for human review and still exercises the review flow. Add an API key to enable provider-backed structured extraction.

Install and start:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API health: `http://localhost:8000/api/health`
API documentation: `http://localhost:8000/docs`

## 4. Configure and run the frontend

Open a second terminal:

```bash
cd frontend
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env.local
```

macOS/Linux:

```bash
cp .env.example .env.local
```

Install and run:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## 5. Reviewer demo login

- **URL:** https://kerala-trails-live.vercel.app/admin
- **Email:** `admin@keralatrails.demo`
- **Password:** `TrailDemo!2026`

This is a seeded demonstration account with fictional data. Change or disable it before any production use. Do not add real traveller records to the demo environment.

## 6. Run tests

```bash
cd backend
python -m pytest -q
```

The backend test suite covers seed data, fallback extraction, public search, anonymous access control, draft preview protection, version restore/history, activity logging, enquiry validation and the sample enquiry-to-suggestion flow.

## Environment variable names (names only)

Backend (`backend/.env`):

- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_EXPIRES_MINUTES`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `CORS_ORIGINS`
- `APP_ENV`

Frontend (`frontend/.env.local`):

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SITE_URL`

Never commit `.env`, `.env.local`, API keys, production credentials or database dumps. `APP_ENV=production` makes the API refuse to start with the known development JWT secret.

## Hosted deployment configuration

The repository includes `render.yaml` for a Render API plus PostgreSQL Blueprint and `backend/Dockerfile` for container deployment. The live frontend is hosted on Vercel with the project root set to `frontend`. The live API is hosted on Render in Singapore.

Vercel project environment variables:

- `NEXT_PUBLIC_API_URL=https://kerala-trails-api-app.onrender.com`
- `NEXT_PUBLIC_SITE_URL=https://kerala-trails-live.vercel.app`

Render API CORS is configured for the Vercel production origin. If the Vercel domain changes, update `CORS_ORIGINS` on Render and redeploy the API.

## Before production use: attach PostgreSQL

The current live API is running on SQLite (`sqlite:///./kerala_trails.db`) as a temporary demonstration configuration. SQLite on the Render service filesystem is not durable across instance replacement and must not be used for real traveller enquiries.

A Render PostgreSQL instance named `kerala-trails-db` has been provisioned. In the Render dashboard:

1. Open the `kerala-trails-db` database and copy its **Internal Database URL**.
2. Open the `kerala-trails-api-app` web service and set `DATABASE_URL` to the internal connection string, using the `postgresql+psycopg://` scheme.
3. Keep `APP_ENV=production` and the existing strong `JWT_SECRET`. Do not expose database credentials in GitHub or in a public document.
4. Redeploy the API and verify `/api/health`, the seeded package list, staff login, package editing and enquiry persistence.
5. Configure automated database backups and an appropriate paid plan before accepting real customer information.

The Render Postgres instance currently has an empty IP allowlist; the API service uses Render's internal network. Do not open the database to all public IP addresses merely to make an external query tool work.

## Deployment verification

1. Open the website and confirm the published package cards appear.
2. Open a package detail page and check itinerary and seasonal prices.
3. Sign in at `/admin` using the demo credentials.
4. Create a draft package and confirm it appears in the private preview but not the public package listing.
5. Submit a test enquiry and inspect its extracted fields and package suggestions in the CMS.
6. Confirm that the CORS origin matches the exact production website domain.

The Vercel production build and Render API deployment both have successful deployment records. Complete the end-to-end smoke test above and attach PostgreSQL before calling this production-ready.

## Operational notes and limitations

- SQLAlchemy currently creates tables on API startup. Add Alembic migrations before production schema evolution.
- The Render database plan provisioned for the demo is a starter/free configuration; select a paid plan and a region appropriate to the client's data-residency needs before real customer use.
- Image URLs are stored as package content; there is no managed upload pipeline in this core slice.
- Email and WhatsApp delivery are mocked. The API returns the fixed acknowledgement and stores the optional WhatsApp consent flag; it does not send messages.
- The 140 old URLs and their destinations were not supplied, so redirects are not invented. Add a verified redirect map before launch.
