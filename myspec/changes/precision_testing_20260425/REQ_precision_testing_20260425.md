# 需求规格说明 - PrecisionQA 精准测试平台

**文档编号**: REQ_PrecisionQA_Platform

**创建日期**: 2026-04-25

**状态**: 需求定义

---

## 执行摘要

### 问题描述

**当前状态**:
- 每次代码变更后执行全量测试，CI 流水线耗时 2-4 小时
- 无法评估代码变更的真实影响范围
- 缺乏代码与测试用例的双向追溯关系
- 只关注单元测试覆盖率，集成/E2E/手动测试覆盖情况未知
- 测试范围选择依赖人工经验

**目标状态**:
- 自动分析影响范围，精准推荐测试用例，回归测试量降低 60-90%
- CI 反馈周期从小时级缩短到分钟级
- 测试用例与代码行精确映射，双向追溯
- 跨单元/集成/E2E/手动测试的全维度覆盖率聚合
- 量化指标驱动测试策略

### 解决方案概述

1. **代码插桩引擎** - JaCoCo（Java）+ Istanbul（JS/TS）覆盖率采集
2. **依赖图构建引擎** - 静态 AST + 运行时调用链，Neo4j 图存储
3. **影响分析引擎** - 图遍历 + 风险评分
4. **智能推荐引擎** - 规则引擎 + XGBoost ML 模型
5. **CI/CD 集成** - Jenkins/GitLab CI/GitHub Actions 质量门禁
6. **Web Console** - React + TypeScript 可视化界面

### 架构决策

#### 方案 B: 自主研发 ✅ **已选择**

**选择理由**:
- ✅ 数据安全可控，满足合规要求
- ✅ 可与混沌测试、压测平台深度协同
- ✅ 支持私有化部署
- ✅ 形成核心资产

### 目标

| 目标编号 | 描述 | 优先级 |
|---------|------|--------|
| GOAL-001 | Java + JS/TS 代码覆盖率自动化采集 | 🔴 严重 |
| GOAL-002 | 代码依赖图构建并存储到 Neo4j | 🔴 严重 |
| GOAL-003 | 基于 Git diff 的影响分析 | 🔴 严重 |
| GOAL-004 | 规则引擎驱动的测试用例推荐 | 🔴 严重 |
| GOAL-005 | Jenkins/GitLab CI 质量门禁 | 🔴 严重 |
| GOAL-006 | Web Console 管理界面 | 🟡 高 |
| GOAL-007 | ML 模型增强推荐准确率 | 🟡 高 |
| GOAL-008 | 跨测试类型覆盖率聚合 | 🟡 高 |
| GOAL-009 | 覆盖率趋势分析和质量画像 | 🟢 中 |
| GOAL-010 | GitHub Actions 集成 | 🟢 中 |
| GOAL-011 | 测试用例与代码双向追溯 | 🟢 中 |
| GOAL-012 | 运维监控和告警 | 🟢 中 |

### 成功标准

| 指标 | 当前 | 目标 | 衡量方式 |
|------|------|------|---------|
| 回归测试时间 | 2-4h | 15-30min | CI 时长统计 |
| 推荐召回率 | N/A | > 80% | 人工抽检 |
| 覆盖率采集成功率 | 0% | > 95% | 任务成功率 |
| 影响 API P99 | N/A | < 5s | 性能监控 |
| 服务可用性 | N/A | > 99% | 月度统计 |

---

## 第 1 节：功能需求

### 1.1 代码插桩引擎

#### FR-1.1.1: Java 代码覆盖率采集

[基于 JaCoCo Agent 的 Java 代码覆盖率自动采集，支持行覆盖、分支覆盖和方法覆盖。]

**验收标准**:
- [ ] 支持 Java 8+，Maven 和 Gradle
- [ ] 采集成功率 > 95%
- [ ] 采集开销 < 10%

**配置**:

```yaml
java_collector:
  agent: "jacoco"
  agent_options:
    output: "file"
    destfile: "/tmp/jacoco.exec"
    excludes: ["*.test.*", "*Test*"]
  reporting:
    endpoint: "/api/v1/coverage/java/upload"
    format: "jacoco_xml"
    compression: true
```

#### FR-1.1.2: JS/TS 代码覆盖率采集

[基于 Istanbul/nyc 的 JS/TS 覆盖率采集，集成 Jest/Mocha/Karma。]

**验收标准**:
- [ ] 支持 JS ES5+ 和 TypeScript
- [ ] 集成 Jest、Mocha、Karma
- [ ] 采集成功率 > 95%
- [ ] 支持 Source Map 还原
- [ ] 采集开销 < 15%

**配置**:

```yaml
js_collector:
  tool: "nyc"
  frameworks: ["jest", "mocha", "karma"]
  coverage_types: ["lines", "branches", "functions", "statements"]
  reporting:
    endpoint: "/api/v1/coverage/js/upload"
    format: "istanbul_json"
    source_map: true
```

### 1.2 依赖图构建引擎

#### FR-1.2.1: 静态依赖关系提取

[通过 Tree-sitter AST 解析 import/module/require 语句，提取静态依赖关系。]

**验收标准**:
- [ ] 支持 Java、JS、TS
- [ ] 依赖提取准确率 > 90%
- [ ] 支持增量更新（仅分析变更文件）

**图数据模型**:

```yaml
graph:
  nodes: ["project", "module", "package", "class", "method", "file"]
  edges:
    - { type: "DEPENDS_ON", weight: 0.8 }
    - { type: "CALLS", weight: 1.0 }
    - { type: "IMPLEMENTS", weight: 0.6 }
    - { type: "EXTENDS", weight: 0.4 }

  neo4j:
    uri: "bolt://neo4j:7687"
    database: "precisionqa"
```

#### FR-1.2.2: 运行时调用链采集

[Java Agent + JS Profiler 采集运行时方法调用关系。]

**验收标准**:
- [ ] 采集开销 < 20%
- [ ] 支持采样配置
- [ ] 调用链数据与静态图融合

### 1.3 影响分析引擎

#### FR-1.3.1: Git diff 解析

[解析 Git 提交/PR 变更，识别变更文件、类、方法。]

**验收标准**:
- [ ] 支持分支对比、PR 对比、单次提交对比
- [ ] 文件过滤（仅分析源码文件）

#### FR-1.3.2: 图遍历与影响范围计算

[在依赖图中进行图遍历，计算变更影响范围。]

**验收标准**:
- [ ] 支持正向（下游）和反向（上游）遍历
- [ ] 遍历深度限制
- [ ] 影响计算耗时 < 5s（万级变更）

**配置**:

```yaml
graph_traversal:
  upstream:
    direction: "INCOMING"
    edge_types: ["CALLS", "DEPENDS_ON"]
    max_depth: 3
  downstream:
    direction: "OUTGOING"
    edge_types: ["DEPENDS_ON", "IMPLEMENTS"]
    max_depth: 2
```

#### FR-1.3.3: 风险评分

[综合代码复杂度、缺陷密度、变更规模计算风险评分。]

**验收标准**:
- [ ] 评分范围 0-100
- [ ] 风险等级：低（0-30）/ 中（31-70）/ 高（71-100）

**配置**:

```yaml
risk_scoring:
  factors:
    complexity: { weight: 0.3 }
    defect_density: { weight: 0.4, lookback_days: 90 }
    change_size: { weight: 0.2 }
    churn_rate: { weight: 0.1, lookback_commits: 10 }
  levels:
    low: { range: [0, 30], action: "auto_approve" }
    medium: { range: [31, 70], action: "manual_review" }
    high: { range: [71, 100], action: "require_approval" }
```

### 1.4 智能推荐引擎

#### FR-1.4.1: 规则引擎

[基于依赖图和影响范围的精确匹配推荐测试用例。]

**验收标准**:
- [ ] 推荐召回率 > 80%
- [ ] 推荐响应 < 3s
- [ ] 支持手动调整

**规则**:

```yaml
rules:
  - { name: "direct_coverage", priority: 1, condition: "coverage intersects changed_files" }
  - { name: "dependency_coverage", priority: 2, condition: "coverage intersects impacted_modules" }
  - { name: "risk_based", priority: 3, condition: "risk_score > threshold" }
  - { name: "regression_prone", priority: 4, condition: "file has recent_defects" }
```

#### FR-1.4.2: ML 推荐模型

[XGBoost 模型预测最可能发现缺陷的测试用例。]

**验收标准**:
- [ ] 准确率 > 70%（A/B 测试）
- [ ] 每周训练更新
- [ ] 模型版本管理

**配置**:

```yaml
ml_engine:
  features: [code_complexity, change_size, risk_score, historical_failure_rate, execution_duration, dependency_depth, coverage]
  model:
    type: "xgboost"
    hyperparameters: { n_estimators: 100, max_depth: 6, learning_rate: 0.1 }
  ab_testing:
    traffic_split: { rule_engine: 0.5, ml_model: 0.5 }
```

### 1.5 CI/CD 集成

#### FR-1.5.1: Jenkins 插件

**验收标准**:
- [ ] 发布到 Jenkins Plugin Market
- [ ] 支持 Pipeline 和 Freestyle
- [ ] 支持质量门禁（覆盖率阈值 + 风险阈值）

**Pipeline 步骤**:
```groovy
precisionqaAnalyze serverUrl: '...', apiKey: '...', projectKey: '...'
precisionqaGate coverageThreshold: 80, riskThreshold: 70
```

#### FR-1.5.2: GitLab CI 集成

**验收标准**:
- [ ] 提供 CI Job 模板
- [ ] 支持 MR 评论集成

#### FR-1.5.3: GitHub Actions 集成

**验收标准**:
- [ ] 发布到 GitHub Marketplace
- [ ] 支持 PR 状态检查

### 1.6 Web Console

#### FR-1.6.1: 项目管理

**验收标准**:
- [ ] 项目 CRUD + 多环境配置
- [ ] 分支白/黑名单
- [ ] CI/CD 集成配置

#### FR-1.6.2: 覆盖率可视化

**验收标准**:
- [ ] 代码热力图（绿色覆盖/红色未覆盖）
- [ ] 按模块/包/类/方法层级下钻
- [ ] 覆盖率趋势图

#### FR-1.6.3: 影响分析界面

**验收标准**:
- [ ] 树形展示影响范围
- [ ] 风险等级颜色标识
- [ ] 支持导出报告

#### FR-1.6.4: 用例推荐界面

**验收标准**:
- [ ] 推荐用例列表（名称、类型、优先级、置信度）
- [ ] 手动添加/删除
- [ ] 一键触发 CI/CD

---

## 第 2 节：非功能需求

### 2.1 性能
- 影响 API P99 < 5s（万级变更）
- 推荐 API P99 < 3s
- 覆盖率上报 P99 < 1s
- Web Console 加载 < 3s
- 系统支持 1000+ 并发分析请求

### 2.2 可用性
- 目标: 99%（月度）
- RTO: 1h, RPO: 1h
- PostgreSQL 主从, Neo4j 3 节点, ClickHouse 3 副本, 应用 >= 2 副本

### 2.3 安全
- TLS 1.2+ 全链路加密
- OAuth2/OIDC + RBAC
- AES-256 静态加密
- 审计日志 90 天

### 2.4 可扩展性
- 应用无状态，支持 K8s HPA
- Neo4j 因果集群, ClickHouse 分布式表

### 2.5 可观测性
- JSON 结构化日志 → Loki/ELK，保留 30 天
- Prometheus RED + USE 指标
- 告警: 可用性 < 99% P1, 错误率 > 5% P2, P99 > 10s P2

---

## 第 3 节：基础设施需求

| 服务 | 用途 | 环境 |
|------|------|------|
| Kubernetes | 容器编排 | 全部 |
| Neo4j | 图数据库 | 全部 |
| ClickHouse | 时序数据库 | 全部 |
| PostgreSQL | 关系数据库 | 全部 |
| Redis | 缓存 | 全部 |
| MinIO/S3 | 对象存储 | 全部 |
| Prometheus + Grafana | 监控 | 全部 |

---

## 第 4 节：集成需求

| 外部服务 | 协议 | 认证 | 方向 |
|---------|------|------|------|
| GitLab/GitHub API | HTTPS | API Key/OAuth | 出站 |
| Jira/TestRail | HTTPS | API Key | 出站 |
| Jenkins | HTTPS | API Key | 出站 |
| GitLab/GitHub Webhook | HTTPS | HMAC 签名 | 入站 |

---

## 第 5 节：部署需求

| 阶段 | 目标 | 进入条件 | 验证 |
|------|------|---------|------|
| 1 | dev (Minikube) | Helm Charts 就绪 | 健康检查通过 |
| 2 | test (K8s) | dev 验证完成 | 集成测试通过 |
| 3 | staging (K8s HA) | test 稳定 2 周 | 性能测试通过 |
| 4 | prod (K8s HA) | staging 审批 | 冒烟测试 + 监控验证 |

---

## 第 6 节：测试需求

| 测试编号 | 描述 | 预期结果 |
|---------|------|---------|
| IVT-001 | API Server 健康检查 | HTTP 200 |
| IVT-002 | Neo4j 连接测试 | 查询成功 |
| IVT-003 | ClickHouse 写入测试 | 数据持久化 |
| IVT-004 | 覆盖率上报测试 | 上报成功 |
| IVT-005 | 影响分析端到端 | 正确推荐 |

**性能测试**:

| 场景 | 目标 | 阈值 | 持续 |
|------|------|------|------|
| 影响 API 基准 | P99 | 3s | 5min |
| 影响 API 峰值 | P99 | 5s | 10min |
| 覆盖率上报 | P99 | 1s | 5min |

---

## 第 7 节：文档需求

- [ ] 架构设计文档
- [ ] API 接口文档（OpenAPI）
- [ ] 数据模型文档
- [ ] 部署运维手册
- [ ] 用户使用手册
- [ ] CI/CD 集成指南

---

## 第 8 节：验收标准汇总

### 开发环境
- [ ] 基础设施部署完成
- [ ] 核心 API 可访问
- [ ] 1 个试点项目接入

### 测试环境
- [ ] 高可用部署完成
- [ ] 性能测试通过
- [ ] 3 个项目接入

### 生产环境
- [ ] 备份恢复验证
- [ ] 监控告警激活
- [ ] 运维手册完成

---

## 相关文档

- **差距分析**: `GAP_precision_testing_20260425.md`
- **产品方案**: `docs/precision_testing/product_solution.md`

---

**文档版本**: 1.0 | **最后更新**: 2026-04-25 | **下次审查**: 2026-05-09
