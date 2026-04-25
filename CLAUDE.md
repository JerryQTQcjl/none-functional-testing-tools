# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise-grade non-functional testing tool suite comprising three platforms: Precision Testing, Chaos Testing, and Full-Chain Stress Testing. The repo currently contains product documentation and a working PoC for the stress testing platform called **LoadForge**.

## Repository Structure

- `docs/` — Product solution documents per platform (precision_testing, chaos_testing, stress_testing)
- `claudedocs/` — Technical research reports
- `power-gatling/` — LoadForge distributed load testing PoC (the only code)

## LoadForge Architecture

Distributed Gatling-based load testing platform with Master-Worker topology orchestrated via Redis Pub/Sub.

```
Frontend (React/Vite) → Master (FastAPI) → Redis (Pub/Sub + state store) → Workers (Gatling JVM)
```

### Components

| Component | Directory | Stack | Role |
|-----------|-----------|-------|------|
| Master API | `power-gatling/master/app/` | Python/FastAPI | REST API, WebSocket, orchestrates workers |
| Frontend | `power-gatling/frontend/` | React 18 + Vite + Ant Design + Recharts | Web console UI |
| Worker | `power-gatling/worker/` | Python agent + Gatling (Java) | Executes load tests, reports metrics |
| Demo Target | `power-gatling/demo-target/` | Python/Flask | Built-in REST API for testing |
| Config | `power-gatling/config/` | Nginx configs, sample scenarios | Supporting files |

### Data Flow

1. User creates a **Scenario** (target URL, concurrency, duration) via Master API
2. User triggers execution → Master generates Gatling simulation code from Jinja2 template, stores task config in Redis, publishes `start_test` command on `loadforge:control` channel
3. Workers subscribe to `loadforge:control`, pick up task, generate Java simulation file, launch Gatling subprocess
4. `MetricsCollector` on each worker parses `simulation.log` every second, publishes aggregated metrics to `loadforge:metrics` Redis channel
5. Master's `orchestrator.py` listens on `loadforge:metrics`, aggregates across workers (weighted mean for response times, sum for RPS/errors), updates execution record in Redis
6. Frontend polls API or uses WebSocket (`/api/executions/{id}/realtime`) for live metrics

### Redis Key Schema

- `loadforge:scenarios:{id}` — Scenario definitions
- `loadforge:executions:{id}` — Execution state and aggregated metrics
- `loadforge:workers:{worker_id}` — Worker registration + heartbeat
- `loadforge:task:{execution_id}` — Task config distributed to workers
- `loadforge:simulation:{execution_id}` — Generated Gatling code
- `loadforge:metrics` — Pub/Sub channel for real-time worker metrics
- `loadforge:control` — Pub/Sub channel for start/stop commands

### Master API Structure (`power-gatling/master/app/`)

- `main.py` — FastAPI app, CORS, lifespan, static file serving
- `config.py` — Settings from env vars (REDIS_URL, WORKER_COUNT, paths)
- `models.py` — Pydantic models: Scenario, Execution, MetricPoint, WorkerInfo
- `routers/` — scenarios, executions, reports, system
- `services/orchestrator.py` — Execution lifecycle and multi-worker metric aggregation
- `services/gatling_gen.py` — Gatling simulation code generation
- `services/report_service.py` — Execution metrics persistence
- `core/redis.py` — Async Redis wrapper (json_get/set, pubsub)
- `core/worker_manager.py` — Worker registration, task distribution, user-per-worker splitting

### Worker Structure (`power-gatling/worker/`)

- `worker_agent.py` — Main loop: Redis connection, heartbeat, command listener, Gatling process management
- `simulation_builder.py` — Generates Java simulation from Jinja2 template
- `metrics_collector.py` — Parses Gatling `simulation.log`, computes percentiles, publishes to Redis
- `templates/simulation.java.j2` — Gatling simulation Java template

## Commands

### Full Stack (Docker Compose)

```bash
cd power-gatling

# Start (default 3 workers)
./scripts/setup.sh

# Start with N workers
./scripts/setup.sh 5

# Scale workers
./scripts/scale-workers.sh 10

# Stop
./scripts/stop.sh

# Full cleanup including data
docker compose down -v
```

### Frontend Development

```bash
cd power-gatling/frontend
npm install
npm run dev       # Vite dev server
npm run build     # tsc + vite build
```

### Environment Variables

Key vars (see `power-gatling/.env` and `docker-compose.yml`):
- `REDIS_URL` — Redis connection (default: `redis://redis:6379`)
- `WORKER_COUNT` — Number of worker replicas (default: 3)
- `MASTER_PORT` — Master API port (default: 8000)
- `GATLING_HOME` — Gatling install path in worker container (default: `/opt/gatling`)

## Language

All documentation and code comments are in Chinese. Maintain Chinese for docs, user-facing strings, and comments; English is fine for code identifiers.
