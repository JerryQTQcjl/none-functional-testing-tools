"""Metrics collector - parses Gatling simulation.log and reports to Redis."""

import json
import logging
import os
import time
import threading
from typing import Optional

import redis

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, redis_url: str, worker_id: str, execution_id: str):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.worker_id = worker_id
        self.execution_id = execution_id
        self.results_dir: Optional[str] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # Accumulated metrics
        self.total_requests = 0
        self.total_errors = 0
        self.all_rts: list[float] = []

    def start(self, results_dir: str):
        self.results_dir = results_dir
        self.running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.info(f"Metrics collector started, watching {results_dir}")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._publish_final()

    def _find_simulation_log(self) -> Optional[str]:
        # Search multiple potential locations for Gatling results
        search_dirs = [self.results_dir, "/app/results", "/opt/gatling/results"]
        for base_dir in search_dirs:
            if not base_dir or not os.path.isdir(base_dir):
                continue
            for root, dirs, files in os.walk(base_dir):
                if "simulation.log" in files:
                    return os.path.join(root, "simulation.log")
        return None

    def _parse_log(self, log_path: str) -> list[dict]:
        entries = []
        last_offset = getattr(self, "_last_offset", 0)

        try:
            with open(log_path, "r") as f:
                f.seek(last_offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split("\t")
                    if len(parts) < 9:
                        continue

                    record_type = parts[0]
                    if record_type == "REQUEST":
                        try:
                            start_ts = int(parts[4]) if parts[4].isdigit() else 0
                            end_ts = int(parts[5]) if parts[5].isdigit() else 0
                            response_time = end_ts - start_ts if start_ts and end_ts else 0
                            status = parts[7] if len(parts) > 7 else "OK"

                            entry = {
                                "response_time": max(0, response_time / 1_000_000),  # ns to ms
                                "status": status,
                                "timestamp": start_ts / 1_000_000_000,  # ns to s
                            }
                            entries.append(entry)
                        except (ValueError, IndexError):
                            pass

                self._last_offset = f.tell()
        except FileNotFoundError:
            pass

        return entries

    def _compute_metrics(self) -> dict:
        if not self.all_rts:
            return self._empty_metrics()

        sorted_rts = sorted(self.all_rts)
        n = len(sorted_rts)

        return {
            "worker_id": self.worker_id,
            "execution_id": self.execution_id,
            "timestamp": time.time(),
            "rps": round(n / max(time.time() - getattr(self, "_start_time", time.time()), 1), 2),
            "mean_rt": round(sum(sorted_rts) / n, 2),
            "p50_rt": round(sorted_rts[int(n * 0.50)], 2),
            "p90_rt": round(sorted_rts[int(n * 0.90)], 2),
            "p99_rt": round(sorted_rts[min(int(n * 0.99), n - 1)], 2),
            "max_rt": round(sorted_rts[-1], 2),
            "error_rate": round(self.total_errors / max(self.total_requests, 1), 4),
            "active_users": 0,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
        }

    def _empty_metrics(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "execution_id": self.execution_id,
            "timestamp": time.time(),
            "rps": 0,
            "mean_rt": 0,
            "p50_rt": 0,
            "p90_rt": 0,
            "p99_rt": 0,
            "max_rt": 0,
            "error_rate": 0,
            "active_users": 0,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
        }

    def _publish_metrics(self, metrics: dict):
        try:
            self.redis.publish("loadforge:metrics", json.dumps(metrics))
        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}")

    def _publish_final(self):
        metrics = self._compute_metrics()
        metrics["final"] = True
        self._publish_metrics(metrics)

    def _collect_loop(self):
        self._start_time = time.time()
        log_path = None

        while self.running:
            if log_path is None:
                log_path = self._find_simulation_log()

            if log_path:
                entries = self._parse_log(log_path)
                for entry in entries:
                    self.total_requests += 1
                    if entry["status"] != "OK":
                        self.total_errors += 1
                    self.all_rts.append(entry["response_time"])

            metrics = self._compute_metrics()
            self._publish_metrics(metrics)

            time.sleep(1)
