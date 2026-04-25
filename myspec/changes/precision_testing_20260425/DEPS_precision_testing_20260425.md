# 基础设施与 DevOps 依赖规则 - PrecisionQA 精准测试平台

**文档 ID**: DEPS_PrecisionQA_Platform

**创建日期**: 2026-04-25

**分支**: feature/precisionqa-platform

**状态**: 草稿

---

## 目录

- [第 1 节：概述](#第-1-节概述)
- [第 2 节：环境依赖规则](#第-2-节环境依赖规则)
- [第 3 节：基础设施组件依赖](#第-3-节基础设施组件依赖)
- [第 4 节：跨服务依赖规则](#第-4-节跨服务依赖规则)
- [第 5 节：部署阻断规则](#第-5-节部署阻断规则)
- [第 6 节：命名与标签依赖](#第-6-节命名与标签依赖)
- [第 7 节：验证检查清单](#第-7-节验证检查清单)
- [第 8 节：常见模式](#第-8-节常见模式)

---

## 第 1 节：概述

### 目的

本文档定义了 PrecisionQA 精准测试平台的基础设施配置、服务部署和环境晋升的依赖规则。依赖规则确保资源按正确顺序创建，服务通过已批准的路径通信，并在前置条件不满足时阻断部署。

### 范围

| 方面 | 覆盖范围 |
|------|----------|
| **项目** | PrecisionQA 精准测试平台 |
| **团队** | 平台工程团队、测试工程团队 |
| **环境** | dev, test, staging, prod |
| **IaC 工具** | Helm + Kubernetes |
| **CI/CD 平台** | GitLab CI, GitHub Actions |
| **云服务商** | AWS / Azure / GCP |

### 相关文档

| 文档 | ID | 关系 |
|------|----|------|
| 差距分析 | GAP_PrecisionQA_Platform | 基线和差距识别 |
| 需求规格 | REQ_PrecisionQA_Platform | 功能和非功能需求 |
| 命名规范 | NAMING_PrecisionQA_Platform | 资源命名标准 |

---

## 第 2 节：环境依赖规则

### 2.1 环境晋升顺序

基础设施变更必须遵循以下晋升路径。除非获得平台工程负责人的明确例外批准，否则禁止跳过环境。

```
                     +-------+
                     |  dev  |   <-- 所有变更从这里开始
                     +---+---+
                         |
                         v
                     +-------+
                     | test  |   <-- 自动化集成测试
                     +---+---+
                         |
                         v
                     +---------+
                     | staging |   <-- 预生产一致性检查
                     +----+----+
                          |
                          v
                     +-------+
                     | prod  |   <-- 生产发布
                     +-------+
```

**晋升规则：**

1. 在 `test` 环境中未通过测试运行的情况下，任何变更不得晋升到 `staging`
2. 在 `staging` 环境中未成功部署的情况下，任何变更不得晋升到 `prod`
3. 热修复遵循路径 `dev -> staging -> prod`，但要求在 24 小时内完成 PIR（事后复盘）

### 2.2 环境隔离规则

1. **网络隔离**：每个环境必须位于自己的 Kubernetes Namespace 中
2. **IAM 边界**：ServiceAccount 必须包含环境范围的边界
3. **配置隔离**：ConfigMap 和 Secret 必须按环境划分
4. **密钥隔离**：数据库密码必须存储在环境特定的 Secret 中
5. **日志隔离**：日志必须按环境划分到不同的日志组

### 2.3 各环境配置

| 环境 | Namespace | 存储类 | 副本数 | 资源配额 |
|------|-----------|--------|--------|----------|
| dev | precisionqa-dev | standard | 1 | 开发配额 |
| test | precisionqa-test | standard | 2 | 测试配额 |
| staging | precisionqa-staging | standard | 2 | 预发布配额 |
| prod | precisionqa-prod | ssd | 3 | 生产配额 |

---

## 第 3 节：基础设施组件依赖

### 3.1 依赖图

```
Phase 1 (Foundation)         Phase 2 (Storage)          Phase 3 (Services)
+-----------------+          +-----------------+        +------------------+
|     Namespace   |--------->|   PostgreSQL   |------->| Coverage Collector|
+-----------------+          +-----------------+        +------------------+
         |                            |                          |
         v                            v                          v
+-----------------+          +-----------------+        +------------------+
|   StorageClass   |--------->|     Neo4j      |------->|Dependency Analyzer|
+-----------------+          +-----------------+        +------------------+
         |                            |                          |
         v                            v                          v
+-----------------+          +-----------------+        +------------------+
|    ConfigMap    |--------->|   ClickHouse   |------->| Impact Analyzer   |
+-----------------+          +-----------------+        +------------------+
         |                            |                          |
         v                            v                          v
+-----------------+          +-----------------+        +------------------+
|     Secret      |--------->|     Redis      |------->|Recommendation Eng |
+-----------------+          +-----------------+        +------------------+
                                                                     |
                                                                     v
                                                             +------------------+
                                                             |   Web Console    |
                                                             +------------------+
```

### 3.2 组件依赖矩阵

| 组件 | 依赖于 | 阻断 | Helm Chart |
|------|--------|------|------------|
| Namespace | 无 | 所有资源 | 基础设施 |
| StorageClass | Namespace | PVC | 基础设施 |
| ConfigMap | Namespace | 应用部署 | 基础设施 |
| Secret | Namespace | 应用部署 | 基础设施 |
| PostgreSQL | Namespace、StorageClass | 业务服务 | 数据存储 |
| Neo4j | Namespace、StorageClass | 依赖分析服务 | 数据存储 |
| ClickHouse | Namespace、StorageClass | 覆盖率服务 | 数据存储 |
| Redis | Namespace、StorageClass | 缓存服务 | 数据存储 |
| Coverage Collector | PostgreSQL、ClickHouse、ConfigMap、Secret | 依赖分析 | 应用服务 |
| Dependency Analyzer | Neo4j、ConfigMap、Secret | 影响分析 | 应用服务 |
| Impact Analyzer | Neo4j、ConfigMap、Secret | 推荐引擎 | 应用服务 |
| Recommendation Engine | Neo4j、ClickHouse、ConfigMap、Secret | Web Console | 应用服务 |
| Web Console | 所有后端服务、ConfigMap、Secret | Ingress | 应用服务 |
| Ingress | Web Console Service | DNS | 网络 |

### 3.3 Helm Charts 依赖

```
precisionqa/
+-- charts/
|   +-- common/              <-- 共享 Chart 库
|   +-- postgresql/          <-- PostgreSQL Chart
|   +-- neo4j/               <-- Neo4j Chart
|   +-- clickhouse/          <-- ClickHouse Chart
|   +-- redis/               <-- Redis Chart
|   +-- coverage-collector/  <-- 覆盖率采集服务 Chart
|   +-- dependency-analyzer/ <-- 依赖分析服务 Chart
|   +-- impact-analyzer/     <-- 影响分析服务 Chart
|   +-- recommendation-engine/ <-- 推荐引擎服务 Chart
|   +-- web-console/         <-- Web Console Chart
+-- environments/
    +-- dev/
    |   +-- values.yaml
    +-- test/
    |   +-- values.yaml
    +-- staging/
    |   +-- values.yaml
    +-- prod/
        +-- values.yaml
```

### 3.4 资源创建顺序

**Phase 1 -- 基础层（无依赖）**

1. Kubernetes Namespace
2. StorageClass
3. ConfigMap（全局配置）
4. Secret（全局密钥）

**Phase 2 -- 数据存储层（依赖于 Phase 1）**

5. PostgreSQL（主从）
6. Neo4j（单节点或集群）
7. ClickHouse（单节点或集群）
8. Redis（主从或哨兵）

**Phase 3 -- 应用服务层（依赖于 Phase 2）**

9. Coverage Collector 服务
10. Dependency Analyzer 服务
11. Impact Analyzer 服务
12. Recommendation Engine 服务

**Phase 4 -- Web 层（依赖于 Phase 3）**

13. Web Console 服务
14. Ingress 配置
15. DNS 配置

**Phase 5 -- 验证（依赖于 Phase 4）**

16. 健康检查验证
17. 集成测试验证
18. 性能测试验证

---

## 第 4 节：跨服务依赖规则

### 4.1 共享基础设施规则

| 共享资源 | 所有者 | 变更审批 | 影响范围 |
|----------|--------|----------|----------|
| PostgreSQL | 平台工程团队 | 技术负责人审批 | 所有服务 |
| Neo4j | 平台工程团队 | 技术负责人审批 | 依赖分析、影响分析、推荐引擎 |
| ClickHouse | 平台工程团队 | 技术负责人审批 | 覆盖率采集服务 |
| Redis | 平台工程团队 | 技术负责人审批 | 所有缓存服务 |
| Ingress Controller | 平台工程团队 | 技术负责人审批 | 所有 Web 服务 |

**规则：**

1. 共享基础设施的变更需要至少 2 个审批
2. 共享资源变更必须在维护窗口内部署
3. 在应用任何共享资源变更之前，必须记录回滚计划

### 4.2 服务间通信规则

```
                   +-------------------+
                   |     Ingress       |
                   +--------+----------+
                            |
              +--------------+--------------+
              |                             |
      +-------+--------+          +---------+------+
      | Web Console     |          | CI/CD Plugin   |
      +-------+--------+          +---------+------+
              |                             |
              v                             v
      +-------+--------+          +---------+------+
      | API Gateway     |          |   Jenkins/     |
      | (Optional)      |          |   GitLab CI    |
      +-------+--------+          +---------+------+
              |
              v
      +-------+--------+          +---------+------+
      | Coverage        |          | Dependency     |
      | Collector       |          | Analyzer       |
      +-------+--------+          +---------+------+
              |                             |
              v                             v
      +-------+--------+          +---------+------+
      | Impact           |          | Recommendation  |
      | Analyzer         |          | Engine         |
      +-----------------+          +-----------------+
```

| 规则 ID | 描述 | 执行方式 |
|---------|------|----------|
| COM-001 | 服务必须通过 Service 或 Ingress 通信 | NetworkPolicy |
| COM-002 | 跨 Namespace 通信需要 NetworkPolicy 允许 | NetworkPolicy |
| COM-003 | 服务不得直接访问另一个服务的数据库 | IAM + NetworkPolicy |
| COM-004 | 外部访问必须通过 Ingress | Ingress Controller |

### 4.3 数据库访问规则

| 服务 | 数据库 | 访问级别 | 连接方式 | Secret |
|------|--------|----------|----------|--------|
| Coverage Collector | PostgreSQL | 读写 | Service Account | postgresql-secret |
| Dependency Analyzer | Neo4j | 读写 | Service Account | neo4j-secret |
| Impact Analyzer | Neo4j | 读写 | Service Account | neo4j-secret |
| Recommendation Engine | ClickHouse | 读写 | Service Account | clickhouse-secret |
| All Services | Redis | 读写 | Service Account | redis-secret |

**规则：**

1. 每个服务必须使用自己的 ServiceAccount 访问数据库
2. 只读访问应为默认设置
3. 数据库凭证必须每 90 天轮换
4. 任何服务不得在 `prod` 环境中拥有超级用户权限

---

## 第 5 节：部署阻断规则

### 5.1 硬阻断

| 阻断 ID | 条件 | 检测方式 | 解决方案 |
|---------|------|----------|----------|
| HB-001 | Helm dry-run 显示将删除生产数据库 PVC | `helm diff` | 手动审查 plan；添加 PVC 保护 |
| HB-002 | Pod 安全策略允许特权容器 | `kubectl get psp` | 移除特权配置 |
| HB-003 | ServiceAccount 拥有 cluster-admin 权限 | `kubectl auth can-i` | 最小化 RBAC 权限 |
| HB-004 | Ingress 缺少 TLS 证书 | `kubectl get ingress` | 添加 TLS 配置 |
| HB-005 | 数据库迁移包含不可逆操作 | 迁移审查脚本 | 添加可逆迁移 |
| HB-006 | 资源限制未设置 | `kubectl describe pod` | 添加资源限制 |
| HB-007 | 健康检查未配置 | `kubectl describe pod` | 配置健康检查 |

### 5.2 软阻断

| 阻断 ID | 条件 | 检测方式 | 解决方案 | 默认操作 |
|---------|------|----------|----------|----------|
| SB-001 | Helm diff 显示超过 10 个资源变更 | `helm diff` | 审查并确认 | 警告 + 需确认 |
| SB-002 | 镜像标签为 `latest` | CI 流水线检查 | 使用版本标签 | 警告 |
| SB-003 | 新服务未定义健康检查 | 检查清单 | 添加健康检查 | 警告 |
| SB-004 | 资源标签不完整 | `kubectl get pod` | 添加缺失标签 | 警告 |
| SB-005 | 监控未配置 | `kubectl get servicemonitor` | 配置监控 | 警告 |

### 5.3 环境特定阻断

| 环境 | 附加阻断 | 理由 |
|------|----------|------|
| dev | 无 | 开发环境允许更快的迭代 |
| test | 所有硬阻断 + SB-001、SB-002 | 基线质量门禁 |
| staging | 所有硬阻断 + 所有软阻断 | 必须反映生产就绪状态 |
| prod | 所有硬阻断 + 所有软阻断 + 手动审批 | 生产环境的最高安全级别 |

---

## 第 6 节：命名与标签依赖

### 6.1 资源命名依赖

| 资源类型 | 命名模式 | 依赖于 | 示例 |
|----------|----------|--------|------|
| Namespace | `precisionqa-{env}` | 环境名称 | `precisionqa-dev` |
| Deployment | `{service}-{env}` | 服务名称、环境 | `coverage-collector-dev` |
| Service | `{service}-{env}` | 服务名称、环境 | `coverage-collector-dev` |
| ConfigMap | `{service}-{env}-config` | 服务名称、环境 | `coverage-collector-dev-config` |
| Secret | `{service}-{env}-secret` | 服务名称、环境 | `postgresql-dev-secret` |
| Ingress | `{service}-{env}` | 服务名称、环境 | `web-dev` |

### 6.2 各资源类型的必需标签

| 标签键 | 适用资源 | 格式 | 示例 | 执行工具 |
|--------|----------|------|------|----------|
| `app` | 所有资源 | `precisionqa` | `precisionqa` | Helm |
| `component` | 所有资源 | 组件名称 | `coverage-collector` | Helm |
| `environment` | 所有资源 | `dev`, `test`, `staging`, `prod` | `dev` | Helm |
| `managed-by` | 所有资源 | `helm` | `helm` | Helm |
| `version` | 所有资源 | 版本号 | `v1.0.0` | Helm |

### 6.3 基于标签的访问控制规则

| 规则 | 标签条件 | 效果 | 范围 |
|------|----------|------|------|
| TBA-001 | `environment = prod` 且调用者不在 prod-admin 角色中 | 拒绝修改操作 | 所有生产资源 |
| TBA-002 | `managed-by != helm` | 拒绝所有操作 | 所有资源 |
| TBA-003 | 缺少 `environment` 标签 | 拒绝资源创建 | 所有资源 |

---

## 第 7 节：验证检查清单

### 7.1 部署前检查清单

- [ ] Helm `diff` 无错误且已由 2 名团队成员审查
- [ ] 所有硬阻断（第 5.1 节）已解决或已记录例外情况
- [ ] 所有软阻断（第 5.2 节）已确认
- [ ] 镜像已构建、扫描并推送到镜像仓库，使用版本化标签
- [ ] 数据库迁移脚本已在低等级环境中测试
- [ ] 健康检查已配置
- [ ] TLS 证书已配置
- [ ] DNS 记录已准备
- [ ] 回滚计划已记录并测试
- [ ] 利益相关者已收到部署窗口通知

### 7.2 部署后验证

- [ ] Helm `upgrade` 无错误完成
- [ ] Pod 正在运行且已通过健康检查
- [ ] Service Endpoint 可访问
- [ ] Ingress 返回预期响应
- [ ] DNS 解析返回正确的 IP 地址
- [ ] TLS 证书有效
- [ ] 日志正在写入
- [ ] 监控和告警已配置
- [ ] 集成测试通过
- [ ] 后续的 `helm diff` 中无意外变更

### 7.3 环境就绪检查清单

| 检查项 | dev | test | staging | prod |
|--------|-----|------|---------|------|
| Namespace 已创建 | [ ] | [ ] | [ ] | [ ] |
| StorageClass 已配置 | [ ] | [ ] | [ ] | [ ] |
| PostgreSQL 已部署 | [ ] | [ ] | [ ] | [ ] |
| Neo4j 已部署 | [ ] | [ ] | [ ] | [ ] |
| ClickHouse 已部署 | [ ] | [ ] | [ ] | [ ] |
| Redis 已部署 | [ ] | [ ] | [ ] | [ ] |
| ConfigMap 已创建 | [ ] | [ ] | [ ] | [ ] |
| Secret 已创建 | [ ] | [ ] | [ ] | [ ] |

### 7.4 回滚验证

- [ ] Helm `rollback` 已成功执行
- [ ] Pod 已回滚到先前版本
- [ ] 数据库迁移已回滚（如适用）
- [ ] 监控和告警已恢复正常
- [ ] 已创建事件工单
- [ | 事后复盘会议已在 24 小时内安排

---

## 第 8 节：常见模式

### 8.1 新服务接入模式

**前置条件**：服务已定义 Dockerfile 和 Helm Chart

**步骤：**

1. **创建 Helm Chart**：`charts/{service-name}/`
   - 添加 `Chart.yaml`、`values.yaml`
   - 定义 Deployment、Service、ConfigMap、Secret

2. **在环境 values 中注册服务**：更新 `environments/{env}/values.yaml`
   - 添加服务配置
   - 传入环境特定变量

3. **创建数据库 Schema**（如适用）：
   - 添加迁移脚本
   - 在 dev 环境测试

4. **配置服务间通信**：
   - 添加 Service 或 Ingress 配置
   - 配置 NetworkPolicy

5. **添加监控**：
   - 创建 ServiceMonitor
   - 配置告警规则

6. **更新文档**：
   - 在依赖矩阵（第 3.2 节）中添加服务条目
   - 在数据库访问表（第 4.3 节）中添加服务条目

7. **在各环境中部署**：遵循第 2.1 节的晋升顺序

### 8.2 数据库迁移模式

**前置条件**：迁移脚本已审查并在本地测试

**步骤：**

1. **创建可逆迁移**：每个 `UP` 迁移必须有对应的 `DOWN` 迁移
2. **在 dev 中测试**：对 dev 数据库运行迁移
3. **在 test 中运行**：作为 CI 流水线的一部分执行
4. **在 staging 中预演**：对生产数据的副本运行
5. **应用到 prod**：在维护窗口内执行
6. **验证**：运行数据完整性检查
7. **完成**：移除回滚标志

### 8.3 服务扩展模式

**前置条件**：服务已稳定运行

**步骤：**

1. **调整副本数**：更新 `values.yaml` 中的 `replicas`
2. **配置 HPA**：添加 HorizontalPodAutoscaler
3. **验证扩展**：测试自动扩展
4. **监控资源**：确保资源配额足够
5. **更新告警**：调整告警阈值

---

## 页脚

| 字段 | 值 |
|------|----|
| **版本** | 1.0 |
| **最后更新** | 2026-04-25 |
| **作者** | 平台工程团队 |
| **审批人** | 技术架构师 |
| **下次评审日期** | 2026-07-25 |

---

**相关文档**:

- 命名规范: `NAMING_precision_testing_20260425.md`
- 故障模式: `FAILURE_precision_testing_20260425.md`
- 任务清单: `TASKS_precision_testing_20260425.md`
