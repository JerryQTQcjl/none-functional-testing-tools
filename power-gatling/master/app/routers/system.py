"""System status API routes."""

from fastapi import APIRouter

from ..core import redis as redis_store
from ..core.worker_manager import get_all_workers, get_active_worker_count
from ..models import ApiResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status():
    redis_connected = False
    try:
        r = await redis_store.get_redis()
        await r.ping()
        redis_connected = True
    except Exception:
        pass

    workers = await get_all_workers()
    active_count = await get_active_worker_count()

    executions = await redis_store.json_list("loadforge:executions:")
    active_executions = [e for e in executions if e.get("status") == "running"]

    return ApiResponse(data={
        "redis_connected": redis_connected,
        "active_workers": active_count,
        "registered_workers": len(workers),
        "active_executions": len(active_executions),
        "workers": workers,
    })


@router.get("/workers")
async def list_workers():
    workers = await get_all_workers()
    return ApiResponse(data=workers)
