# DineAssist AI frontend

This React/Vite app is the operations console for the DineAssist FastAPI backend.

## Local development

Start the backend first from the repository root:

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
Pop-Location
```

In a second terminal, start the frontend:

```powershell
Push-Location frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
Pop-Location
```

Open the local URL printed by Vite. The frontend sends API requests to `http://127.0.0.1:8001` by default. Set `VITE_API_BASE_URL` in `.env.local` when the backend runs elsewhere.

Configure unique administrator credentials in `backend/.env` from `backend/.env.example`. Do not commit real credentials or API keys.

## Checks

```powershell
Push-Location backend; pytest; Pop-Location
Push-Location frontend; npm run lint; npm run build; Pop-Location
```
