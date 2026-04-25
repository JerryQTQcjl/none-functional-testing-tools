"""Report API routes."""

from fastapi import APIRouter, HTTPException

from ..core import redis as redis_store
from ..models import ApiResponse
from ..services.report_service import get_report_summary, get_execution_timeline

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{execution_id}/summary")
async def get_report(execution_id: str):
    summary = await get_report_summary(execution_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Report not found")
    return ApiResponse(data=summary)


@router.get("/{execution_id}/timeline")
async def get_timeline(execution_id: str):
    timeline = await get_execution_timeline(execution_id)
    return ApiResponse(data=timeline)
