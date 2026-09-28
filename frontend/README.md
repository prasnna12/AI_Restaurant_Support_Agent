# DineAssist AI frontend

This React/Vite app is the operations console for the DineAssist FastAPI backend.

## Local development

Start the backend first from the repository root:

```powershell
Push-Location backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
Pop-Location
```

In a second terminal, start the frontend:

```powershell
Push-Location frontend
npm install
npm run dev
Pop-Location
```

Open http://localhost:5173. The frontend sends API requests to `http://localhost:8000` by default. Set `VITE_API_URL` when the backend runs elsewhere.

## Demo login

The backend seeds this administrator on first startup when the default local `.env` settings are used:

- Email: `admin@restaurant.ai`
- Password: `Admin@1234`

Change these values in `backend/.env` for any shared or non-demo environment. Never commit real credentials or API keys.

## Checks

```powershell
Push-Location backend; pytest; Pop-Location
Push-Location frontend; npm run lint; npm run build; Pop-Location
```
