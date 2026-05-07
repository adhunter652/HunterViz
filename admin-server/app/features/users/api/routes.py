"""User management pages and API. No app-level auth; IAP handles access."""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import AdminSettings, get_settings
from app.core.infrastructure.templating import render_template
from app.features.users.firestore_store import FirestoreUserStore
from app.core.infrastructure.google_drive import share_report, extract_file_id

router = APIRouter(prefix="/users", tags=["users"])


def get_user_store() -> FirestoreUserStore:
    return FirestoreUserStore()


# --- Pages ---


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def list_users_page(
    request: Request,
    store: FirestoreUserStore = Depends(get_user_store),
    settings: AdminSettings = Depends(get_settings),
):
    users = store.list_users()
    return HTMLResponse(
        render_template(
            "list_users",
            {"app_name": settings.app_name, "users": users},
        )
    )


@router.get("/{user_id}", response_class=HTMLResponse)
def edit_user_page(
    request: Request,
    user_id: str,
    store: FirestoreUserStore = Depends(get_user_store),
    settings: AdminSettings = Depends(get_settings),
):
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    dashboards = user.get("dashboards") or []
    
    return HTMLResponse(
        render_template(
            "edit_user",
            {
                "app_name": settings.app_name,
                "user": safe_user,
                "dashboards": dashboards,
            },
        )
    )


# --- Update user (form post) ---


@router.post("/{user_id}")
def update_user(
    user_id: str,
    email: str = Form(..., alias="email"),
    company_name: str = Form("", alias="company_name"),
    store: FirestoreUserStore = Depends(get_user_store),
):
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["email"] = email.strip()
    user["company_name"] = (company_name or "").strip()
    store.save(user)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


# --- Dashboards: add/remove (form POST from edit page) ---


@router.post("/{user_id}/dashboards")
def add_dashboard(
    user_id: str,
    id: str = Form("", alias="dashboard_id"),
    link: str = Form("", alias="dashboard_link"),
    refresh_url: str = Form("", alias="refresh_url"),
    store: FirestoreUserStore = Depends(get_user_store),
):
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    dashboards = list(user.get("dashboards") or [])
    dash_id = (id or "").strip() or f"dash-{len(dashboards) + 1}"
    dashboards.append({
        "id": dash_id, 
        "link": (link or "").strip(),
        "refresh_url": (refresh_url or "").strip()
    })
    user["dashboards"] = dashboards
    store.save(user)

    # Automatic sharing for Looker Studio
    if link and ("lookerstudio.google.com" in link or "datastudio.google.com" in link):
        file_id = extract_file_id(link)
        if file_id and user.get("email"):
            share_report(file_id, user["email"])

    return RedirectResponse(url=f"/users/{user_id}#dashboards", status_code=303)


@router.post("/{user_id}/dashboards/remove")
def remove_dashboard(
    user_id: str,
    dashboard_index: int = Form(..., alias="dashboard_index"),
    store: FirestoreUserStore = Depends(get_user_store),
):
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    dashboards = list(user.get("dashboards") or [])
    if 0 <= dashboard_index < len(dashboards):
        dashboards.pop(dashboard_index)
    user["dashboards"] = dashboards
    store.save(user)
    return RedirectResponse(url=f"/users/{user_id}#dashboards", status_code=303)
