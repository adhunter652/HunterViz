# Security Checklist and Policy

This document defines **security policies** the application must follow and **checklists** for the repository, Google Cloud, and other external systems. Use it before deploying to production and when adding new features.

**Related docs:** [ARCHITECTURE.md](ARCHITECTURE.md) (auth, subscriptions, JSON store), [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md) (Cloud Run, build, env vars).

---

## 1. Security Policies (Must Follow)

These are non-negotiable rules the app and deployment must adhere to.

| Policy | Description |
|--------|-------------|
| **No secrets in code** | API keys, passwords, `SECRET_KEY`, Stripe keys, SMTP credentials, and webhook secrets must never be committed. Use environment variables or Google Secret Manager. |
| **Secrets in production** | In production, `SECRET_KEY` must be strong (e.g. 32+ random bytes, hex or base64). The default `change-me-in-production` must never be used in production. |
| **HTTPS only** | All traffic to the app must be over HTTPS. Cookies must use the `Secure` flag in production. |
| **Least privilege** | Service accounts and IAM roles must have only the permissions they need (e.g. Cloud Run service account: Secret Manager access only for secrets it reads; no broad project roles). |
| **Auth on sensitive routes** | All routes that read or write user or subscription data must require a valid JWT/cookie. Public routes are only: landing, `/health`, `/app/login`, `/app/signup`, `/app/signup`, `/app/subscribe`, `/app/contact` (GET), `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/subscriptions/plan`. |
| **Webhook verification** | Any Stripe (or other provider) webhook endpoint must verify the request signature (e.g. `Stripe-Signature`) before processing. Never process webhook payloads without verification. |
| **No user enumeration** | Login and password-reset flows must return the same generic error (e.g. "Invalid email or password") for wrong email vs wrong password. |
| **Sensitive data not logged** | Do not log tokens, passwords, full card numbers, or full request bodies. Log request IDs and minimal identifiers only. |
| **Dependencies** | Keep Python and system dependencies up to date. Run `pip audit` (or equivalent) and fix known vulnerabilities before release. |

---

## 2. Repository / Application Checklist

Complete these in the **codebase** before treating the app as production-ready.

### 2.1 Authentication and Sessions

- [x] **Cookie flags:** Access token cookie must use `HttpOnly=True` and `Secure=True` in production so it cannot be read by JavaScript and is sent only over HTTPS. *(Implemented: cookie uses `httponly=True`, `secure=config.get_cookie_secure()`; production when `cloud_run_url` is HTTPS and not debug.)*
- [x] **CORS:** Do not use `allow_origins=["*"]` when `allow_credentials=True`. Restrict to your real origins. *(Implemented: `CORS_ORIGINS` env / config; default localhost; middleware never uses `*` with credentials.)*
- [x] **Logout:** Logout must clear the auth cookie. *(Implemented: `POST /api/v1/auth/logout` clears `access_token` cookie with same flags.)*
- [x] **Token storage:** Prefer a single strategy. *(Cookie is HttpOnly; client may also send Bearer; avoid storing same token in non-HttpOnly cookie and localStorage.)*
- [x] **Secret key check:** In production, fail startup if `SECRET_KEY` is missing or default. *(Implemented: startup raises if `is_production()` and secret is placeholder.)*

### 2.2 Passwords and Registration

- [x] **Password policy:** Enforce minimum length (e.g. 8–12 characters) on registration. *(Implemented: min 8 characters in `RegisterBody` and `AuthService.register`.)*
- [x] **Hashing:** Passwords must be hashed with bcrypt or Argon2. *(Implemented: `passlib` with bcrypt in auth_service.)*
- [x] **Same message on login failure:** Use a single generic message for "email not found" and "wrong password". *(Implemented: "Invalid email or password" in auth_service.login.)*

### 2.3 Rate Limiting and Abuse

- [x] **Rate limiting:** Apply rate limiting to login, register, contact, and webhook POST endpoints. *(Implemented in `app/core/api/middleware.py`: 10 requests per 60 seconds per IP per path prefix.)*
- [x] Limits documented in code: `RATE_LIMIT_MAX=10`, `RATE_LIMIT_WINDOW_SEC=60`.

### 2.4 Headers and XSS/Clickjacking

- [x] **Security headers:** Middleware sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Strict-Transport-Security: max-age=31536000; includeSubDomains` in production.
- [x] **Templating:** Jinja2 with `autoescape=True` in `app/core/infrastructure/templating.py`.

### 2.5 Data and Storage

- [x] **User/store files:** `data/*.json` is in `.gitignore`; no route serves `data/` as static (only `static/assets` is mounted).
- [ ] **File permissions:** When running on a server, restrict filesystem permissions on the data directory (e.g. `chmod 700` directory, `600` files). *(Operational: do at deploy or container build.)*
- [ ] **Concurrency:** If using JSON-file store with multiple Cloud Run instances, use `max-instances: 1` or a proper datastore (e.g. Firestore).

### 2.6 Webhooks and Third-Party APIs

- [ ] **Stripe webhooks:** When implementing the webhook endpoint, verify every request with `stripe.Webhook.construct_event(payload, signature_header, webhook_secret)` before processing. *(Required when endpoint is added; see comment in `app/features/subscriptions/api/routes.py`.)*
- [ ] **Idempotency:** Use webhook event IDs (or idempotency keys) to avoid processing the same event twice.

### 2.7 Redirects and Open Redirect

- [x] **Redirects:** Catch-all uses fixed `STATIC_SITE_URL` only; `full_path` is not used as redirect target (`app/main.py`).

### 2.8 Health and Debug

- [x] **Health endpoint:** `/health` returns only `{"status": "ok"}`; no stack traces or secrets.
- [x] **Debug mode:** `DEBUG` defaults to false; app does not enable FastAPI debug or detailed error pages from config.

---

## 3. Google Cloud Checklist

Perform these in **Google Cloud Console** (or gcloud/terraform). See [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md) for setup steps.

### 3.1 Secret Manager (Recommended for Production)

- [ ] **Create secrets** in Secret Manager for sensitive config (do not put these in Cloud Run env vars if you want audit and rotation):
  - `SECRET_KEY` (JWT signing)
  - `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (if using Stripe)
  - `SMTP_PASSWORD` (if using SMTP)
- [ ] **Grant the Cloud Run service account** access to only the secrets it needs:
  - e.g. `roles/secretmanager.secretAccessor` on the specific secrets or a secret prefix.
- [ ] **Configure Cloud Run** to mount or inject these secrets (e.g. "Secret Manager" integration in the Cloud Run service so env vars or volume mounts are populated from Secret Manager). Prefer this over plain env vars for production.

**Example (gcloud) – create secret and grant access:**

```bash
# Create secret (you will be prompted to enter the value, or use --data-file)
gcloud secrets create SECRET_KEY --project=hunterviz --replication-policy=automatic
echo -n "your-strong-random-secret-here" | gcloud secrets versions add SECRET_KEY --data-file=-

# Grant the Cloud Run service account access (replace SERVICE_ACCOUNT_EMAIL)
gcloud secrets add-iam-policy-binding SECRET_KEY \
  --project=hunterviz \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### 3.2 Cloud Run Service

- [ ] **Environment variables:** Never set `SECRET_KEY=change-me-in-production` in production. Use a strong value from Secret Manager or a secure env var (e.g. generated once and stored in Secret Manager).
- [ ] **HTTPS only:** Cloud Run serves HTTPS. Ensure your custom domain (e.g. `app.hunterviz.com`) is mapped to the service and users only access the app via HTTPS.
- [ ] **Allow unauthenticated:** The service is public (`--allow-unauthenticated`); application-level auth (JWT/cookie) protects sensitive routes. Ensure no sensitive data is exposed on public routes (see Policy: Auth on sensitive routes).
- [ ] **Min instances:** You may use `min-instances=0` for cost; be aware of cold starts and JSON-file concurrency if `max-instances > 1` (see Data and Storage above).
- [ ] **Service account:** The Cloud Run service should run as a dedicated service account with minimal roles (e.g. Secret Manager access only for secrets it uses; Storage only if it reads/writes GCS).

### 3.3 IAM and Build

- [ ] **Cloud Build service account** has only the roles needed to build and deploy: e.g. Cloud Run Admin, Artifact Registry Writer, Service Account User for the Cloud Run service account. Avoid broad roles like Owner or Editor.
- [ ] **No long-lived keys in repo:** Cloud Build should use Workload Identity or the default Cloud Build service account; do not commit JSON key files or passwords.

### 3.4 Networking and DNS

- [ ] **Custom domain:** Point `app.hunterviz.com` (or your app domain) to Cloud Run via Load Balancer or Cloud Run custom domain mapping. Use HTTPS and avoid mixed content.
- [ ] **Static site:** If the marketing site is on another host (e.g. hunterviz.com), ensure it only links to HTTPS URLs for the app (e.g. `https://app.hunterviz.com/app/login`).

### 3.5 Logging and Monitoring

- [ ] **Logs:** Ensure Cloud Run logs are retained according to your policy. Do not log request bodies, tokens, or passwords.
- [ ] **Alerts (optional):** Consider alerts on high error rates, repeated 401/403, or unusual traffic to auth endpoints.

---

## 4. Other External / Operational Checklist

Items that are **outside the repo** (Stripe, DNS, team process).

### 4.1 Stripe (When Used)

- [ ] **Webhook signing secret:** In Stripe Dashboard → Developers → Webhooks, create an endpoint for your production URL and copy the **Signing secret**. Store it in Secret Manager (or env) as `STRIPE_WEBHOOK_SECRET`. Never use the publishable key or another value for verification.
- [ ] **Keys:** Use live keys in production; restrict API key usage in Stripe if possible. Store `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in Secret Manager or secure env vars only.
- [ ] **HTTPS:** Webhook URL must be `https://` and reachable by Stripe.

### 4.2 Domain and TLS

- [ ] **TLS:** Custom domain for the app must use a valid certificate (Cloud Run / Load Balancer provide this when you map the domain).
- [ ] **HSTS:** Once security headers are implemented (see Repository checklist), HSTS will instruct browsers to use HTTPS only.

### 4.3 Team and Process

- [ ] **Access:** Only necessary people have deploy access to the GCP project and the Cloud Build trigger. Use IAM and branch protection (e.g. require PR review for `main`).
- [ ] **Secrets rotation:** Plan to rotate `SECRET_KEY` and Stripe/webhook secrets periodically; document how to update Secret Manager and redeploy without downtime (e.g. new secret version, then redeploy to pick it up).
- [ ] **Incident response:** Know how to revoke access, rotate secrets, and roll back a deployment (e.g. redeploy previous image from Artifact Registry).

---

## 5. Quick Reference: Where to Set What

| Item | Where to set | Notes |
|------|----------------------|--------|
| `SECRET_KEY` | Secret Manager (recommended) or Cloud Run env | Must be strong in prod; never default. |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Secret Manager or Cloud Run env | Never in repo. |
| `SMTP_PASSWORD` | Secret Manager or Cloud Run env | Never in repo. |
| CORS origins | Repo (`app/core/api/middleware.py` or config) | Restrict to your domains. |
| Cookie `Secure` / `HttpOnly` | Repo (auth routes) | Set in code; can depend on config (e.g. `cloud_run_url` scheme). |
| Rate limits | Repo (middleware or route deps) | Implement in app. |
| Security headers | Repo (middleware) | Implement in app. |
| Cloud Run service account IAM | Google Cloud Console / gcloud | Least privilege. |
| Webhook URL and signing secret | Stripe Dashboard + Secret Manager / env | Verification in repo. |
| Custom domain → Cloud Run | Load Balancer / Cloud Run custom domain | GCP. |

---

## 6. Summary

- **Policies:** No secrets in code; strong `SECRET_KEY` in prod; HTTPS only; least privilege; auth on sensitive routes; webhook verification; no user enumeration; no sensitive logging; keep dependencies updated.
- **Repo:** Cookie flags, CORS, logout, password policy, rate limiting, security headers, data not in repo, Stripe webhook verification, safe redirects, health/debug off in prod.
- **Google Cloud:** Secret Manager for secrets; Cloud Run env/HTTPS/service account; IAM least privilege; safe build; domain and TLS.
- **Elsewhere:** Stripe webhook secret and keys; domain/TLS; team access and rotation/incident process.

Use this document as the single checklist for making the app **very secure** before and after deployment. Update it when you add new features (e.g. new webhooks or auth flows).
