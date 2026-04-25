from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    name: str
    description: str = ""
    target_url: str
    method: str = "GET"
    headers: dict = Field(default_factory=dict)
    body: Optional[str] = None
    concurrent_users: int = 100
    ramp_up_duration: int = 10
    sustained_duration: int = 60
    workers: int = 1
    tags: list[str] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[str] = None
    concurrent_users: Optional[int] = None
    ramp_up_duration: Optional[int] = None
    sustained_duration: Optional[int] = None
    workers: Optional[int] = None
    tags: Optional[list[str]] = None


class Scenario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    target_url: str
    method: str = "GET"
    headers: dict = Field(default_factory=dict)
    body: Optional[str] = None
    concurrent_users: int = 100
    ramp_up_duration: int = 10
    sustained_duration: int = 60
    workers: int = 1
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ExecutionCreate(BaseModel):
    scenario_id: str


class Execution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    status: str = "pending"  # pending/running/completed/failed/stopped
    workers: int = 1
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    total_requests: int = 0
    total_errors: int = 0
    mean_rt: float = 0.0
    p50_rt: float = 0.0
    p90_rt: float = 0.0
    p95_rt: float = 0.0
    p99_rt: float = 0.0
    max_rt: float = 0.0
    rps: float = 0.0
    error_rate: float = 0.0


class MetricPoint(BaseModel):
    timestamp: float
    rps: float = 0.0
    mean_rt: float = 0.0
    p50_rt: float = 0.0
    p90_rt: float = 0.0
    p99_rt: float = 0.0
    error_rate: float = 0.0
    active_users: int = 0
    total_requests: int = 0
    total_errors: int = 0


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[dict | list] = None


class WorkerInfo(BaseModel):
    worker_id: str
    status: str = "idle"
    execution_id: Optional[str] = None
    started_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
