# Kerala Trails — local setup and deployment

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

If the repository has not been pushed yet, unzip the project source archive and use the included Git history, then push it after authenticating with GitHub.

## 2. Start PostgreSQL

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

Edit `backend/.env` and replace `JWT_SECRET` with a long random value. `OPENAI_API_KEY` is optional for local use. With no key, the conservative local parser extracts a subset of the sample enquiry, marks all fields for human review and still exercises the review flow. Add an API key to enable provider-backed structured extraction.

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

- **URL:** `http://localhost:3000/admin`
- **Email:** `admin@keralatrails.demo`
- **Password:** `TrailDemo!2026`

This is a seeded demonstration account with fictional data. Change or disable it before any production use. Do not add real traveller records to the demo environment.

## 6. Run tests

```bash
cd backend
python -m pytest -q
```

The current backend test suite covers seed data, fallback extraction, public search, anonymous access control, draft preview protection, version restore/history, activity logging, enquiry validation and the sample enquiry-to-suggestion flow.

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

## Hosted deployment

The backend and PostgreSQL blueprint is in `render.yaml` and the API Dockerfile is `backend/Dockerfile`.

1. Push the public GitHub repository.
2. In Render, create a new Blueprint deployment from the repository and review the `kerala-trails-api` service and `kerala-trails-db` database before applying it.
3. Set `CORS_ORIGINS` to the exact Vercel frontend origin. Add `OPENAI_API_KEY` only if provider-backed extraction is required.
4. Deploy the frontend on Vercel with the project root set to `frontend`.
5. Set `NEXT_PUBLIC_API_URL` to the deployed API origin and `NEXT_PUBLIC_SITE_URL` to the deployed frontend origin in Vercel. Set the API's `CORS_ORIGINS` to that same frontend origin in Render, then redeploy the API.
6. Verify `/api/health`, sign in with the demo account, create and publish a test package, confirm its public route, submit the sample enquiry, review its extraction and verify that a draft is not publicly accessible.
7. Replace the demo password, use a managed database with backups, and keep all production secrets in the hosting providers' environment-variable settings.

**Deployment status:** no hosted environment or live URL has been configured or smoke-tested in this workspace. The files above provide the deployment configuration and repeatable steps; do not represent the application as live until those steps have been completed.

## Operational notes and limitations

- SQLAlchemy currently creates tables on API startup. Add Alembic migrations before production schema evolution.
- The included Render database plan is a starter configuration; select a paid plan and a region appropriate to the client's data-residency needs before real customer use.
- Image URLs are stored as package content; there is no managed upload pipeline in this core slice.
- Email and WhatsApp delivery are mocked. The API returns the fixed acknowledgement and stores the optional WhatsApp consent flag; it does not send messages.
- The 140 old URLs and their destinations were not supplied, so redirects are not invented. Add a verified redirect map before launch.
