"""HTML page builders for subscription views."""


def subscribe_page_html(
    app_name: str, plan_name: str, plan_description: str, contact_sales: bool
) -> str:
    contact_btn = (
        '<a href="mailto:sales@example.com" class="btn-sales">Contact Sales</a>'
        if contact_sales
        else ""
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Subscribe — {app_name}</title>
  <link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'DM Sans', system-ui, sans-serif; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #0b0f14; color: #e6edf3; padding: 2rem; }}
    .brand {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .brand .logo-img {{ width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0; }}
    .brand .company-name-img {{ height: 28px; width: auto; display: block; }}
    .module {{ width: 100%; max-width: 400px; background: #141a22; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 2rem; text-align: center; }}
    .module h2 {{ margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600; }}
    .module p {{ margin: 0 0 1.5rem 0; color: #8b9cad; line-height: 1.5; }}
    .btn-sales {{ display: inline-block; padding: 0.75rem 1.5rem; background: #3b82f6; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; }}
    .btn-sales:hover {{ background: #2563eb; color: #fff; }}
    .back {{ margin-top: 1.5rem; }}
    .back a {{ color: #3b82f6; text-decoration: none; }}
    .back a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="module">
    <a href="/" class="brand" style="text-decoration:none;color:inherit;">
      <img src="/assets/logo.svg" alt="" class="logo-img">
      <img src="/assets/company-name.svg" alt="{app_name}" class="company-name-img">
    </a>
    <h2>{plan_name}</h2>
    <p>{plan_description}</p>
    {contact_btn}
    <p class="back"><a href="/app">Back to dashboard</a></p>
  </div>
</body>
</html>
"""
