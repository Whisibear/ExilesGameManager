import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import diagnostics, system_settings
from app.services.diagnostics import DiagnosticsError

router = APIRouter()


class SystemSettingsRequest(BaseModel):
    bootWithWindows: bool
    autoStartActiveServer: bool
    privacyMode: bool
    adminPort: int
    debugLogging: bool = False


class RunDiagnosticsRequest(BaseModel):
    forceAdmin: bool = False


@router.get("")
async def get_system_settings() -> dict[str, Any]:
    return system_settings.get_config()


@router.post("")
async def update_system_settings(body: SystemSettingsRequest) -> dict[str, Any]:
    try:
        return system_settings.update_config(
            boot_with_windows=body.bootWithWindows,
            auto_start_active_server=body.autoStartActiveServer,
            privacy_mode=body.privacyMode,
            admin_port=body.adminPort,
            debug_logging=body.debugLogging,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Couldn't update Windows startup: {e}")


@router.post("/diagnostics")
async def run_diagnostics(body: RunDiagnosticsRequest = RunDiagnosticsRequest()) -> dict[str, Any]:
    try:
        return await asyncio.to_thread(diagnostics.run, body.forceAdmin)
    except DiagnosticsError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.post("/diagnostics/package")
async def create_diagnostic_package() -> dict[str, Any]:
    try:
        return await asyncio.to_thread(diagnostics.create_package)
    except DiagnosticsError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.get("/diagnostics/package/{file_name}")
async def download_diagnostic_package(file_name: str) -> FileResponse:
    try:
        path = diagnostics.package_path(file_name)
    except DiagnosticsError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return FileResponse(path, media_type="application/zip", filename=path.name)
