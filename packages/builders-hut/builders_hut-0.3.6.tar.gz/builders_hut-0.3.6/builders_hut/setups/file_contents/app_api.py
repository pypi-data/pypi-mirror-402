"""app/api/*"""

from textwrap import dedent


APP_API_INIT_CONTENT = dedent("""
from app.api.common import router as common_router

__all__ = ["common_router"]
""")


APP_API_COMMON_CONTENT = dedent("""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from scalar_fastapi import Theme, get_scalar_api_reference

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@router.get("/docs", include_in_schema=False)
async def get_docs():
    '''
    Get the documentation for the API
    '''
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        dark_mode=True,
        show_developer_tools=True,
        hide_download_button=True,
        theme=Theme.PURPLE,
        hide_models=True,
    )

""")
