from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["ui"])

UI_DIR = Path(__file__).resolve().parents[2] / "ui"


@router.get("/", response_class=FileResponse)
def login_page():
    return FileResponse(UI_DIR / "login.html")


@router.get("/panel", response_class=FileResponse)
def panel_page():
    return FileResponse(UI_DIR / "panel.html")


@router.get("/ui/styles.css", response_class=FileResponse)
def ui_styles():
    return FileResponse(UI_DIR / "styles.css", media_type="text/css")


@router.get("/ui/app.js", response_class=FileResponse)
def ui_app_js():
    return FileResponse(UI_DIR / "app.js", media_type="application/javascript")

