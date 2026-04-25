# LoadForge 压测平台 PoC

基于分布式 Gatling 引擎 + Redis 编排的全链路压测平台演示版。

## 快速开始

### 前置要求
- Docker Desktop / Docker Engine 20.10+
- Docker Compose v2

### 一键启动

```bash
# 默认启动 3 个 Worker
./scripts/setup.sh

# 指定 Worker 数量
./scripts/setup.sh 5
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **Web Console** | http://localhost:3000 | 压测管理界面 |
| **API Server** | http://localhost:8000 | REST API |
| **Demo Target** | http://localhost:8080 | 内置压测目标 |

## 使用流程

### 1. 创建压测场景
打开 http://localhost:3000，在「压测场景」页面点击「新建场景」：
- **目标 URL**: `http://demo-target:8080/api/products` (使用容器内地址)
- **HTTP 方法**: GET/POST
- **并发用户数**: 100-10000
- **Ramp-up**: 10s
- **持续时长**: 60s
- **Worker 数量**: 1-N (根据实际启动的 Worker 数量)

### 2. 执行压测
- 在场景卡片上点击「Run Test」，或在「压测执行」页面选择场景后点击「Start Test」
- 实时查看 RPS、响应时间、错误率等指标

### 3. 查看报告
- 在「压测执行」页面查看历史执行记录
- 查看实时图表和汇总数据

## 扩容 Worker

```bash
# 扩容到 10 个 Worker
./scripts/scale-workers.sh 10

# 或直接使用 docker compose
docker compose up -d --scale worker=10
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/scenarios | 列出所有场景 |
| POST | /api/scenarios | 创建场景 |
| GET | /api/scenarios/{id} | 获取场景详情 |
| PUT | /api/scenarios/{id} | 更新场景 |
| DELETE | /api/scenarios/{id} | 删除场景 |
| GET | /api/scenarios/{id}/code | 预览 Gatling 代码 |
| POST | /api/executions | 启动压测 |
| GET | /api/executions | 列出执行记录 |
| GET | /api/executions/{id} | 获取执行详情 |
| POST | /api/executions/{id}/stop | 停止压测 |
| WS | /api/executions/{id}/realtime | 实时指标推送 |
| GET | /api/reports/{id}/summary | 压测报告 |
| GET | /api/reports/{id}/timeline | 时间线数据 |
| GET | /api/system/status | 系统状态 |

## 架构说明

```
┌──────────────┐     ┌──────────────┐
│  Web Console │────▶│  API Server  │
│  (React)     │     │  (FastAPI)   │
└──────────────┘     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │    Redis     │
                     │  (Pub/Sub)   │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────▼───┐  ┌─────▼───┐  ┌─────▼───┐
        │ Worker1 │  │ Worker2 │  │ WorkerN │
        │ (Gatling│  │ (Gatling│  │ (Gatling│
        │  JVM)   │  │  JVM)   │  │  JVM)   │
        └─────────┘  └─────────┘  └─────────┘
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                   ┌────────────────┐
                   │  Demo Target   │
                   │  (REST API)    │
                   └────────────────┘
```

- **Master**: FastAPI 服务，提供 REST API 和 WebSocket，管理场景和执行
- **Worker**: Gatling JVM 实例，通过 Redis 接收任务，执行压测，上报指标
- **Redis**: 通信中枢，Pub/Sub 分发命令，存储场景/执行数据

## 停止服务

```bash
./scripts/stop.sh

# 完全清理（包括数据）
docker compose down -v
```
