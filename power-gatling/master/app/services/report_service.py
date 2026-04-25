"""Report service - aggregates metrics and generates reports."""

import json
import logging
from datetime import datetime
from typing import Optional

from ..core import redis as redis_store

logger = logging.getLogger(__name__)


async def get_execution_timeline(execution_id: str) -> list[dict]:
    """Get timeline metric points for an execution."""
    key = f"loadforge:timeline:{execution_id}"
    r = await redis_store.get_redis()
    data = await r.lrange(key, 0, -1)
    points = []
    for item in data:
        try:
            points.append(json.loads(item))
        except (json.JSONDecodeError, TypeError):
            pass
    return points


async def add_timeline_point(execution_id: str, point: dict):
    """Add a metric point to the execution timeline."""
    key = f"loadforge:timeline:{execution_id}"
    r = await redis_store.get_redis()
    await r.rpush(key, json.dumps(point, ensure_ascii=False))
    await r.expire(key, 3600)  # Keep for 1 hour


async def get_report_summary(execution_id: str) -> Optional[dict]:
    """Generate a report summary for an execution."""
    execution = await redis_store.json_get(f"loadforge:executions:{execution_id}")
    if not execution:
        return None

    timeline = await get_execution_timeline(execution_id)

    summary = {
        "execution": execution,
        "timeline_points": len(timeline),
        "peak_rps": max((p.get("rps", 0) for p in timeline), default=0),
        "peak_rt": max((p.get("p99_rt", 0) for p in timeline), default=0),
        "avg_rps": sum(p.get("rps", 0) for p in timeline) / max(len(timeline), 1),
        "avg_rt": sum(p.get("mean_rt", 0) for p in timeline) / max(len(timeline), 1),
        "avg_error_rate": sum(p.get("error_rate", 0) for p in timeline) / max(len(timeline), 1),
    }

    if timeline:
        summary["rt_distribution"] = {
            "p50_avg": sum(p.get("p50_rt", 0) for p in timeline) / len(timeline),
            "p90_avg": sum(p.get("p90_rt", 0) for p in timeline) / len(timeline),
            "p99_avg": sum(p.get("p99_rt", 0) for p in timeline) / len(timeline),
        }

    return summary


async def update_execution_metrics(execution_id: str, aggregated: dict):
    """Update execution record with latest aggregated metrics."""
    execution = await redis_store.json_get(f"loadforge:executions:{execution_id}")
    if not execution:
        return

    execution["total_requests"] = aggregated.get("total_requests", 0)
    execution["total_errors"] = aggregated.get("total_errors", 0)
    execution["rps"] = round(aggregated.get("rps", 0.0), 2)
    execution["mean_rt"] = round(aggregated.get("mean_rt", 0.0), 2)
    execution["p50_rt"] = round(aggregated.get("p50_rt", 0.0), 2)
    execution["p90_rt"] = round(aggregated.get("p90_rt", 0.0), 2)
    execution["p95_rt"] = round(aggregated.get("p95_rt", 0.0), 2)
    execution["p99_rt"] = round(aggregated.get("p99_rt", 0.0), 2)
    execution["max_rt"] = round(aggregated.get("max_rt", 0.0), 2)
    execution["error_rate"] = round(aggregated.get("error_rate", 0.0), 4)

    await redis_store.json_set(f"loadforge:executions:{execution_id}", execution)

    timeline_point = {
        "timestamp": aggregated.get("timestamp", datetime.now().timestamp()),
        "rps": execution["rps"],
        "mean_rt": execution["mean_rt"],
        "p50_rt": execution["p50_rt"],
        "p90_rt": execution["p90_rt"],
        "p99_rt": execution["p99_rt"],
        "error_rate": execution["error_rate"],
        "active_users": aggregated.get("active_users", 0),
        "total_requests": execution["total_requests"],
        "total_errors": execution["total_errors"],
    }
    await add_timeline_point(execution_id, timeline_point)
