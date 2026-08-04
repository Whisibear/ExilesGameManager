from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import html

from app.services import nexus_oauth

router = APIRouter()


@router.get("/callback", response_class=HTMLResponse)
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> HTMLResponse:
    message = html.escape(await nexus_oauth.complete_callback(code, state, error))
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'><title>Exiles Game Manager</title>"
        "<style>body{font-family:Segoe UI,sans-serif;background:#0d0b12;color:#eee;display:grid;"
        "place-items:center;min-height:100vh;margin:0}.card{max-width:680px;padding:32px;border:1px solid #49385f;"
        "border-radius:14px;background:#17121f;box-shadow:0 18px 60px #0008}h1{margin-top:0}</style></head>"
        f"<body><div class='card'><h1>Exiles Game Manager</h1><p>{message}</p></div></body></html>",
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
            "X-Content-Type-Options": "nosniff",
        },
    )
