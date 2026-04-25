# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise-grade non-functional testing tool suite comprising three platforms: Precision Testing, Chaos Testing, and Full-Chain Stress Testing. The repo currently contains product documentation and a working PoC for the stress testing platform called **LoadForge**.

## Repository Structure

- `docs/` — Product solution documents per platform (precision_testing, chaos_testing, stress_testing)
- `claudedocs/` — Technical research reports
- `power-gatling/` — LoadForge distributed load testing PoC (the only code)
- `myspec/` — Spec Coding 规范编码模板，用于基础设施与平台工程项目的结构化规范体系

## LoadForge Architecture

Distributed Gatling-based load testing platform with Master-Worker topology orchestrated via Redis Pub/Sub.

```
Frontend (React/Vite) → Master (FastAPI) → Redis (Pub/Sub + state store) → Workers (Gatling JVM)
```

### Components

| Component | Directory | Stack | Role |
|-----------|-----------|-------|------|
| Master API | `power-gatling/master/app/` | Python/FastAPI | REST API, WebSocket, orchestrates workers |
| Frontend | `power-gatling/frontend/` | React 18 + TypeScript + Vite + Ant Design + Recharts | Web console UI |
| Worker | `power-gatling/worker/` | Python agent + Gatling (Java) | Executes load tests, reports metrics |
| Demo Target | `power-gatling/demo-target/` | Python/Flask | Built-in REST API for testing (GET /api/products, POST /api/orders) |
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

**Frontend Stack**: React 18 + TypeScript + Vite + Ant Design + Recharts + Axios

### Python Development (Local)

各组件可独立运行进行本地开发：

```bash
# Master API
cd power-gatling/master
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379
uvicorn app.main:app --reload --port 8000

# Worker
cd power-gatling/worker
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379
export GATLING_HOME=/path/to/gatling
python worker_agent.py

# Demo Target
cd power-gatling/demo-target
pip install -r requirements.txt
python app.py
```

**Python Stack**: Python 3.11+, FastAPI, Uvicorn, Redis (async), Pydantic v2, Jinja2, WebSockets

### Environment Variables

Key vars (see `power-gatling/.env` and `docker-compose.yml`):
- `REDIS_URL` — Redis connection (default: `redis://redis:6379`)
- `WORKER_COUNT` — Number of worker replicas (default: 3)
- `MASTER_PORT` — Master API port (default: 8000)
- `GATLING_HOME` — Gatling install path in worker container (default: `/opt/gatling`)

## Spec Coding 规范

`myspec/` 目录包含 Spec Coding 规范编码模板，用于基础设施与平台工程项目的结构化规范体系。

**四文档流水线**：
1. GAP 差距分析 (`01_GAP_Analysis_Template.md`) — 评估现状、识别差距、论证投资价值
2. 需求规格说明 (`02_Requirements_Template.md`) — 定义功能/非功能/基础设施需求
3. FIP 功能实现计划 (`03_FIP_Template.md`) — 含架构图和实现方案的详细技术设计
4. 任务清单 (`04_Task_List_Template.md`) — 分解为含依赖和工作量估算的分阶段任务

**辅助规范文档**：
- `05_Naming_Rules_Template.md` — 资源命名规范
- `06_Failure_Patterns_Template.md` — 故障模式记录
- `07_Auto_Task_Config_Template.md` — 自动化任务配置
- `08_Infra_DevOps_Dependency_Rules_Template.md` — 基础设施依赖规则

详细使用指南参见 `myspec/references/README.md`。

## Development Notes

### Master Service Key Files

- `app/services/orchestrator.py` — 执行生命周期和多 Worker 指标聚合逻辑
- `app/services/gatling_gen.py` — 使用 Jinja2 模板生成 Gatling 仿真代码
- `app/core/worker_manager.py` — Worker 注册、任务分发、用户级并发分配

### Worker Metrics Collection

Worker 每秒解析 `simulation.log`，计算百分位数（p50/p95/p99），通过 Redis Pub/Sub 发布到 `loadforge:metrics` 频道。

### Metric Aggregation Strategy

- **响应时间**: 跨 Worker 加权平均（按请求数加权）
- **RPS/错误数**: 跨 Worker 求和
- **百分位数**: 从所有 Worker 的原始数据重新计算

## Language

All documentation and code comments are in Chinese. Maintain Chinese for docs, user-facing strings, and comments; English is fine for code identifiers.
