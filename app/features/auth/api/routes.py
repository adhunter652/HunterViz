"""POST login, register, refresh; serve sign-in/sign-up and dashboard pages from templates."""
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.core.infrastructure.templating import render_template
from app.features.auth.application.auth_service import AuthService
from app.core.infrastructure.google_drive import share_report, extract_file_id

from starlette.requests import Request as StarletteRequest
from authlib.integrations.starlette_client import OAuth

router = APIRouter(prefix="/auth", tags=["auth"])
pages_router = APIRouter(tags=["auth-views"])

oauth = OAuth()


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="At least 8 characters")
    company_name: str = ""


def get_auth_service(settings: Settings) -> AuthService:
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    user_repo = FirestoreUserStore()
    company_repo = FirestoreCompanyStore()
    return AuthService(
        user_repository=user_repo,
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        company_repository=company_repo,
    )


@router.post("/login")
def login(body: LoginBody, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        data = service.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    response = JSONResponse(content=data)
    response.set_cookie(
        key="access_token",
        value=data["access_token"],
        path="/",
        max_age=config.access_token_expire_minutes * 60,
        samesite="lax",
        httponly=True,
        secure=config.get_cookie_secure(),
    )
    return response


@router.post("/register", response_model=dict)
def register(body: RegisterBody, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        return service.register(body.email, body.password, body.company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
def me(user_id: UserId = Depends(get_current_user_id), config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout")
def logout(config: Settings = Depends(get_config)):
    """Clear the auth cookie. Client should discard any stored token."""
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=config.get_cookie_secure(),
        samesite="lax",
    )
    return response


class RefreshDataBody(BaseModel):
    dashboard_id: Optional[str] = None


from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
import json
import httpx


@router.post("/refresh-data")
async def refresh_data(
    body: Optional[RefreshDataBody] = None,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config),
):
    """Trigger a data refresh and stream progress updates."""
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    store = FirestoreUserStore()
    user = store.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dashboards = user.get("dashboards") or []
    refresh_url = None
    
    if body and body.dashboard_id:
        for d in dashboards:
            if d.get("id") == body.dashboard_id:
                refresh_url = d.get("refresh_url")
                break
    elif dashboards:
        refresh_url = dashboards[0].get("refresh_url")

    async def event_generator():
        yield json.dumps({"status": "starting", "message": "Starting data refresh..."}) + "\n"
        
        # Give the "safe to navigate away" message early
        yield json.dumps({
            "status": "info", 
            "message": "This process usually takes several minutes. You can safely navigate away or close this tab; your data will update in the background."
        }) + "\n"

        if not refresh_url:
            # Fallback/Demo mode
            import asyncio
            await asyncio.sleep(2)
            yield json.dumps({"status": "progress", "message": "Fetching latest records..."}) + "\n"
            await asyncio.sleep(3)
            yield json.dumps({"status": "progress", "message": "Processing transformations..."}) + "\n"
            await asyncio.sleep(2)
            yield json.dumps({"status": "complete", "message": "Refresh complete!"}) + "\n"
            return

        # Real call to the pipeline
        try:
            yield json.dumps({"status": "triggering", "message": "Triggering data pipeline..."}) + "\n"
            
            async with httpx.AsyncClient() as client:
                # Use a long timeout for the pipeline call
                # Note: If the pipeline itself takes 10 mins, we might want to just trigger it 
                # and return "Started", but here we'll try to wait for it if possible.
                response = await client.post(refresh_url, timeout=300.0) 
                
                if response.status_code == 200:
                    yield json.dumps({"status": "complete", "message": "Pipeline finished successfully!"}) + "\n"
                else:
                    yield json.dumps({
                        "status": "error", 
                        "message": f"Pipeline returned error {response.status_code}: {response.text[:100]}"
                    }) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to trigger refresh: {str(e)}"}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# --- Google OAuth ---

@router.get("/google/login")
async def google_login(request: Request, config: Settings = Depends(get_config)):
    if not config.google_client_id or not config.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    oauth.register(
        name='google',
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    redirect_uri = request.url_for('google_callback')
    # If running behind a proxy (like Cloud Run), ensure redirect_uri uses https
    if config.is_production():
        redirect_uri = str(redirect_uri).replace("http://", "https://")
        
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="No user info from Google")
    
    email = user_info.get('email')
    data = service.get_or_create_google_user(email)
    
    response = RedirectResponse(url="/app/complete-profile" if data["is_new"] else "/app/")
    response.set_cookie(
        key="access_token",
        value=data["access_token"],
        path="/",
        max_age=config.access_token_expire_minutes * 60,
        samesite="lax",
        httponly=True,
        secure=config.get_cookie_secure(),
    )
    return response


@router.post("/complete-profile")
def complete_profile(
    company_name: str = Form(..., alias="company_name"),
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    service = get_auth_service(config)
    try:
        service.update_company_name(user_id, company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/app/", status_code=303)


# --- App pages (HTML from feature templates) ---


@pages_router.get("/login", response_class=HTMLResponse)
def login_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "login", {"app_name": config.app_name}))


@pages_router.get("/signup", response_class=HTMLResponse)
def signup_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "signup", {"app_name": config.app_name}))


@pages_router.get("/complete-profile", response_class=HTMLResponse)
def complete_profile_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "complete_profile", {"app_name": config.app_name}))


@pages_router.get("", response_class=HTMLResponse)
@pages_router.get("/", response_class=HTMLResponse)
def user_landing(request: Request, config: Settings = Depends(get_config)):
    """User landing: requires auth via token in request (cookie or Bearer)."""
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
    user_store = FirestoreUserStore()
    company_store = FirestoreCompanyStore()
    sub_store = JsonSubscriptionStore(config.subscription_store_path)
    
    user = user_store.get_by_id(UserId(user_id))
    if not user:
        return RedirectResponse(url="/app/login", status_code=302)
    
    sub = sub_store.get_active_by_user_id(UserId(user_id))
    primary_company_name = user.get("company_name") or "My Company"
    user_email = user.get("email")
    
    # 1. Collect all dashboards (owned + shared)
    all_dashboards = []
    
    # Owned dashboards
    owned_dashboards = user.get("dashboards") or []
    for d in owned_dashboards:
        d_copy = d.copy()
        if not d_copy.get("company_name"):
            d_copy["company_name"] = primary_company_name
        all_dashboards.append(d_copy)
        
    # Shared dashboards (from other companies)
    member_companies = company_store.list_by_member_email(user_email)
    for c in member_companies:
        owner_id = c.get("owner_id")
        if owner_id == user_id: continue # Handled by owned_companies
        
        owner_doc = user_store.get_by_id(UserId(owner_id))
        if not owner_doc: continue
        
        owner_dashboards = owner_doc.get("dashboards") or []
        allowed_ids = c.get("members", {}).get(user_email, {}).get("report_ids", [])
        
        for d in owner_dashboards:
            if "all" in allowed_ids or d.get("id") in allowed_ids:
                d_copy = d.copy()
                d_copy["company_id"] = c.get("id")
                d_copy["company_name"] = c.get("name")
                d_copy["is_shared"] = True
                all_dashboards.append(d_copy)

    # 2. Companies for the filter dropdown
    owned_companies = company_store.list_by_owner(user_id)
    
    return HTMLResponse(
        render_template(
            "auth",
            "dashboard",
            {
                "app_name": config.app_name,
                "company_name": primary_company_name,
                "subscribed": sub is not None,
                "dashboards": all_dashboards,
                "owned_companies": owned_companies,
                "member_companies": member_companies,
                "user_email": user_email,
            },
        )
    )


class ShareDashboardBody(BaseModel):
    dashboard_id: str
    email: EmailStr


class CreateCompanyBody(BaseModel):
    name: str


@router.post("/companies")
async def create_company(
    body: CreateCompanyBody,
    user_id: UserId = Depends(get_current_user_id),
):
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    store = FirestoreCompanyStore()
    new_company = {
        "name": body.name.strip(),
        "owner_id": str(user_id),
        "members": {},
        "member_emails": []
    }
    store.save(new_company)
    return {"ok": True, "company": new_company}


class InviteMemberBody(BaseModel):
    email: EmailStr
    report_ids: list[str] # ["all"] or specific IDs


def _send_invite_email(config: Settings, company_name: str, target_email: str):
    """Send an invitation email to the user."""
    url = "https://app.hunterviz.com"
    text = f"""
    You've been invited to view reports for {company_name} on HunterViz.
    
    Click the button below to access your dashboard:
    {url}
    
    If you don't have an account yet, please sign up with this email address.
    """
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #0f172a;">You've been invited!</h2>
        <p style="color: #475569; font-size: 16px; line-height: 1.5;">
            You've been invited to view reports for <strong>{company_name}</strong> on HunterViz.
        </p>
        <div style="margin: 30px 0;">
            <a href="{url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                Go to Dashboard
            </a>
        </div>
        <p style="color: #94a3b8; font-size: 14px;">
            If the button doesn't work, copy and paste this link into your browser: <br>
            <a href="{url}" style="color: #2563eb;">{url}</a>
        </p>
    </div>
    """
    
    if config.smtp_host and config.smtp_user and config.smtp_password:
        from_addr = config.smtp_from or config.smtp_user
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Invitation to view {company_name} reports"
        msg["From"] = from_addr
        msg["To"] = target_email
        
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(config.smtp_user, config.smtp_password)
            smtp.sendmail(from_addr, [target_email], msg.as_string())


@router.get("/companies/{company_id}/members")
async def list_company_members(
    company_id: str,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    store = FirestoreCompanyStore()
    company = store.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if company.get("owner_id") != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
        
    return {"members": company.get("members") or {}}


@router.post("/companies/{company_id}/invite")
async def invite_company_member(
    company_id: str,
    body: InviteMemberBody,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    company_store = FirestoreCompanyStore()
    user_store = FirestoreUserStore()
    
    company = company_store.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if company.get("owner_id") != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
    
    members = company.get("members") or {}
    is_new = body.email not in members
    members[body.email] = {"report_ids": body.report_ids}
    company["members"] = members
    company_store.save(company)
    
    # Underlying Looker Studio sharing
    owner_doc = user_store.get_by_id(user_id)
    dashboards = owner_doc.get("dashboards") or []
    
    for d in dashboards:
        if "all" in body.report_ids or d.get("id") in body.report_ids:
            link = d.get("link")
            if link and ("lookerstudio.google.com" in link or "datastudio.google.com" in link):
                file_id = extract_file_id(link)
                if file_id:
                    share_report(file_id, body.email)
    
    # Send email
    try:
        _send_invite_email(config, company.get("name", "HunterViz"), body.email)
    except Exception as e:
        print(f"Failed to send invite email: {e}")
        
    return {"ok": True, "message": "User invited successfully"}


@router.delete("/companies/{company_id}/members/{email}")
async def remove_company_member(
    company_id: str,
    email: str,
    user_id: UserId = Depends(get_current_user_id),
):
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    store = FirestoreCompanyStore()
    company = store.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if company.get("owner_id") != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
        
    members = company.get("members") or {}
    if email in members:
        del members[email]
        company["members"] = members
        store.save(company)
        
    return {"ok": True}


@router.post("/share-dashboard")
async def share_dashboard(
    body: ShareDashboardBody,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    store = FirestoreUserStore()
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    dashboards = user.get("dashboards") or []
    target_dash = next((d for d in dashboards if d.get("id") == body.dashboard_id), None)
    
    if not target_dash:
        raise HTTPException(status_code=404, detail="Dashboard not found in your account")
        
    link = target_dash.get("link")
    if not link or ("lookerstudio.google.com" not in link and "datastudio.google.com" not in link):
        raise HTTPException(status_code=400, detail="Only Looker Studio dashboards can be shared via this tool.")
        
    file_id = extract_file_id(link)
    if not file_id:
        raise HTTPException(status_code=400, detail="Could not identify the report ID from the dashboard link.")
        
    success, message = share_report(file_id, body.email)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"ok": True, "message": message}
