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

### 3.3 Three entry routes

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
