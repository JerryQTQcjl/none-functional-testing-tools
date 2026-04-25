"""LoadForge Worker Agent - connects to Redis, receives tasks, runs Gatling simulations."""

import json
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from typing import Optional

import redis

from simulation_builder import SimulationBuilder
from metrics_collector import MetricsCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
WORKER_ID = os.getenv("WORKER_ID", f"worker-{socket.gethostname()}-{uuid.uuid4().hex[:8]}")
GATLING_HOME = os.getenv("GATLING_HOME", "/opt/gatling")
RESULTS_DIR = os.getenv("RESULTS_DIR", "/app/results")
SIMULATIONS_DIR = os.path.join(GATLING_HOME, "user-files", "simulations")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

r: Optional[redis.Redis] = None
current_process: Optional[subprocess.Popen] = None
metrics_collector: Optional[MetricsCollector] = None
running = True


def connect_redis() -> redis.Redis:
    global r
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    logger.info(f"Connected to Redis at {REDIS_URL}")
    return r


WORKER_KEY = f"loadforge:workers:{WORKER_ID}"


def register_worker():
    info = {
        "worker_id": WORKER_ID,
        "status": "idle",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_heartbeat": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hostname": socket.gethostname(),
    }
    r.set(WORKER_KEY, json.dumps(info))
    logger.info(f"Registered worker: {WORKER_ID}")


def deregister_worker():
    try:
        r.delete(WORKER_KEY)
        logger.info(f"Deregistered worker: {WORKER_ID}")
    except Exception:
        pass


def update_heartbeat():
    while running:
        try:
            info_raw = r.get(WORKER_KEY)
            if info_raw:
                info = json.loads(info_raw)
            else:
                info = {"worker_id": WORKER_ID, "status": "idle"}
            info["last_heartbeat"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            r.set(WORKER_KEY, json.dumps(info))
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
        time.sleep(5)


def update_status(status: str, execution_id: str = ""):
    try:
        info_raw = r.get(WORKER_KEY)
        if info_raw:
            info = json.loads(info_raw)
        else:
            info = {"worker_id": WORKER_ID}
        info["status"] = status
        info["execution_id"] = execution_id
        info["last_heartbeat"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        r.set(WORKER_KEY, json.dumps(info))
    except Exception as e:
        logger.error(f"Status update failed: {e}")


def run_gatling(simulation_class: str, execution_id: str) -> subprocess.Popen:
    results_subdir = os.path.join(RESULTS_DIR, execution_id)
    os.makedirs(results_subdir, exist_ok=True)

    cmd = [
        os.path.join(GATLING_HOME, "bin", "gatling.sh"),
        "--run-mode", "local",
        "--simulation", simulation_class,
    ]

    env = os.environ.copy()
    env["GATLING_HOME"] = GATLING_HOME

    logger.info(f"Starting Gatling: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=None,
        stderr=None,
        env=env,
        cwd=GATLING_HOME,
    )
    # Gatling 3.10 bundle asks to select simulation interactively
    # Send "1" to select our simulation, then empty line for description
    try:
        proc.stdin.write(b"1\n\n")
        proc.stdin.flush()
    except Exception:
        pass
    return proc


def handle_start_test(config: dict):
    global current_process, metrics_collector

    execution_id = config.get("execution_id", str(uuid.uuid4()))
    logger.info(f"Starting test for execution: {execution_id}")

    # Build simulation Java file
    builder = SimulationBuilder(TEMPLATE_DIR)
    class_name = f"Sim_{execution_id.replace('-', '_')}"
    sim_path = os.path.join(SIMULATIONS_DIR, f"{class_name}.java")

    config["execution_id"] = execution_id
    builder.build(config, sim_path)
    logger.info(f"Generated simulation: {sim_path}")

    # Start Gatling
    update_status("running", execution_id)
    proc = run_gatling(f"loadforge.{class_name}", execution_id)
    current_process = proc

    # Start metrics collector
    results_subdir = os.path.join(RESULTS_DIR, execution_id)
    metrics_collector = MetricsCollector(REDIS_URL, WORKER_ID, execution_id)
    metrics_collector.start(results_subdir)

    # Monitor process in a thread
    def monitor():
        proc.wait()
        logger.info(f"Gatling process exited with code: {proc.returncode}")
        if metrics_collector:
            metrics_collector.stop()
        update_status("idle")
        current_process = None

    t = threading.Thread(target=monitor, daemon=True)
    t.start()


def handle_stop_test(execution_id: str):
    global current_process, metrics_collector

    logger.info(f"Stopping test: {execution_id}")

    if current_process:
        current_process.terminate()
        try:
            current_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            current_process.kill()
        current_process = None

    if metrics_collector:
        metrics_collector.stop()
        metrics_collector = None

    update_status("idle")


def listen_for_commands():
    pubsub = r.pubsub()
    pubsub.subscribe("loadforge:control")
    logger.info("Listening for commands on loadforge:control...")

    for message in pubsub.listen():
        if not running:
            break

        if message["type"] != "message":
            continue

        try:
            data = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError):
            continue

        action = data.get("action")

        if action == "start_test":
            task_key = data.get("task_key")
            if task_key:
                task_json = r.get(task_key)
                if task_json:
                    config = json.loads(task_json)
                    handle_start_test(config)
                else:
                    logger.error(f"Task not found: {task_key}")
            else:
                logger.error("No task_key in start_test command")

        elif action == "stop_test":
            execution_id = data.get("execution_id")
            if execution_id:
                handle_stop_test(execution_id)

        else:
            logger.warning(f"Unknown action: {action}")


def signal_handler(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False
    if current_process:
        current_process.terminate()
    if metrics_collector:
        metrics_collector.stop()
    deregister_worker()
    sys.exit(0)


def main():
    global running

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"LoadForge Worker starting: {WORKER_ID}")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"Gatling Home: {GATLING_HOME}")

    connect_redis()

    os.makedirs(SIMULATIONS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    register_worker()

    heartbeat_thread = threading.Thread(target=update_heartbeat, daemon=True)
    heartbeat_thread.start()

    try:
        listen_for_commands()
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        deregister_worker()


if __name__ == "__main__":
    main()
