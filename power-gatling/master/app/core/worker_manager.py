import json
import logging
from datetime import datetime
from typing import Optional

from . import redis as redis_store

logger = logging.getLogger(__name__)


async def register_worker(worker_id: str, info: dict):
    info["last_heartbeat"] = datetime.now().isoformat()
    await redis_store.json_set(f"loadforge:workers:{worker_id}", info)


async def deregister_worker(worker_id: str):
    await redis_store.delete_key(f"loadforge:workers:{worker_id}")


async def get_all_workers() -> list[dict]:
    r = await redis_store.get_redis()
    workers = []
    async for key in r.scan_iter(match="loadforge:workers:*"):
        data = await redis_store.json_get(key)
        if data:
            workers.append(data)
    return workers


async def get_active_worker_count() -> int:
    workers = await get_all_workers()
    count = 0
    for w in workers:
        hb = w.get("last_heartbeat", "")
        if hb:
            try:
                hb_time = datetime.fromisoformat(hb)
                diff = (datetime.now() - hb_time).total_seconds()
                if diff < 30:
                    count += 1
            except (ValueError, TypeError):
                pass
    return count


async def distribute_task(execution_id: str, scenario: dict, num_workers: int):
    """Distribute a test task to workers via Redis."""
    users_per_worker = max(1, scenario["concurrent_users"] // num_workers)

    task_config = {
        "execution_id": execution_id,
        "scenario_id": scenario["id"],
        "target_url": scenario["target_url"],
        "method": scenario.get("method", "GET"),
        "headers": scenario.get("headers", {}),
        "body": scenario.get("body"),
        "concurrent_users": users_per_worker,
        "ramp_up_duration": scenario.get("ramp_up_duration", 10),
        "sustained_duration": scenario.get("sustained_duration", 60),
        "expected_status": 200,
        "num_workers": num_workers,
        "total_users": scenario["concurrent_users"],
    }

    await redis_store.json_set(f"loadforge:task:{execution_id}", task_config)

    command = {
        "action": "start_test",
        "execution_id": execution_id,
        "task_key": f"loadforge:task:{execution_id}",
    }
    await redis_store.publish("loadforge:control", command)
    logger.info(f"Distributed task {execution_id} to {num_workers} workers")


async def stop_task(execution_id: str):
    """Send stop command to workers for an execution."""
    command = {
        "action": "stop_test",
        "execution_id": execution_id,
    }
    await redis_store.publish("loadforge:control", command)
    logger.info(f"Sent stop command for execution {execution_id}")
