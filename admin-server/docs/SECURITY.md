# Admin Server — Security

The admin server follows the **same security policies** as the main app (see main repo [SECURITY.md](../../docs/SECURITY.md)), with the following specifics.

## Access control

- **No sign-in in the app.** Authentication and authorization are handled by **Google Identity-Aware Proxy (IAP)**. Deploy the service with `--no-allow-unauthenticated` and put IAP in front so only allowed users can reach the admin UI.
- Do not add login/session logic to the admin server; IAP validates identity and injects headers (e.g. `X-Goog-IAP-JWT-Assertion`). Optionally you can verify that header for audit, but access control is IAP’s responsibility.

## Policies (aligned with main app)

| Policy | How it applies here |
|--------|----------------------|
| **No secrets in code** | Use environment variables or Secret Manager for any secrets. Admin server does not use JWT signing; no `SECRET_KEY`. |
| **HTTPS only** | All traffic over HTTPS. Cloud Run and IAP enforce this. |
| **Least privilege** | Service account for the admin Cloud Run service should have only the permissions it needs (e.g. GCS read/write on the data bucket). |
| **Sensitive data not logged** | Do not log `password_hash`, tokens, or full request bodies. Log request IDs and minimal identifiers only. |
| **Security headers** | Middleware sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and HSTS in production. |
| **CORS** | Restrict `CORS_ORIGINS` to your admin/IAP origin. Never use `*` with credentials. |
| **Rate limiting** | Write endpoints (POST/PUT/DELETE) are rate-limited per IP. |

## Data

- The admin server uses the **same GCS bucket** as the main app (`GCS_DATA_BUCKET`). Same blob names (`users.json`, etc.) so both apps see the same data.
- User store writes preserve all fields (including `password_hash`). The admin UI never displays or logs password hashes.

## Deployment

- Deploy with `--no-allow-unauthenticated`. Grant **Cloud Run Invoker** only to the IAP service account and/or specific users/groups. Configure IAP to protect the admin service URL.
