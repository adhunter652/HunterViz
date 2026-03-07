"""Public pages and /app routes: login, signup, user landing, subscribe."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId

app_router = APIRouter(tags=["app"])


def _signin_html() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign In - HunterViz</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f5f5f5; }
    .card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); width: 100%; max-width: 360px; }
    h1 { margin: 0 0 1.5rem 0; font-size: 1.5rem; }
    label { display: block; margin-bottom: 0.25rem; font-weight: 500; }
    input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    button { width: 100%; padding: 0.75rem; background: #111; color: #fff; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
    button:hover { background: #333; }
    .error { color: #c00; margin-bottom: 1rem; font-size: 0.9rem; }
    .link { margin-top: 1rem; text-align: center; }
    .link a { color: #0066cc; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Sign In</h1>
    <div id="error" class="error" style="display:none;"></div>
    <form id="form">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" required>
      <label for="password">Password</label>
      <input type="password" id="password" name="password" required>
      <button type="submit">Sign In</button>
    </form>
    <p class="link">Don't have an account? <a href="/app/signup">Sign up</a></p>
  </div>
  <script>
    const form = document.getElementById('form');
    const errorEl = document.getElementById('error');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.style.display = 'none';
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email.value, password: form.password.value })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { errorEl.textContent = data.detail || 'Sign in failed'; errorEl.style.display = 'block'; return; }
      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/app';
    });
  </script>
</body>
</html>
"""


def _signup_html() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign Up - HunterViz</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f5f5f5; }
    .card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); width: 100%; max-width: 360px; }
    h1 { margin: 0 0 1.5rem 0; font-size: 1.5rem; }
    label { display: block; margin-bottom: 0.25rem; font-weight: 500; }
    input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    button { width: 100%; padding: 0.75rem; background: #111; color: #fff; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
    button:hover { background: #333; }
    .error { color: #c00; margin-bottom: 1rem; font-size: 0.9rem; }
    .link { margin-top: 1rem; text-align: center; }
    .link a { color: #0066cc; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Sign Up</h1>
    <div id="error" class="error" style="display:none;"></div>
    <form id="form">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" required>
      <label for="password">Password</label>
      <input type="password" id="password" name="password" required>
      <label for="company_name">Company name</label>
      <input type="text" id="company_name" name="company_name" placeholder="My Company">
      <button type="submit">Sign Up</button>
    </form>
    <p class="link">Already have an account? <a href="/app/login">Sign in</a></p>
  </div>
  <script>
    const form = document.getElementById('form');
    const errorEl = document.getElementById('error');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.style.display = 'none';
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: form.email.value,
          password: form.password.value,
          company_name: form.company_name.value || 'My Company'
        })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { errorEl.textContent = data.detail || 'Sign up failed'; errorEl.style.display = 'block'; return; }
      const loginRes = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email.value, password: form.password.value })
      });
      const loginData = await loginRes.json().catch(() => ({}));
      if (loginRes.ok) localStorage.setItem('access_token', loginData.access_token);
      window.location.href = '/app/subscribe';
    });
  </script>
</body>
</html>
"""


def _user_landing_html(company_name: str, subscribed: bool, dashboard_url: str) -> str:
    warning = ""
    if not subscribed:
        warning = """
    <div class="warning-box">
      <h2>You are not subscribed</h2>
      <p>Subscribe to access the full dashboard and analytics.</p>
      <a href="/app/subscribe" class="btn-warning">Go to Subscribe</a>
    </div>
"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard - HunterViz</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, sans-serif; margin: 0; min-height: 100vh; background: #f5f5f5; padding: 2rem; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }}
    .warning-box {{ background: #fff3cd; border: 2px solid #ff9800; border-radius: 8px; padding: 2rem; margin-bottom: 2rem; text-align: center; max-width: 600px; margin-left: auto; margin-right: auto; }}
    .warning-box h2 {{ margin: 0 0 0.5rem 0; color: #b45309; font-size: 1.5rem; }}
    .warning-box p {{ margin: 0 0 1rem 0; color: #333; }}
    .btn-warning {{ display: inline-block; padding: 0.75rem 1.5rem; background: #ff9800; color: #fff; text-decoration: none; border-radius: 4px; font-weight: 600; }}
    .btn-warning:hover {{ background: #e68900; }}
    h1 {{ margin: 0; font-size: 1.5rem; }}
    .thumbnail {{ display: block; width: 280px; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-decoration: none; color: inherit; text-align: center; margin-top: 1rem; }}
    .thumbnail:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
    .thumbnail span {{ font-size: 1.25rem; font-weight: 500; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{company_name}</h1>
  </div>
{warning}
  <a href="{dashboard_url}" class="thumbnail" target="_blank" rel="noopener">
    <span>Open Dashboard</span>
  </a>
</body>
</html>
"""


def _subscribe_page_html(plan_name: str, plan_description: str, contact_sales: bool) -> str:
    contact_btn = '<a href="mailto:sales@hunterviz.com" class="btn-sales">Contact Sales</a>' if contact_sales else ""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Subscribe - HunterViz</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f5f5; padding: 2rem; }}
    .module {{ width: 100%; max-width: 400px; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 2rem; text-align: center; }}
    .module h2 {{ margin: 0 0 1rem 0; font-size: 1.5rem; }}
    .module p {{ margin: 0 0 1.5rem 0; color: #555; line-height: 1.5; }}
    .btn-sales {{ display: inline-block; padding: 0.75rem 1.5rem; background: #111; color: #fff; text-decoration: none; border-radius: 4px; font-weight: 500; }}
    .btn-sales:hover {{ background: #333; }}
    .back {{ margin-top: 1.5rem; }}
    .back a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <div class="module">
    <h2>{plan_name}</h2>
    <p>{plan_description}</p>
    {contact_btn}
    <p class="back"><a href="/app">Back to dashboard</a></p>
  </div>
</body>
</html>
"""


@app_router.get("/login", response_class=HTMLResponse)
def app_login_page():
    return HTMLResponse(_signin_html())


@app_router.get("/signup", response_class=HTMLResponse)
def app_signup_page():
    return HTMLResponse(_signup_html())


@app_router.get("/subscribe", response_class=HTMLResponse)
def app_subscribe_page(config: Settings = Depends(get_config)):
    from app.features.subscriptions.domain.subscription import DEFAULT_PLAN
    p = DEFAULT_PLAN
    return HTMLResponse(_subscribe_page_html(p["name"], p["description"], p.get("contact_sales", True)))


@app_router.get("", response_class=HTMLResponse)
@app_router.get("/", response_class=HTMLResponse)
def app_user_landing(
    request: Request,
    config: Settings = Depends(get_config),
):
    """User landing: requires auth via token in request (e.g. from cookie or redirect with token)."""
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "").strip()
    if not token and request.cookies:
        token = request.cookies.get("access_token", "")
    if not token:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.core.infrastructure.jwt_utils import decode_token
    payload = decode_token(token, config.secret_key)
    if not payload:
        return RedirectResponse(url="/app/login", status_code=302)
    user_id = payload.get("sub")
    if not user_id:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.features.auth.infrastructure.user_store import JsonUserStore
    from app.features.subscriptions.infrastructure.subscription_store import JsonSubscriptionStore
    user_store = JsonUserStore(config.user_store_path)
    sub_store = JsonSubscriptionStore(config.subscription_store_path)
    user = user_store.get_by_id(UserId(user_id))
    if not user:
        return RedirectResponse(url="/app/login", status_code=302)
    sub = sub_store.get_active_by_user_id(UserId(user_id))
    company_name = user.get("company_name") or "My Company"
    return HTMLResponse(
        _user_landing_html(company_name, sub is not None, config.dashboard_url)
    )
