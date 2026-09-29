# AI Restaurant Support & Operations Agent

DineAssist is an operations workspace for restaurant support teams. It pairs a React dashboard with a FastAPI service for order lookup, ticket handling, customer support chat, complaint workflows, and knowledge retrieval.

## Implemented features

- Authenticated administrator sign-in using bearer tokens.
- Dashboard counts, recent support activity, and a seven-day ticket-volume chart.
- Searchable order and ticket lists, with order details and ticket timelines.
- Ticket creation, status changes, and API-backed confirmation of returned ticket references.
- Support chat that can look up order data, retrieve indexed policy information, and return tool/source metadata from the backend.
- Complaint classification and workflow execution endpoints.
- Knowledge document management, search, and index rebuild endpoints.
- Health and readiness endpoints.

The backend seeds sample records when starting an empty database. Dashboard data can therefore contain sample records; the app labels this explicitly. This is not an isolated demo mode, and the seeded records use the configured database.

## Technology

- Frontend: React 19, Vite 8, Axios, Recharts, and Lucide React.
- Backend: Python, FastAPI, Pydantic Settings, SQLAlchemy, and SQLite by default.
- AI: deterministic mock/fallback behavior by default; OpenAI and Google providers are available when configured.
- Retrieval: FAISS and sentence-transformers, using knowledge documents stored by the backend.

The current frontend uses local component state for its four workspace views. React Router is present as a dependency but is not currently used for page routing.

## Repository layout

```text
.github/workflows/deploy.yml   GitHub Pages frontend deployment
backend/app/api/               FastAPI route handlers
backend/app/agents/            Chat agent
backend/app/core/              Settings and security
backend/app/db/                Database setup and seeding
backend/app/models/            SQLAlchemy models
backend/app/rag/               Knowledge retrieval pipeline
backend/app/repositories/      Database query helpers
backend/app/schemas/            API request and response schemas
backend/app/tools/              Agent tools
backend/app/workflows/         Complaint workflow
backend/tests/                 Backend API tests
frontend/src/                  React application and styles
```

## Prerequisites

- Python 3.10 or newer.
- Node.js 22 or newer and npm.
- A supported Python environment for the packages in `backend/requirements.txt`.

## Local setup

Use two terminals from the repository root.

### Backend terminal

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` before starting. Replace the secret and administrator placeholders; configure an AI provider/key only if using OpenAI or Google. The backend reads `.env` relative to the current working directory. Start the service from `backend/`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The API documentation is available at `http://127.0.0.1:8001/api/docs` while the backend is running. Seeded administrator credentials are controlled by `ADMIN_EMAIL` and `ADMIN_PASSWORD`; seeding creates the initial administrator only when the database does not already contain one. Use unique local values and do not publish them.

### Frontend terminal

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The frontend reads `VITE_API_BASE_URL` from the Vite environment. During development only, it falls back to `http://127.0.0.1:8001` when that variable is unset. `.env.local` is ignored by Git.

## Configuration

`backend/.env.example` lists backend settings. Important settings include:

- `DATABASE_URL`: SQLite is the default; select a durable database for hosted use.
- `SECRET_KEY`: replace with a unique, randomly generated secret before hosting.
- `ADMIN_EMAIL` and `ADMIN_PASSWORD`: initial administrator values for an empty database.
- `AI_PROVIDER`: `mock`, `openai`, or `google`; provider keys are required for the hosted LLM providers.
- `ALLOWED_ORIGINS`: JSON array of exact frontend origins. For the GitHub Pages project site, allow the origin `https://prasnna12.github.io` (the project path is not part of the origin).

`frontend/.env.example` shows the local API URL. Vite embeds `VITE_API_BASE_URL` in the built frontend, so it is a public URL, not a secret. For GitHub Actions, set the repository variable `VITE_API_BASE_URL` to the deployed backend's HTTPS base URL. If it is unset in a production build, API calls are stopped with a configuration message instead of silently targeting localhost.

The default `mock` AI provider uses deterministic fallback logic. It does not call a hosted language model. Knowledge search only has document references when a RAG index is available; building an index uses the configured embedding model and can require model download and storage. OpenAI/Google provider usage requires the corresponding API key and may incur provider costs.

## Quality checks

Run from the repository root:

```powershell
Push-Location frontend; npm run lint; npm run build; Pop-Location
Push-Location backend; pytest; Pop-Location
```

## GitHub Pages deployment

The workflow in `.github/workflows/deploy.yml` deploys only the Vite static frontend. It builds the site with the project base path `/AI_Restaurant_Support_Agent/`, installs from `frontend/package-lock.json`, and publishes `frontend/dist` on pushes to `main` or a manual workflow dispatch.

In GitHub, select **Settings → Pages → Build and deployment → Source → GitHub Actions**. The first deployment is not complete merely because the workflow exists; check the Actions run and the Pages deployment status. Configure the repository variable `VITE_API_BASE_URL` for the backend before a build intended to use that API.

GitHub Pages does not host this Python backend. The backend must be separately deployed to a reachable HTTPS host, its origin must be allowed by backend `ALLOWED_ORIGINS`, and the frontend must be rebuilt with that backend URL. Until all three are configured, the static frontend may load while login, dashboard data, chat, and ticket operations remain unavailable.

## Known limitations

- The frontend currently has four client-side views rather than URL-addressable routes; browser refresh does not select a saved view.
- Ticket management is limited to the backend's existing list, detail, create, and status-update operations. There is no delete operation.
- The backend's default SQLite database and local vector index are not suitable as ephemeral production storage; use persistent hosting volumes or an appropriate managed database and storage plan.
- The readiness endpoint reports provider configuration, not an end-to-end test of an external AI provider.
- No real backend hosting target or production API URL is configured in this repository.
