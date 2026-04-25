"""Orchestrator service - manages test execution lifecycle and metrics aggregation."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from ..core import redis as redis_store
from ..core import worker_manager
from ..services.gatling_gen import generate_simulation
from ..services.report_service import update_execution_metrics

logger = logging.getLogger(__name__)

# Active metric listener tasks
_metric_listeners: dict[str, asyncio.Task] = {}


async def start_execution(execution_id: str, scenario: dict) -> dict:
    """Start a distributed test execution."""
    num_workers = scenario.get("workers", 1)

    # Generate Gatling simulation code
    sim_code = generate_simulation(scenario)

    # Store the generated code
    await redis_store.json_set(
        f"loadforge:simulation:{execution_id}",
        {"code": sim_code, "scenario_id": scenario["id"]},
    )

    # Create execution record
    execution = {
        "id": execution_id,
        "scenario_id": scenario["id"],
        "scenario_name": scenario.get("name", ""),
        "status": "running",
        "workers": num_workers,
        "started_at": datetime.now().isoformat(),
        "ended_at": None,
        "total_requests": 0,
        "total_errors": 0,
        "mean_rt": 0.0,
        "p50_rt": 0.0,
        "p90_rt": 0.0,
        "p95_rt": 0.0,
        "p99_rt": 0.0,
        "max_rt": 0.0,
        "rps": 0.0,
        "error_rate": 0.0,
    }
    await redis_store.json_set(f"loadforge:executions:{execution_id}", execution)

    # Distribute task to workers
    await worker_manager.distribute_task(execution_id, scenario, num_workers)

    # Start metric listener
    task = asyncio.create_task(_listen_metrics(execution_id))
    _metric_listeners[execution_id] = task

    return execution


async def stop_execution(execution_id: str) -> Optional[dict]:
    """Stop a running execution."""
    execution = await redis_store.json_get(f"loadforge:executions:{execution_id}")
    if not execution:
        return None

    execution["status"] = "stopped"
    execution["ended_at"] = datetime.now().isoformat()
    await redis_store.json_set(f"loadforge:executions:{execution_id}", execution)

    await worker_manager.stop_task(execution_id)

    if execution_id in _metric_listeners:
        _metric_listeners[execution_id].cancel()
        del _metric_listeners[execution_id]

    return execution


async def complete_execution(execution_id: str, status: str = "completed"):
    """Mark an execution as completed."""
    execution = await redis_store.json_get(f"loadforge:executions:{execution_id}")
    if not execution:
        return

    execution["status"] = status
    execution["ended_at"] = datetime.now().isoformat()
    await redis_store.json_set(f"loadforge:executions:{execution_id}", execution)

    if execution_id in _metric_listeners:
        _metric_listeners[execution_id].cancel()
        del _metric_listeners[execution_id]


async def _listen_metrics(execution_id: str):
    """Listen for metrics from workers and aggregate them."""
    try:
        pubsub = await redis_store.get_pubsub()
        await pubsub.subscribe("loadforge:metrics")

        worker_metrics: dict[str, dict] = {}

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                continue

            if data.get("execution_id") != execution_id:
                continue

            worker_id = data.get("worker_id", "unknown")
            worker_metrics[worker_id] = data

            # Aggregate all worker metrics
            aggregated = _aggregate_metrics(list(worker_metrics.values()))
            aggregated["timestamp"] = data.get("timestamp", datetime.now().timestamp())

            await update_execution_metrics(execution_id, aggregated)

    except asyncio.CancelledError:
        logger.info(f"Metrics listener cancelled for {execution_id}")
    except Exception as e:
        logger.error(f"Metrics listener error for {execution_id}: {e}")
        await complete_execution(execution_id, "failed")


def _aggregate_metrics(metrics_list: list[dict]) -> dict:
    """Aggregate metrics from multiple workers."""
    if not metrics_list:
        return {
            "rps": 0, "mean_rt": 0, "p50_rt": 0, "p90_rt": 0,
            "p99_rt": 0, "max_rt": 0, "error_rate": 0,
            "active_users": 0, "total_requests": 0, "total_errors": 0,
        }

    n = len(metrics_list)
    total_requests = sum(m.get("total_requests", 0) for m in metrics_list)
    total_errors = sum(m.get("total_errors", 0) for m in metrics_list)

    # Weighted mean for response times based on request counts
    total_weight = max(total_requests, 1)

    return {
        "rps": sum(m.get("rps", 0) for m in metrics_list),
        "mean_rt": sum(m.get("mean_rt", 0) * m.get("total_requests", 0) for m in metrics_list) / total_weight,
        "p50_rt": sum(m.get("p50_rt", 0) for m in metrics_list) / n,
        "p90_rt": sum(m.get("p90_rt", 0) for m in metrics_list) / n,
        "p99_rt": sum(m.get("p99_rt", 0) for m in metrics_list) / n,
        "max_rt": max(m.get("max_rt", 0) for m in metrics_list),
        "error_rate": total_errors / max(total_requests, 1),
        "active_users": sum(m.get("active_users", 0) for m in metrics_list),
        "total_requests": total_requests,
        "total_errors": total_errors,
    }
