# Google Cloud Setup: Cloud Run, Buckets, and Build Trigger

This guide walks you through setting up **Google Cloud Run** (scale-to-zero), **GCS buckets**, and a **Cloud Build trigger** so the app builds and deploys automatically on git push. The landing page is hosted by a 3rd party; the three entry routes that can cold-start this service are **`/app/login`**, **`/app/signup`**, and **`/app/contact`**.

**Project:** ID `hunterviz`, number `310331161278`.

For production security (secrets, IAM, rate limiting, cookies, etc.), see **[SECURITY.md](SECURITY.md)**.

---

## 1. Prerequisites

- **Google Cloud SDK (gcloud)** installed and logged in:
  ```bash
  gcloud auth login
  gcloud config set project hunterviz
  ```
- **Billing** enabled on the project.
- **APIs** to enable (run once):
  ```bash
  gcloud services enable run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com
  ```

---

## 2. GCS Buckets

Create buckets for data persistence (Cloud Run’s filesystem is ephemeral; see [ARCHITECTURE.md](ARCHITECTURE.md) for context).

1. **Data bucket** (e.g. for future JSON/store files or volume mount):
   ```bash
   gsutil mb -p hunterviz -l US-CENTRAL1 gs://hunterviz-data
   ```
2. **Optional:** Uploads or assets:
   ```bash
   gsutil mb -p hunterviz -l US-CENTRAL1 gs://hunterviz-uploads
   ```

**IAM:** The Cloud Run service account (e.g. `PROJECT_NUMBER-compute@developer.gserviceaccount.com`) needs read/write on these buckets if the app will use them. For now the app uses local JSON files; when you add GCS support or a volume mount, grant the Run service account `roles/storage.objectAdmin` (or a custom role) on the bucket.

**Location:** Use a region that matches your Cloud Run region (e.g. `US-CENTRAL1`) if you use FUSE or same-region access.

---

## 3. Cloud Run Service

The service runs the container built by Cloud Build (see below). It scales to zero when idle; the first request to any of `/app/login`, `/app/signup`, or `/app/contact` will cold-start it.

### 3.1 Deploy (first time or after building the image)

After the first successful Cloud Build (or a manual build), deploy with:

```bash
gcloud run deploy hunterviz-web \
  --image REGION-docker.pkg.dev/hunterviz/REPO_NAME/IMAGE_NAME:TAG \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "PORT=8080" \
  --set-env-vars "SECRET_KEY=your-secret-key-here" \
  --set-env-vars "CLOUD_RUN_URL=https://app.hunterviz.com"
```

Replace:

- `REGION` (e.g. `us-central1`), `REPO_NAME`, `IMAGE_NAME`, `TAG` with the image built by Cloud Build.
- `CLOUD_RUN_URL` to `https://app.hunterviz.com` (or your custom domain that points to this Cloud Run service).

**Min instances = 0** so the service starts only when a user hits one of the three app routes.

### 3.2 Environment variables

Set these (via `--set-env-vars` or the Cloud Run UI) from [app/core/config.py](../app/core/config.py):

| Variable | Required | Notes |
|----------|----------|--------|
| `PORT` | Yes | Set to `8080` (Cloud Run default). |
| `SECRET_KEY` | Yes | Use a strong secret in production. |
| `CLOUD_RUN_URL` | Yes | App server URL (e.g. `https://app.hunterviz.com`) for redirects. Map this domain to your Cloud Run service. |
| `CONTACT_EMAIL` | Optional | Default in code. |
| `CONTACT_PHONE` | Optional | Default in code. |
| `SMTP_*` | Optional | If you want contact form submissions emailed. |
| `STRIPE_*` | Optional | For subscribe/checkout. |
| `GCS_DATA_BUCKET` | Optional | When set (e.g. `hunterviz-data`), JSON data files are synced to this bucket: pull on startup and every 20s, push on every write. Grant the Cloud Run service account `roles/storage.objectAdmin` on the bucket. |

### 3.3 "STARTUP TCP probe failed" / Connection CANCELLED

If the container fails to start and you see:

- **Default STARTUP TCP probe failed … for container "…" on port 8080**
- **Connection failed with status CANCELLED**

the app is exiting before it can listen on port 8080. The usual cause is **production SECRET_KEY validation**: in production the app refuses to run if `SECRET_KEY` is missing or still the default placeholder, so the process exits and the probe never succeeds.

**Fix:** Set `SECRET_KEY` (and `CLOUD_RUN_URL` if needed) on the Cloud Run service. Either:

1. **One-time via gcloud** (env vars persist across future Cloud Build deploys):
   ```bash
   gcloud run services update hunterviz-web \
     --region us-central1 \
     --set-env-vars "PORT=8080,SECRET_KEY=YOUR_STRONG_SECRET,CLOUD_RUN_URL=https://app.hunterviz.com"
   ```
   Use a strong random value for `SECRET_KEY` (e.g. from `openssl rand -hex 32`). Prefer Secret Manager for production (see [SECURITY.md](SECURITY.md)).

2. **In Google Cloud Console:** Cloud Run → select `hunterviz-web` → Edit & deploy new revision → Variables & secrets → add `SECRET_KEY` (and others as in §3.2).

After saving, new revisions will keep these variables; the next deploy (or a new request that starts an instance) should pass the startup probe.

### 3.4 Three entry routes

The service wakes on the first request to any of:

- **`/app/login`**
- **`/app/signup`**
- **`/app/contact`**

The **landing page is on hunterviz.com** (static). Point the three buttons (Sign in, Sign up, Contact us) to the app subdomain:

- `https://app.hunterviz.com/app/login`
- `https://app.hunterviz.com/app/signup`
- `https://app.hunterviz.com/app/contact`

---

## 4. Cloud Build Trigger (git push)

Build and deploy from this repository so “the build has all the configuration in this repository.”

### 4.1 Connect the repository

- **Option A – GitHub:** In [Cloud Console](https://console.cloud.google.com/cloud-build/triggers) → Triggers → Connect repository → GitHub; authorize and select the repo.
- **Option B – Cloud Source Repositories:** Push a mirror and connect that repo.

### 4.2 Create the trigger

1. **Create trigger** → Name: e.g. `hunterviz-web-deploy`.
2. **Event:** Push to a branch.
3. **Source:** The connected repo; branch `^main$` (or your default branch).
4. **Configuration:** **Cloud Build configuration file (yaml or json)**.
5. **Location:** Repository; path **`cloudbuild.yaml`** (at repo root).

The trigger will run the steps in `cloudbuild.yaml` on every push to `main`. That file builds the Docker image with the repo’s Dockerfile, pushes to Artifact Registry, and deploys to Cloud Run.

### 4.3 Create Artifact Registry repository (once)

Before the first build, create a Docker repository in Artifact Registry (matches `_ARTIFACT_REPO` in `cloudbuild.yaml`, default `docker-repo`):

```bash
gcloud artifacts repositories create docker-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=hunterviz
```

### 4.4 First run

On the first push after adding `cloudbuild.yaml` and the Dockerfile, the build will:

1. Build the image from the Dockerfile in the repo.
2. Push it to Artifact Registry (project `hunterviz`).
3. Deploy to Cloud Run (service name and region as in `cloudbuild.yaml`).

Ensure the Cloud Build service account has roles: **Cloud Run Admin**, **Storage Admin** (for Artifact Registry), and **Service Account User** (for the Cloud Run service account).

---

## 5. Summary

| Step | What you did |
|------|----------------|
| Prerequisites | gcloud, project `hunterviz`, billing, APIs enabled. |
| Buckets | e.g. `hunterviz-data`, optional `hunterviz-uploads`. |
| Cloud Run | Deploy image with min instances = 0; set `PORT`, `SECRET_KEY`, `CLOUD_RUN_URL`. |
| Entry routes | Only `/app/login`, `/app/signup`, `/app/contact` cold-start the service. |
| Trigger | Push to `main` runs `cloudbuild.yaml` → build → push → deploy. |

After the first successful deploy, map **app.hunterviz.com** to your Cloud Run service (e.g. via Load Balancer or Cloud Run custom domain), set **CLOUD_RUN_URL** to `https://app.hunterviz.com`, and ensure the static site at **hunterviz.com** links to the URLs in section 3.3.

---

## 6. Separate admin/build service (optional)

The **admin server** runs in the **same GCP project** as the main server (same project ID). It is a second Cloud Run service that is **not** public and has **separate IAM permissions**.

### 6.1 Why a separate service?

- **Public service** (`hunterviz-web`): `--allow-unauthenticated`; anyone can hit the app; app-level auth (JWT/cookie) protects sensitive routes.
- **Admin service** (`hunterviz-admin`): `--no-allow-unauthenticated`; only IAM principals you grant **Cloud Run Invoker** can call it. Use this for:
  - Admin or client-management UIs/APIs
  - Separate permissions (e.g. only certain users or a dedicated admin service account can invoke it)
  - Same or different codebase (same Dockerfile is fine; differentiate with env vars or routes if needed)

### 6.2 Build and deploy the admin service

The admin app lives in **`admin-server/`** (separate FastAPI app, own Dockerfile). The config **`cloudbuild-admin.yaml`** at repo root builds from `admin-server/` and deploys the admin service.

**If push fails with "Repository docker-repo not found":** Create the Artifact Registry repository once in the same project (both main and admin use the same project and same `docker-repo`):

```bash
gcloud artifacts repositories create docker-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=hunterviz
```

Use your actual project ID if different from `hunterviz`. After this, both `cloudbuild.yaml` (main app) and `cloudbuild-admin.yaml` (admin) push to the same repo.

1. **Create a second Cloud Build trigger** (or run manually):
   - In Cloud Console → Cloud Build → Triggers → **Create trigger**.
   - Name: e.g. `hunterviz-admin-deploy`.
   - Event: Push to branch (e.g. `main`) or **Manual**.
   - Configuration: **Cloud Build configuration file**; path: **`cloudbuild-admin.yaml`** (repo root).

   Or run from repo root (build context is `admin-server/`):
   ```bash
   gcloud builds submit --config=cloudbuild-admin.yaml .
   ```

2. **First-time deploy / env vars:** Set the same required env vars as the public service (e.g. `PORT`, `SECRET_KEY`, `CLOUD_RUN_URL`). You can point `CLOUD_RUN_URL` to the admin URL or a separate base URL if you use one.
   ```bash
   gcloud run services update hunterviz-admin \
     --region us-central1 \
     --set-env-vars "PORT=8080,SECRET_KEY=YOUR_STRONG_SECRET,CLOUD_RUN_URL=https://admin.hunterviz.com"
   ```

3. **Grant access:** Only principals with **Cloud Run Invoker** on `hunterviz-admin` can call it. Grant yourself (or an admin group):
   ```bash
   gcloud run services add-iam-policy-binding hunterviz-admin \
     --region=us-central1 \
     --member="user:your-email@example.com" \
     --role="roles/run.invoker"
   ```
   To call the service, use an identity token (e.g. `gcloud auth print-identity-token`) in the `Authorization: Bearer` header, or use Identity-Aware Proxy in front of it.

### 6.3 Summary

Both services are in the **same GCP project** (same project ID). They share the same Artifact Registry repository (`docker-repo`).

| Service            | Config file              | Access                          | Use case                    |
|--------------------|--------------------------|----------------------------------|-----------------------------|
| `hunterviz-web`    | `cloudbuild.yaml`        | Public (`--allow-unauthenticated`) | App at app.hunterviz.com    |
| `hunterviz-admin`  | `cloudbuild-admin.yaml`  | IAM only (`--no-allow-unauthenticated`) | Client management, admin   |
