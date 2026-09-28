# Repository Instructions

## Project Layout
- `backend/` is a FastAPI application. Its entry point is `app.main:app`; routers live in `app/api/`, and supporting code is organized into `agents/`, `core/`, `db/`, `models/`, `rag/`, `repositories/`, `schemas/`, `tools/`, and `workflows/`.
- `backend/tests/` contains pytest tests. `backend/pytest.ini` sets this test directory and enables automatic asyncio mode.
- `frontend/` is a React 19 application built with Vite. Application code is under `frontend/src/`.
- The backend uses SQLAlchemy and Pydantic Settings. The frontend uses Axios, React Router, Recharts, and Lucide React.

## Commands
Run commands from the relevant project directory:
- Backend tests: `cd backend && pytest`
- Backend development server: `cd backend && uvicorn app.main:app --reload`
- Frontend development server: `cd frontend && npm run dev`
- Frontend production build: `cd frontend && npm run build`
- Frontend lint: `cd frontend && npm run lint`

The backend loads `.env` relative to its current working directory. Use `backend/.env.example` as the configuration reference; never commit real API keys or other secrets.

## Working Agreements
- Keep changes scoped to the requested behavior and follow nearby patterns before adding abstractions or dependencies.
- Preserve the API contracts between the frontend and backend; inspect the relevant route, schema, and client call when changing an endpoint.
- Add or update focused pytest coverage for backend behavior changes. Run the frontend lint/build checks for relevant frontend changes.
- Keep configuration and credentials out of source code. Prefer environment settings defined in `backend/app/core/config.py`.
- Avoid modifying generated data, local databases, caches, `node_modules/`, or environment files unless the task explicitly requires it.
