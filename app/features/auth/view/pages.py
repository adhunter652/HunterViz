"""HTML page builders for auth views."""


def signin_html(app_name: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign In — {app_name}</title>
  <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'DM Sans', system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0b0f14; color: #e6edf3; }}
    .brand {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .brand .logo-img {{ width: 32px; height: 32px; border-radius: 6px; flex-shrink: 0; }}
    .brand .company-name-img {{ height: 24px; width: auto; display: block; }}
    .card {{ background: #141a22; padding: 2rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); width: 100%; max-width: 360px; }}
    h1 {{ margin: 0 0 1.5rem 0; font-size: 1.5rem; font-weight: 600; }}
    label {{ display: block; margin-bottom: 0.25rem; font-weight: 500; color: #8b9cad; font-size: 0.875rem; }}
    input {{ width: 100%; padding: 0.6rem 0.75rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; background: #0b0f14; color: #e6edf3; font-size: 1rem; }}
    input::placeholder {{ color: #6b7a8c; }}
    button {{ width: 100%; padding: 0.75rem; background: #3b82f6; color: #fff; border: none; border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
    button:hover {{ background: #2563eb; }}
    .error {{ color: #f87171; margin-bottom: 1rem; font-size: 0.9rem; }}
    .link {{ margin-top: 1rem; text-align: center; }}
    .link a {{ color: #3b82f6; text-decoration: none; }}
    .link a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <a href="/" class="brand" style="text-decoration:none;color:inherit;">
      <img src="/assets/logo.svg" alt="" class="logo-img">
      <img src="/assets/company-name.svg" alt="{app_name}" class="company-name-img">
    </a>
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
    form.addEventListener('submit', async (e) => {{
      e.preventDefault();
      errorEl.style.display = 'none';
      const res = await fetch('/api/v1/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ email: form.email.value, password: form.password.value }})
      }});
      const data = await res.json().catch(() => ({{}}));
      if (!res.ok) {{ errorEl.textContent = data.detail || 'Sign in failed'; errorEl.style.display = 'block'; return; }}
      localStorage.setItem('access_token', data.access_token);
      window.location.href = '/app';
    }});
  </script>
</body>
</html>
"""


def signup_html(app_name: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign Up — {app_name}</title>
  <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'DM Sans', system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0b0f14; color: #e6edf3; }}
    .brand {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .brand .logo-img {{ width: 32px; height: 32px; border-radius: 6px; flex-shrink: 0; }}
    .brand .company-name-img {{ height: 24px; width: auto; display: block; }}
    .card {{ background: #141a22; padding: 2rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); width: 100%; max-width: 360px; }}
    h1 {{ margin: 0 0 1.5rem 0; font-size: 1.5rem; font-weight: 600; }}
    label {{ display: block; margin-bottom: 0.25rem; font-weight: 500; color: #8b9cad; font-size: 0.875rem; }}
    input {{ width: 100%; padding: 0.6rem 0.75rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; background: #0b0f14; color: #e6edf3; font-size: 1rem; }}
    input::placeholder {{ color: #6b7a8c; }}
    button {{ width: 100%; padding: 0.75rem; background: #3b82f6; color: #fff; border: none; border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
    button:hover {{ background: #2563eb; }}
    .error {{ color: #f87171; margin-bottom: 1rem; font-size: 0.9rem; }}
    .link {{ margin-top: 1rem; text-align: center; }}
    .link a {{ color: #3b82f6; text-decoration: none; }}
    .link a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <a href="/" class="brand" style="text-decoration:none;color:inherit;">
      <img src="/assets/logo.svg" alt="" class="logo-img">
      <img src="/assets/company-name.svg" alt="{app_name}" class="company-name-img">
    </a>
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
    form.addEventListener('submit', async (e) => {{
      e.preventDefault();
      errorEl.style.display = 'none';
      const res = await fetch('/api/v1/auth/register', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          email: form.email.value,
          password: form.password.value,
          company_name: form.company_name.value || 'My Company'
        }})
      }});
      const data = await res.json().catch(() => ({{}}));
      if (!res.ok) {{ errorEl.textContent = data.detail || 'Sign up failed'; errorEl.style.display = 'block'; return; }}
      const loginRes = await fetch('/api/v1/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ email: form.email.value, password: form.password.value }})
      }});
      const loginData = await loginRes.json().catch(() => ({{}}));
      if (loginRes.ok) localStorage.setItem('access_token', loginData.access_token);
      window.location.href = '/app/subscribe';
    }});
  </script>
</body>
</html>
"""


def user_landing_html(
    app_name: str, company_name: str, subscribed: bool, dashboard_url: str
) -> str:
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
  <title>Dashboard — {app_name}</title>
  <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'DM Sans', system-ui, sans-serif; margin: 0; min-height: 100vh; background: #0b0f14; color: #e6edf3; padding: 2rem; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem; }}
    .brand {{ display: flex; align-items: center; gap: 0.5rem; text-decoration: none; color: inherit; }}
    .brand .logo-img {{ width: 32px; height: 32px; border-radius: 6px; flex-shrink: 0; }}
    .brand .company-name-img {{ height: 24px; width: auto; display: block; }}
    .company {{ margin: 0; font-size: 1.25rem; font-weight: 600; }}
    .warning-box {{ background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.4); border-radius: 10px; padding: 2rem; margin-bottom: 2rem; text-align: center; max-width: 600px; margin-left: auto; margin-right: auto; }}
    .warning-box h2 {{ margin: 0 0 0.5rem 0; color: #fbbf24; font-size: 1.25rem; font-weight: 600; }}
    .warning-box p {{ margin: 0 0 1rem 0; color: #8b9cad; }}
    .btn-warning {{ display: inline-block; padding: 0.75rem 1.5rem; background: #f59e0b; color: #0b0f14; text-decoration: none; border-radius: 6px; font-weight: 600; }}
    .btn-warning:hover {{ background: #d97706; color: #0b0f14; }}
    .thumbnail {{ display: block; width: 280px; padding: 2rem; background: #141a22; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; text-decoration: none; color: inherit; text-align: center; margin-top: 1rem; }}
    .thumbnail:hover {{ border-color: #3b82f6; }}
    .thumbnail span {{ font-size: 1.25rem; font-weight: 500; color: #e6edf3; }}
  </style>
</head>
<body>
  <div class="header">
    <a href="/" class="brand">
      <img src="/assets/logo.svg" alt="" class="logo-img">
      <img src="/assets/company-name.svg" alt="{app_name}" class="company-name-img">
    </a>
    <h1 class="company">{company_name}</h1>
  </div>
{warning}
  <a href="{dashboard_url}" class="thumbnail" target="_blank" rel="noopener">
    <span>Open Dashboard</span>
  </a>
</body>
</html>
"""
