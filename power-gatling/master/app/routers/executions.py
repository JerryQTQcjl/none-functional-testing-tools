"""Execution management API routes."""

import json
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..core import redis as redis_store
from ..models import ExecutionCreate, ApiResponse
from ..services import orchestrator
from ..services.report_service import get_execution_timeline

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.post("")
async def start_execution(req: ExecutionCreate):
    scenario = await redis_store.json_get(f"loadforge:scenarios:{req.scenario_id}")
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    execution_id = str(uuid.uuid4())
    execution = await orchestrator.start_execution(execution_id, scenario)
    return ApiResponse(data=execution)


@router.get("")
async def list_executions():
    executions = await redis_store.json_list("loadforge:executions:")
    return ApiResponse(data=executions)


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    data = await redis_store.json_get(f"loadforge:executions:{execution_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ApiResponse(data=data)


@router.post("/{execution_id}/stop")
async def stop_execution(execution_id: str):
    execution = await orchestrator.stop_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ApiResponse(data=execution)


@router.websocket("/{execution_id}/realtime")
async def realtime_metrics(websocket: WebSocket, execution_id: str):
    await websocket.accept()

    pubsub = await redis_store.get_pubsub()
    await pubsub.subscribe("loadforge:metrics")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                continue

            if data.get("execution_id") != execution_id:
                continue

            await websocket.send_json(data)

            execution = await redis_store.json_get(f"loadforge:executions:{execution_id}")
            if execution and execution.get("status") in ("completed", "failed", "stopped"):
                await websocket.send_json({"event": "execution_end", "status": execution["status"]})
                break

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("loadforge:metrics")
