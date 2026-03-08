# HunterViz Web Server

Web app: professional landing page, sign-in/sign-up, user landing, and subscribe page. Built to the architecture in `docs/ARCHITECTURE.md`. Logo and company name image live in `static/assets/`. Set `APP_NAME` in `.env` to customize the business name.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY and DASHBOARD_URL as needed
python run.py
```

Or: `python -m uvicorn app.main:app --reload` (default port 8000).

**Windows:** If you see `[WinError 10013] ... access permissions`, port 8000 is blocked. Use a different port: set `PORT=8080` in `.env` and run `python run.py`, or run `python -m uvicorn app.main:app --reload --port 8080` and open http://127.0.0.1:8080/

- **Landing**: http://127.0.0.1:8000/ (or the port you set) — HunterViz logo and company name (from assets), hero, “Contact us”, Sign in / Sign up (header).
- **Sign in**: http://127.0.0.1:8000/app/login — redirects to user landing after login.
- **Sign up**: http://127.0.0.1:8000/app/signup — after register, redirects to subscribe page.
- **User landing**: http://127.0.0.1:8000/app — company name, dashboard thumbnail; if not subscribed, large warning and “Go to Subscribe”.
- **Subscribe**: http://127.0.0.1:8000/app/subscribe — plan name, description, Contact Sales button.

## Config

- `DASHBOARD_URL`: URL for the “Open Dashboard” link on the user landing page (you can provide this later).
- `SECRET_KEY`: Set a strong value in production.
- `USER_STORE_PATH` / `SUBSCRIPTION_STORE_PATH`: JSON files for users and subscriptions (default `data/`).

## Firebase Hosting + Cloud Run

Use `firebase.json` to serve the static site from Firebase and rewrite `/app` and `/api` to your Cloud Run service. Replace `your-cloud-run-service-id` and `region` with your deployed service. Sign in / Sign up links use `/app/login` and `/app/signup` (same domain when using rewrites).
