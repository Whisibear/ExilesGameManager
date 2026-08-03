
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.auth_deps import require_super_admin
from app.services import app_update
router=APIRouter()
@router.get("")
async def get_update_status(force: bool=False)->dict[str,Any]: return await app_update.get_status(force=force)
@router.post("/install",dependencies=[Depends(require_super_admin)])
async def install_update()->dict[str,Any]:
    try: return await app_update.install_update()
    except RuntimeError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
