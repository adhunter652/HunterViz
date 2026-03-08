# Web App Architecture: Auth & Subscriptions (Python + Stripe)

This document describes an industry-standard architecture for a Python web application that handles **user authentication** and **subscription handling** using **Stripe** for payments and subscriptions. Each feature owns its own **display**: HTML and UI for that feature live in a **view** folder inside the feature.

---

## 1. High-Level Architecture

### 1.1 Layered (Clean) Architecture

Use a **layered architecture** with clear boundaries so each layer has a single responsibility and dependencies point inward (toward domain/business logic).

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer (API / Web Views)                            │
│  - REST/JSON endpoints or server-rendered pages                  │
│  - Request validation, auth middleware, response formatting      │
├─────────────────────────────────────────────────────────────────┤
│  Application / Service Layer                                     │
│  - Use cases: auth, subscription, and feature-specific display   │
│  - Orchestrates domain logic and external services (Stripe)      │
├─────────────────────────────────────────────────────────────────┤
│  Domain Layer                                                    │
│  - Entities: User, Subscription, Plan, Business                  │
│  - Domain rules and value objects                                │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                            │
│  - Database (repositories), Stripe client, email, file storage   │
└─────────────────────────────────────────────────────────────────┘
```

**Principles:**

- **Dependency rule**: Inner layers do not depend on outer layers. Presentation and infrastructure depend on application/domain, not the other way around.
- **Interfaces in domain/application**: Define ports (e.g. `UserRepository`, `PaymentGateway`) in the application layer; implement them in infrastructure.
- **Framework as detail**: Keep FastAPI/Django/Flask in the presentation and wiring layers so business logic stays framework-agnostic.

---

## 2. Recommended Python Stack

| Concern           | Recommendation                    | Rationale                                      |
|------------------|-----------------------------------|------------------------------------------------|
| Web framework    | **FastAPI** or **Django**         | FastAPI: async, OpenAPI, type hints. Django: batteries-included, admin. |
| Auth             | **Authlib** / **python-jose** + **passlib** | JWT/OAuth2 and secure password hashing (bcrypt/argon2). |
| Database ORM     | **SQLAlchemy** (FastAPI) or **Django ORM** | Migrations, models, repository implementations. |
| Stripe           | **stripe** (official SDK)         | Official, well-documented, idempotency support. |
| Config / secrets | **pydantic-settings** or **django-environ** | Env-based config, no secrets in code.          |
| Task queue       | **Celery** or **ARQ** (async)     | Webhooks, emails, subscription sync off the request path. |

---

## 3. Feature-Based Project Structure (Core + Features)

The codebase is organized by **features**, with a shared **core**. Layers (presentation, application, domain, infrastructure) are preserved **inside** each feature and inside core. This keeps each feature self-contained and makes it clear where new behavior belongs.

### 3.1 Rules for Core vs Features

| Rule | Description |
|------|-------------|
| **Core** | Holds shared code used by more than one feature: config, logging, auth interfaces, shared domain types, and shared infrastructure (e.g. file storage abstraction). No business logic that belongs to a single feature. |
| **Features** | Each feature is a vertical slice: its own API routes, **view** folder (HTML/templates for that feature), use cases, domain entities, and infrastructure. One feature = one bounded context (e.g. auth, subscriptions). There is no separate "business display" feature—each feature owns its own display files. |
| **Dependencies** | Features may depend on **core**. Features should **not** depend on other features; if two features need to collaborate, either move the shared part to core or expose a small interface in core that one feature implements and the other consumes. |
| **Layers inside each** | Both `core/` and each folder under `features/` keep the same layer names: `api/`, `application/`, `domain/`, `infrastructure/`, plus a **view/** folder for that feature's HTML. This keeps the dependency rule (inner layers don’t depend on outer) consistent everywhere. |

### 3.2 Directory Layout

```
web-server/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App entry: mount core + feature routers, wire DI
│   │
│   ├── core/                       # Shared across all features
│   │   ├── __init__.py
│   │   ├── config.py               # Settings from environment
│   │   │
│   │   ├── api/                    # Shared presentation
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # get_current_user, get_config, common deps
│   │   │   └── middleware.py       # CORS, request ID, rate limit
│   │   │
│   │   ├── application/            # Shared use cases / ports only
│   │   │   ├── __init__.py
│   │   │   └── ports.py            # Abstract interfaces (e.g. UserRepository, TokenService)
│   │   │
│   │   ├── domain/                 # Shared domain only if needed
│   │   │   ├── __init__.py
│   │   │   └── value_objects.py    # Shared value types (e.g. UserId, Email)
│   │   │
│   │   └── infrastructure/         # Shared infra used by multiple features
│   │       ├── __init__.py
│   │       ├── file_storage.py     # Read/write JSON or files (used by user store)
│   │       └── logging.py          # Structured logger
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py       # POST login, register, refresh, logout
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   └── auth_service.py # Register, login, verify token
│   │   │   ├── domain/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user.py         # User entity, roles
│   │   │   ├── infrastructure/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_store.py   # Implements UserRepository (e.g. JSON file)
│   │   │   └── view/               # HTML/templates for this feature
│   │   │       ├── login.html
│   │   │       ├── signup.html
│   │   │       └── ...
│   │   │
│   │   ├── subscriptions/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py       # Checkout, portal, webhook endpoint
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   └── subscription_service.py
│   │   │   ├── domain/
│   │   │   │   ├── __init__.py
│   │   │   │   └── subscription.py # Subscription, Plan, status
│   │   │   ├── infrastructure/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── stripe_client.py
│   │   │   │   └── subscription_store.py  # e.g. JSON or same file as users
│   │   │   └── view/               # HTML/templates for this feature
│   │   │       ├── checkout.html
│   │   │       ├── billing.html
│   │   │       └── ...
│   │   │
│   └── shared_schemas/            # Optional: Pydantic request/response models shared by API
│       └── __init__.py
│
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   └── features/
│   │       ├── auth/
│   │       └── subscriptions/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   └── ARCHITECTURE.md
│
├── requirements.txt
├── .env.example
└── README.md
```

### 3.3 Wiring in `main.py`

- Import and include each feature’s router (e.g. `features.auth.api.routes.router` with prefix `/api/v1/auth`).
- Build dependencies (e.g. `UserRepository` → JSON user store, `SubscriptionService` with Stripe client and subscription store) and inject them into core `deps` or feature routes so that **features stay decoupled** and testable with mocks.

---

## 4. User Authentication

### 4.1 Industry-Standard Practices

- **Passwords**: Hash with **bcrypt** or **Argon2** (e.g. `passlib` with `bcrypt` or `argon2-cffi`). Never store plain text or weakly hashed passwords.
- **Sessions / tokens**: Prefer **JWT** (access + refresh) or **server-side sessions** (e.g. Redis/DB) with secure, HttpOnly cookies.
- **HTTPS only**: Enforce TLS; set `Secure` and `SameSite` on cookies.
- **Rate limiting**: Apply to login, register, and password-reset endpoints to prevent brute force and abuse.
- **OAuth2 / OIDC**: Optional; use **Authlib** or **python-social-auth** for “Login with Google/GitHub” and keep a single source of truth for identity (your `User` table linked to `stripe_customer_id`).

### 4.2 Suggested Auth Flow

1. **Register**: Validate email/password → hash password → create `User` in DB → (optional) create Stripe Customer and store `stripe_customer_id`.
2. **Login**: Validate credentials → issue **access token** (short-lived, e.g. 15 min) and **refresh token** (long-lived, e.g. 7 days, stored or signed).
3. **Protected routes**: Middleware/dependency validates JWT or session and attaches `current_user` to the request.
4. **Refresh**: Accept refresh token, validate, issue new access (and optionally refresh) token.
5. **Logout**: Invalidate refresh token (if stored) or rely on client discarding tokens; for JWTs, consider a short blocklist for high-security logout.

### 4.3 Linking Auth to Stripe

- Create a **Stripe Customer** when the user registers (or on first subscription attempt). Store `stripe_customer_id` on `User`.
- Use this `stripe_customer_id` for all Stripe API calls (Checkout, Customer Portal, Subscriptions) so billing is tied to the same identity as auth.

---

## 5. Subscription Handling with Stripe

### 5.1 Stripe Building Blocks

| Need                     | Stripe feature           | Use in your app                          |
|--------------------------|--------------------------|------------------------------------------|
| One-time payments        | **Payment Intents** or **Checkout (one-time)** | One-off purchases, add-ons               |
| Recurring subscriptions  | **Subscriptions** + **Prices** | Monthly/yearly plans                     |
| Checkout UI              | **Checkout Session**     | Redirect users to Stripe-hosted checkout  |
| Self-service management  | **Customer Portal**      | Update payment method, cancel, change plan |
| Async events             | **Webhooks**             | Sync subscription status to your DB      |

### 5.2 Recommended Subscription Flow

1. **Product/Price setup (Stripe Dashboard)**  
   Create **Products** and **Prices** (recurring) in Stripe. Store `price_id` (e.g. in config or DB) per plan.

2. **Start subscription (your backend)**  
   - Authenticate user (JWT/session).  
   - Ensure user has a `stripe_customer_id` (create if not).  
   - Create a **Checkout Session** with:
     - `mode='subscription'`
     - `line_items=[{ price: price_id, quantity: 1 }]`
     - `customer=stripe_customer_id`
     - `success_url` / `cancel_url` (your frontend or backend-rendered pages)
     - `metadata={ "user_id": str(user.id) }` for idempotency and linking
   - Return the Checkout Session `url` to the client; redirect user to it.

3. **After payment (Stripe redirects to success_url)**  
   - Do **not** trust the redirect alone for granting access.  
   - Rely on **webhooks** to update your DB (e.g. `customer.subscription.created` / `updated` / `deleted`).  
   - On success_url, show a “Thank you” page and optionally poll your API for “subscription active” or refresh user state.

4. **Customer Portal (manage/cancel/upgrade)**  
   - Create a **Customer Portal Session** with `customer=stripe_customer_id` and `return_url` to your app.  
   - Return the portal `url`; user completes changes on Stripe.  
   - Webhooks again drive the source of truth in your DB.

### 5.3 Webhooks (Critical)

- **Endpoint**: e.g. `POST /api/v1/webhooks/stripe` (no auth; verified by signature).
- **Verification**: Always verify `Stripe-Signature` using `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`.
- **Idempotency**: Use `event.id` (or event + idempotency key) to avoid processing the same event twice.
- **Processing**: Handle at least:
  - `checkout.session.completed` — link subscription to user if needed.
  - `customer.subscription.created` / `updated` / `deleted` — create/update/delete subscription row and set status (active, past_due, canceled, etc.).
  - `invoice.payment_failed` — optional: notify user, retry logic, or dunning.
- **Async**: Process webhooks in a **background task** (Celery/ARQ): return 200 quickly, then enqueue job. Retry with exponential backoff on failure; Stripe will retry delivery.

### 5.4 Granting Access Based on Subscription

- In your **application layer**, expose something like `get_active_subscription(user_id)` (from DB).
- **Authorization**: After authentication, check “does this user have an active subscription for this feature?” and return 403 or redirect to upgrade if not.
- **Single source of truth**: Subscription status in your DB, updated by webhooks—not by the redirect from Checkout.

---

## 6. Per-Feature Display (View Folder)

Each feature owns its own display. HTML and templates for a feature live in that feature's **view/** folder (e.g. `features/auth/view/`, `features/subscriptions/view/`).

- **Public pages**: Marketing/landing, pricing, feature list—can live in a feature that owns "marketing" or in a dedicated feature with its own view folder. No auth required.
- **Authenticated pages**: Dashboard, account, billing (links to Stripe Checkout/Portal), usage or feature access—each served by the feature that owns that behavior, from its own **view/** folder.
- **Separation**: Use route groups or modules per feature; each feature’s API routes serve both JSON and server-rendered pages from its **view/** folder. Middleware/dependencies enforce “public” vs “authenticated” vs “subscribed.”

---

## 7. Cloud Run Deployment and JSON User Store (No Cloud SQL)

The server is deployed as a **Cloud Run service** (containerized). Without Cloud SQL, user and subscription state can be stored in **JSON files** that are read on login and updated by the app and by webhooks.

### 7.1 Is JSON-File User Storage Secure?

Yes, **if done carefully**:

- **Passwords**: Never store plain-text passwords. Store only **bcrypt/Argon2 hashes** in the JSON (same as with a DB). Treat the file as sensitive.
- **File location**: Store the file **outside** any web root and outside version control. Use a path provided by config (e.g. `USER_STORE_PATH`).
- **Permissions**: Restrict file permissions so only the process that runs the app can read/write (e.g. `chmod 600` on the file; ensure the Cloud Run service account has no broader access than needed).
- **Secrets**: Do not put API keys or tokens in the JSON file; keep them in environment variables or Secret Manager.
- **HTTPS**: All traffic to Cloud Run is HTTPS; data in transit is protected. At rest, the file lives on the container filesystem (or a mounted volume); for high sensitivity, consider encrypting the file or using Secret Manager / encrypted volume.

The main **operational** limitation is **concurrency and multi-instance behavior** (see below).

### 7.2 How It Fits the Architecture

- **Port**: In `core/application/ports.py`, define `UserRepository` (e.g. `get_by_id`, `get_by_email`, `save`). The auth feature's application layer depends only on this port.
- **Adapter**: In `features/auth/infrastructure/user_store.py`, implement a **JSON file–backed** `UserRepository`: on login, **load the JSON file**, find the user by email (or id), verify password hash, and return the user. On register or update, **read the full file**, update the in-memory structure, then **write the file atomically** (write to a temp file, then rename to the canonical path) to avoid corruption on crash.
- **Subscription state**: Use the same pattern: a `SubscriptionRepository` implemented by a JSON file (or a second file keyed by `user_id` or `subscription_id`), updated by your webhook handler and read by your application layer. Stripe remains the source of truth for billing; the JSON file is a **cache** of subscription status for fast access per request.

This keeps the architecture unchanged: you can later swap the JSON implementation for a DB (e.g. Firestore or Cloud SQL) by adding a new adapter that implements the same port.

### 7.3 Cloud Run–Specific Considerations

- **Ephemeral filesystem**: By default, each Cloud Run instance has its own local disk; anything written there is lost when the instance is scaled down. So the JSON file must live on a **persistent volume** (e.g. Cloud Run volume mount from Cloud Storage via FUSE, or a small Filestore instance) if you need data to survive restarts and scale-to-zero. Alternatively, use a **serverless datastore** (e.g. Firestore) that requires no Cloud SQL and fits the same repository interface.
- **Multiple instances**: If you run more than one instance, **multiple processes will read/write the same file**. To stay safe with a single JSON file:
  - Prefer **single-instance** Cloud Run (set `max-instances: 1`) so only one process writes, **or**
  - Use **atomic writes** (write to temp + rename) and accept that last-write-wins is acceptable for your use case and that concurrent webhook and login updates may occasionally overwrite each other. For strict consistency across instances, use Firestore or another datastore instead of a shared file.
- **Cold start**: On cold start, reading a large JSON file can add latency. Keep the file small (e.g. only user id, email, password hash, `stripe_customer_id`); avoid storing large blobs.

### 7.4 Suggested JSON Shape (Users)

Store one JSON file (e.g. `users.json`) with a structure like:

```json
{
  "users": [
    {
      "id": "uuid-or-stable-id",
      "email": "user@example.com",
      "password_hash": "$2b$12$...",
      "stripe_customer_id": "cus_xxx",
      "created_at": "2025-03-07T12:00:00Z"
    }
  ]
}
```

- **Fetch on login**: Load file → find user by `email` → verify password with `passlib` → return user (id, email, stripe_customer_id). No need to expose `password_hash` outside the repository.
- **Ids**: Use a stable **user id** (UUID or ulid) as primary key; Stripe webhooks can carry `user_id` in metadata to associate subscriptions with users.

### 7.5 Summary

- **JSON file for user store is secure** when passwords are hashed, file location and permissions are restricted, and secrets stay in env/Secret Manager.
- **Architecture stays feature-based and layered**: implement `UserRepository` (and optional `SubscriptionRepository`) with JSON in `features/auth/infrastructure` (and `features/subscriptions/infrastructure`), and keep the rest of the app unchanged.
- **Cloud Run**: Use a **persistent volume** for the JSON file if you scale to zero or multiple instances; otherwise prefer **single instance** or move to **Firestore** (or similar) for multi-instance safety.

---

## 8. Static Site + Cloud Run (Only Start Backend on Sign In / Sign Up)

To avoid Cloud Run starting (and incurring cost or cold starts) when someone simply visits your URL, host the **public, static part** of the site on **Firebase Hosting** and use **same-domain path rewrites** so that only `/app` and `/api` hit Cloud Run. The Cloud Run service is only invoked when the user clicks **Sign in** or **Sign up** (or otherwise hits those paths).

### 8.1 Chosen approach: Same domain with Firebase Hosting rewrites

- **Static**: `https://yourapp.com/`, `/pricing`, `/about`, etc. → Firebase Hosting (static files). No Cloud Run.
- **App**: `https://yourapp.com/app` and `https://yourapp.com/app/*` → rewritten to Cloud Run (login, signup, dashboard).
- **API**: `https://yourapp.com/api/*` → rewritten to Cloud Run (auth, subscriptions, webhooks).
- **Sign in / Sign up**: Buttons link to `https://yourapp.com/app` (or `/app/login`, `/app/signup`). First request to that path hits Cloud Run and starts the service.
- **CORS**: Not needed for same-origin; all requests are to `yourapp.com`. Cookies work on the same domain.

### 8.2 Flow

1. **User visits** `https://yourapp.com` → Firebase Hosting serves the static landing page. No Cloud Run.
2. **User browses** `/pricing`, `/about` → static files from Firebase. Still no Cloud Run.
3. **User clicks “Sign in” or “Sign up”** → navigates to `https://yourapp.com/app` (or `/app/login`). Firebase rewrites that path to Cloud Run; first request **starts** the Cloud Run service (cold start if scaled to zero).
4. After that, all `/app/*` and `/api/*` traffic goes to Cloud Run until the user leaves.

So: **Firebase Hosting = static site, always-on, free, no cold start**. **Cloud Run = only when the user enters the app (sign in / sign up or app paths).**

### 8.3 Firebase Hosting configuration

Use **Firebase Hosting** as the static host (same GCP project as Cloud Run). Configure rewrites so only `/app` and `/api` are proxied to your Cloud Run service; everything else is served as static files.

Example **`firebase.json`** (in the project that deploys the static site):

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/app/**",
        "run": {
          "serviceId": "your-cloud-run-service-id",
          "region": "us-central1"
        }
      },
      {
        "source": "/api/**",
        "run": {
          "serviceId": "your-cloud-run-service-id",
          "region": "us-central1"
        }
      }
    ]
  }
}
```

- **`public`**: Directory containing your static build (e.g. `dist` from your frontend build). Served for `/`, `/pricing`, `/about`, and any path that does not match a rewrite.
- **`rewrites`**: Requests to `/app/**` and `/api/**` are sent to the Cloud Run service. Replace `your-cloud-run-service-id` and `region` with your actual Cloud Run service ID and region.
- **Linking Cloud Run**: In Firebase (and optionally in the same repo), ensure the Hosting rewrites point to the deployed Cloud Run service. You can deploy Hosting and Cloud Run separately; Hosting only needs the service ID and region to proxy.

Static site: “Sign in” and “Sign up” should link to **`/app`** or **`/app/login`** and **`/app/signup`** so the first navigation triggers the rewrite and starts Cloud Run.

**Cloud Run path handling**: Requests rewritten from Firebase arrive at Cloud Run with the same path (e.g. `/app/login`, `/api/v1/auth/login`). Your app should mount routes under `/app` and `/api` (e.g. in `main.py`) so these paths are handled correctly.

### 8.4 What to Put Where

| Content | Served by | Reason |
|--------|-----------|--------|
| Landing, marketing, pricing, “Sign in” / “Sign up” **buttons** | Firebase Hosting (static) | No Cloud Run; free; no cold start. |
| `/app`, `/app/login`, `/app/signup`, dashboard, billing | Cloud Run (via rewrite) | First request to `/app` starts Cloud Run. |
| Auth API (`/api/v1/auth/login`, etc.) | Cloud Run (via `/api` rewrite) | Backend only. |
| Stripe webhooks | Cloud Run (e.g. `/api/v1/webhooks/stripe`) | Backend only. |

“Sign in” / “Sign up” on the static site link to **`/app`** or **`/app/login`** so the user is sent through the rewrite to Cloud Run; that first request starts the service.

### 8.5 Summary

- **Firebase Hosting** serves the static site on the **same domain**; hitting the main URL or static paths does **not** start Cloud Run.
- **Rewrites** send only **`/app/**`** and **`/api/**`** to Cloud Run. “Sign in” / “Sign up” point to `/app` (or `/app/login`, `/app/signup`).
- **Cloud Run** starts only when the user clicks Sign in / Sign up (or otherwise hits `/app` or `/api`). Same domain means no CORS and straightforward cookies.

---

## 9. Security Checklist

- [ ] All credentials and API keys in environment variables (e.g. `.env`), never in code.
- [ ] Stripe **webhook secret** used only for signature verification; different from publishable/secret key.
- [ ] **CORS** restricted to your frontend origins.
- [ ] **Rate limiting** on auth and webhook endpoints.
- [ ] **SQL injection**: Use ORM/parameterized queries only.
- [ ] **XSS**: Sanitize or escape output if rendering HTML; prefer a frontend framework with safe templating.
- [ ] **CSRF**: Use CSRF tokens for state-changing browser requests if using cookie-based sessions.
- [ ] **Least privilege**: DB user and Stripe key scope limited to what the app needs.

---

## 10. Scalability and Operations

- **User / subscription store**: With JSON-file storage (Cloud Run, no Cloud SQL), use a **persistent volume** and **single instance** or **atomic writes**; for multi-instance scaling, prefer Firestore or another serverless datastore. With a SQL DB: use connection pooling (e.g. SQLAlchemy pool); consider read replicas for read-heavy pages and reporting.
- **Stripe**: Use **idempotency keys** for Create operations (Checkout Session, Customer, etc.) when retrying.
- **Caching**: Optional cache (e.g. Redis) for session or “current plan” to reduce DB load.
- **Logging**: Structured logs (JSON) with request ID; no sensitive data (no tokens, full card numbers).
- **Health**: `/health` and `/ready` endpoints for load balancers and orchestrators; optionally check DB and Stripe connectivity in `/ready`.

---

## 11. Summary Diagram

```
                    ┌──────────────┐
                    │   Client     │
                    │ (Browser/SPA)│
                    └──────┬───────┘
                           │ HTTPS
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Python Web Application                        │
│  ┌─────────────┐  ┌─────────────┐                                │
│  │ Auth API    │  │ Subs API    │  (each feature has api/ + view/)│
│  │ + view/     │  │ + view/     │                                │
│  │ (login,     │  │ (checkout,  │                                │
│  │  register,  │  │  portal,    │                                │
│  │  pages)     │  │  webhook,   │                                │
│  └──────┬──────┘  └──────┬──────┘                                │
│         │                │                                         │
│         ▼                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Application / Service Layer                      ││
│  │  (auth, subscription use cases; each feature owns its display) ││
│  └──────┬────────────────────┬────────────────────┬────────────┘│
│         │                    │                                       │
│         ▼                    ▼                                       │
│  ┌────────────┐     ┌───────────────┐     ┌──────────────┐          │
│  │   User     │     │   Stripe      │     │  Repository  │          │
│  │ Repository │     │   Client      │     │ (subscription)│          │
│  └──────┬─────┘     └───────┬───────┘     └──────┬───────┘          │
│         │                   │                    │                │
└─────────┼───────────────────┼────────────────────┼────────────────┘
          │                   │                    │
          ▼                   ▼                    ▼
   ┌────────────┐      ┌────────────┐      ┌────────────┐
   │ User store │      │   Stripe   │      │ Subscription│
   │ (JSON file)│      │   API      │      │ store (JSON)│
   └────────────┘      └────────────┘      └────────────┘
                              │
                              │ Webhooks (async)
                              ▼
                       ┌────────────┐
                       │  Webhook   │
                       │  Handler   │ → Update DB, send email, etc.
                       └────────────┘
```

---

This architecture gives you a clear separation of concerns, secure auth, reliable subscription state via Stripe and webhooks, and a scalable structure for adding more features later. Implement incrementally: auth first (including its view/ pages), then Stripe Checkout and webhooks, then Customer Portal and each feature's view/ as needed.
