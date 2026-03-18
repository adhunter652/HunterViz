# Admin Server

Separate server for managing users and dashboards. Uses the **same GCS bucket** as the main app so data is shared. **No sign-in** in the app — access is controlled by **Google IAP**.

## Features

- **User list** — `/users`
- **Edit user** — `/users/{id}` (email, company name)
- **Dashboards** — Add/remove dashboard entries (id + link) on the user object; same data the main app dashboard page reads

## Same as main app

- Security policies (headers, CORS, rate limiting, no secrets in code). See [docs/SECURITY.md](docs/SECURITY.md).
- GCS bucket sync: same bucket, same blob names (`users.json`, etc.), pull on startup and every 20s, push on write.

## Run locally

```bash
cd admin-server
pip install -r requirements.txt
cp .env.example .env
# Set GCS_DATA_BUCKET if you want to sync with the same bucket
uvicorn app.main:app --reload --port 8001
```

Open http://localhost:8001/users .

## Deploy (Cloud Run + IAP)

From repo root:

```bash
gcloud builds submit --config=cloudbuild-admin.yaml .
```

Or create a Cloud Build trigger that uses `cloudbuild-admin.yaml` with source at repo root. Set env vars on the service (e.g. `GCS_DATA_BUCKET`, `PORT=8080`). Deploy with `--no-allow-unauthenticated` and put **IAP** in front so only allowed users can access the admin UI.
