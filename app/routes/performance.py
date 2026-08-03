import asyncio
from fastapi import APIRouter, HTTPException
from app.services import performance_monitor

router = APIRouter()

@router.get("/active")
async def active_performance():
    try:
        return await asyncio.to_thread(performance_monitor.active_snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/instances")
async def instance_performance():
    return {"instances": await asyncio.to_thread(performance_monitor.all_instances_snapshot)}
