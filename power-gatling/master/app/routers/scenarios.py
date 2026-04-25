"""Scenario management API routes."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..core import redis as redis_store
from ..models import Scenario, ScenarioCreate, ScenarioUpdate, ApiResponse
from ..services.gatling_gen import generate_simulation

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
async def list_scenarios():
    scenarios = await redis_store.json_list("loadforge:scenarios:")
    return ApiResponse(data=scenarios)


@router.post("")
async def create_scenario(req: ScenarioCreate):
    scenario = Scenario(**req.model_dump())
    await redis_store.json_set(
        f"loadforge:scenarios:{scenario.id}",
        scenario.model_dump(),
    )
    return ApiResponse(data=scenario.model_dump())


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    data = await redis_store.json_get(f"loadforge:scenarios:{scenario_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ApiResponse(data=data)


@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, req: ScenarioUpdate):
    data = await redis_store.json_get(f"loadforge:scenarios:{scenario_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Scenario not found")

    update_data = req.model_dump(exclude_none=True)
    data.update(update_data)
    data["updated_at"] = datetime.now().isoformat()

    await redis_store.json_set(f"loadforge:scenarios:{scenario_id}", data)
    return ApiResponse(data=data)


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str):
    await redis_store.delete_key(f"loadforge:scenarios:{scenario_id}")
    return ApiResponse(data={"deleted": True})


@router.get("/{scenario_id}/code")
async def get_scenario_code(scenario_id: str):
    data = await redis_store.json_get(f"loadforge:scenarios:{scenario_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = Scenario(**data)
    code = generate_simulation(scenario.model_dump())
    return ApiResponse(data={"code": code, "language": "java"})
