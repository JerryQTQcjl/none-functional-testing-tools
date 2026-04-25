# 命名规范规则 - PrecisionQA 精准测试平台

**文档编号**: NAMING_PrecisionQA_Platform

**创建日期**: 2026-04-25

**分支**: feature/precisionqa-platform

**状态**: 草稿

---

## 目录

- [1. 概述](#1-概述)
- [2. 通用原则](#2-通用原则)
- [3. 资源命名规则](#3-资源命名规则)
- [4. 环境后缀规则](#4-环境后缀规则)
- [5. 标签标准](#5-标签标准)
- [6. 验证](#6-验证)
- [7. 迁移指南](#7-迁移指南)

---

## 1. 概述

### 1.1 目的

本文档为 **PrecisionQA 精准测试平台** 的所有基础设施资源、代码制品和配置对象建立强制性的命名规范。目标如下：

- **可发现性** -- 工程师无需打开控制台即可按名称定位任何资源
- **可追溯性** -- 每个资源名称可关联到所属服务、环境和成本中心
- **一致性** -- 自动化流水线可以程序化地解析和验证资源名称
- **合规性** -- 名称满足企业级安全和合规要求

### 1.2 范围

| 类别 | 资源 |
|------|------|
| 计算 | Kubernetes Deployment、Service、Pod、CronJob |
| 网络 | Ingress、Service、NetworkPolicy |
| 存储 | PVC、PV、StorageClass |
| 数据库 | PostgreSQL、Neo4j、ClickHouse、Redis |
| 配置 | ConfigMap、Secret |
| CI/CD | Jenkins Job、GitLab CI Pipeline、GitHub Actions Workflow |

---

## 2. 通用原则

### 2.1 一致性原则

同一类型的所有资源在每个环境中必须遵循相同的命名模式。`dev` 环境中的服务必须使用与 `prod` 中对应资源相同的结构模式。

**规则**: 如果两名工程师独立命名同一概念资源，结果名称必须完全一致。

### 2.2 描述性原则

资源名称必须能够传达其**用途**、**所属服务**和**环境**，无需读者查阅额外文档。

**规则**: 新团队成员必须能仅从名称判断资源的用途。

### 2.3 简洁性原则

名称应在保持描述性的同时尽可能简短。避免冗余的前缀或后缀。

**规则**: Kubernetes 资源名称最大长度不得超过 63 字符。

### 2.4 环境感知原则

每个可部署资源必须在名称中编码其目标环境。

**规则**: 没有环境标识的资源名称无效。

---

## 3. 资源命名规则

### 3.1 Kubernetes Deployment

**模式**:
```
{service}-{environment}
```

**分隔符**: 连字符（`-`）| **字符限制**: 63 字符

| 资源 | 模式 | 示例 |
|------|------|------|
| 覆盖率采集服务 | `{service}-{env}` | `coverage-collector-dev` |
| 依赖分析服务 | `{service}-{env}` | `dependency-analyzer-dev` |
| 影响分析服务 | `{service}-{env}` | `impact-analyzer-dev` |
| 推荐引擎服务 | `{service}-{env}` | `recommendation-engine-dev` |
| Web Console | `{service}-{env}` | `web-console-dev` |

### 3.2 Kubernetes Service

**模式**:
```
{service}-{environment}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 覆盖率采集服务 | `{service}-{env}` | `coverage-collector-dev` |
| 依赖分析服务 | `{service}-{env}` | `dependency-analyzer-dev` |
| 影响分析服务 | `{service}-{env}` | `impact-analyzer-dev` |
| 推荐引擎服务 | `{service}-{env}` | `recommendation-engine-dev` |
| Web Console | `{service}-{env}` | `web-console-dev` |

### 3.3 Ingress

**模式**:
```
{service}-{environment}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| API Ingress | `api-{env}` | `api-dev` |
| Web Console Ingress | `web-{env}` | `web-dev` |

### 3.4 ConfigMap

**模式**:
```
{service}-{environment}-config
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 覆盖率采集配置 | `{service}-{env}-config` | `coverage-collector-dev-config` |
| 依赖分析配置 | `{service}-{env}-config` | `dependency-analyzer-dev-config` |

### 3.5 Secret

**模式**:
```
{service}-{environment}-secret
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 数据库凭证 | `{service}-{env}-secret` | `postgresql-dev-secret` |
| API 密钥 | `{service}-{env}-secret` | `api-dev-secret` |

### 3.6 PostgreSQL 数据库

**模式**:
```
precisionqa_{entity}_{environment}
```

**分隔符**: 下划线（`_`）| **字符限制**: 63 字符

| 资源 | 模式 | 示例 |
|------|------|------|
| 业务数据库 | `precisionqa_{entity}_{env}` | `precisionqa_business_dev` |
| 测试数据库 | `precisionqa_test_{env}` | `precisionqa_test_dev` |

### 3.7 Neo4j 图数据库

**模式**:
```
precisionqa_{entity}_{environment}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 依赖图数据库 | `precisionqa_dependency_{env}` | `precisionqa_dependency_dev` |
| 图数据备份 | `precisionqa_graph_backup_{env}` | `precisionqa_graph_backup_dev` |

### 3.8 ClickHouse 时序数据库

**模式**:
```
precisionqa_{entity}_{environment}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 覆盖率数据表 | `{metric}_coverage_{env}` | `line_coverage_dev` |
| 指标数据表 | `{metric}_metrics_{env}` | `branch_metrics_dev` |

### 3.9 Redis Key

**模式**:
```
precisionqa:{entity}:{environment}:{id}
```

**分隔符**: 冒号（`:`）用于层级，连字符（`-`）用于段内

| 资源 | 模式 | 示例 |
|------|------|------|
| 任务状态 | `precisionqa:task:{env}:{id}` | `precisionqa:task:dev:12345` |
| 缓存数据 | `precisionqa:cache:{env}:{key}` | `precisionqa:cache:dev:impact_result` |

### 3.10 容器镜像

**模式**:
```
{registry}/precisionqa/{service}:{version}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| 覆盖率采集镜像 | `{registry}/precisionqa/{service}:{version}` | `registry.example.com/precisionqa/coverage-collector:v1.0.0` |
| Web Console 镜像 | `{registry}/precisionqa/{service}:{version}` | `registry.example.com/precisionqa/web-console:v1.0.0` |

### 3.11 CI/CD Pipeline

**模式**:
```
{project}-{service}-{environment}
```

| 资源 | 模式 | 示例 |
|------|------|------|
| GitLab CI Pipeline | `{project}-{service}-{env}` | `precisionqa-coverage-collector-dev` |
| GitHub Actions Workflow | `{service}-{env}` | `coverage-collector-dev` |

---

## 4. 环境后缀规则

### 4.1 环境映射

| 环境 | 后缀 | 短代码 | 示例（Deployment） | 示例（数据库） |
|------|------|--------|---------------------|---------------|
| 开发 | `dev` | `d` | `coverage-collector-dev` | `precisionqa_business_dev` |
| 测试 | `test` | `t` | `coverage-collector-test` | `precisionqa_business_test` |
| 预发布 | `staging` | `s` | `coverage-collector-staging` | `precisionqa_business_staging` |
| 生产 | `prod` | `p` | `coverage-collector-prod` | `precisionqa_business_prod` |

### 4.2 环境位置规则

| 资源类型 | 环境位置 | 示例 |
|----------|----------|------|
| Kubernetes Deployment | 后缀（尾随） | `coverage-collector-dev` |
| Kubernetes Service | 后缀（尾随） | `coverage-collector-dev` |
| Ingress | 后缀（尾随） | `api-dev` |
| PostgreSQL 数据库 | 后缀（尾随） | `precisionqa_business_dev` |
| Neo4j 数据库 | 后缀（尾随） | `precisionqa_dependency_dev` |
| ClickHouse 表 | 后缀（尾随） | `line_coverage_dev` |
| Redis Key | 第三段 | `precisionqa:task:dev:12345` |
| 容器镜像 | Tag | `v1.0.0-dev` |

---

## 5. 标签标准

### 5.1 必需标签

每个支持标签的资源必须包含以下所有标签：

| 标签键 | 描述 | 示例值 | 必需 |
|--------|------|--------|------|
| `app` | 应用名称 | `precisionqa` | 是 |
| `component` | 组件名称 | `coverage-collector` | 是 |
| `environment` | 部署环境 | `dev`, `test`, `staging`, `prod` | 是 |
| `managed-by` | 管理工具 | `helm`, `kubectl` | 是 |
| `version` | 应用版本 | `v1.0.0` | 是 |

### 5.2 可选标签

| 标签键 | 描述 | 示例值 |
|--------|------|--------|
| `team` | 负责团队 | `platform-team` |
| `tier` | 层级 | `backend`, `frontend`, `database` |
| `cost-center` | 成本中心 | `CC-1001` |

### 5.3 标签执行

缺少必需标签的资源必须：

1. 在 Helm 部署前被拒绝
2. 在 CI/CD 流水线中自动添加
3. 定期审计并修复

---

## 6. 验证

### 6.1 自动化验证脚本

```bash
#!/usr/bin/env bash
# naming-validator.sh -- 验证资源命名规范

set -euo pipefail

NAMESPACE="${1:-default}"
VIOLATIONS=0

# 验证 Kubernetes 资源命名
validate_k8s_resources() {
  echo "=== 验证 Kubernetes 资源命名 ==="
  
  # Deployment 命名验证
  kubectl get deployments -n $NAMESPACE -o json | \
    jq -r '.items[].metadata.name' | while read name; do
      if [[ ! "$name" =~ ^[a-z0-9-]+-(dev|test|staging|prod)$ ]]; then
        echo "  ❌ Deployment 命名违规: '$name'"
        ((VIOLATIONS++))
      fi
    done
  
  # Service 命名验证
  kubectl get services -n $NAMESPACE -o json | \
    jq -r '.items[].metadata.name' | while read name; do
      if [[ ! "$name" =~ ^[a-z0-9-]+-(dev|test|staging|prod)$ ]]; then
        echo "  ❌ Service 命名违规: '$name'"
        ((VIOLATIONS++))
      fi
    done
}

# 验证标签
validate_labels() {
  echo "=== 验证必需标签 ==="
  
  REQUIRED_LABELS=("app" "component" "environment" "managed-by" "version")
  
  kubectl get deployments -n $NAMESPACE -o json | \
    jq -c '.items[]' | while read -r res; do
      name=$(echo "$res" | jq -r '.metadata.name')
      labels=$(echo "$res" | jq -r '.metadata.labels // {}')
      
      for label in "${REQUIRED_LABELS[@]}"; do
        if ! echo "$labels" | jq -e ".$label" >/dev/null 2>&1; then
          echo "  ❌ $name 缺少标签: '$label'"
          ((VIOLATIONS++))
        fi
      done
    done
}

validate_k8s_resources
validate_labels

if [ "$VIOLATIONS" -gt 0 ]; then
  echo "❌ 发现 $VIOLATIONS 个违规"
  exit 1
else
  echo "✅ 所有资源命名符合规范"
  exit 0
fi
```

### 6.2 命名检查清单

- [ ] 所有新资源名称遵循第 3 节定义的模式
- [ ] 环境后缀与目标部署环境匹配（第 4 节）
- [ ] 没有资源名称超过 63 字符限制
- [ ] 所有可标记资源上存在必需标签（第 5.1 节）
- [ ] 标签值使用正确格式（例如 `dev` 而不是 `development`）
- [ ] 容器镜像使用版本号标签而非 `latest`
- [ ] 数据库名称包含环境后缀
- [ ] Redis Key 使用分层的冒号分隔模式
- [ ] CI/CD Pipeline 名称遵循命名模式
- [ ] 不使用未经批准缩写

### 6.3 常见错误

| # | 错误 | 错误示例 | 正确示例 | 参考 |
|---|------|----------|----------|------|
| 1 | Deployment 名称缺少环境标识 | `coverage-collector` | `coverage-collector-dev` | 3.1 |
| 2 | 数据库名称使用连字符 | `precisionqa-business-dev` | `precisionqa_business_dev` | 3.6 |
| 3 | Redis Key 使用连字符 | `precisionqa-task-dev-12345` | `precisionqa:task:dev:12345` | 3.9 |
| 4 | 环境后缀格式错误 | `coverage-collector-development` | `coverage-collector-dev` | 4.1 |
| 5 | 容器镜像使用 latest | `coverage-collector:latest` | `coverage-collector:v1.0.0` | 3.10 |
| 6 | 资源名称使用大写字母 | `Coverage-Collector-Dev` | `coverage-collector-dev` | 2.1 |
| 7 | 镜像标签缺少版本 | `coverage-collector:dev` | `coverage-collector:v1.0.0-dev` | 3.10 |
| 8 | 环境标识位置错误 | `dev-coverage-collector` | `coverage-collector-dev` | 4.2 |
| 9 | 超出字符限制 | `very-long-service-name-that-exceeds-kubernetes-limit-dev` | 缩短以适应限制 | 2.3 |
| 10 | 缺少必需标签 | `labels: {app: precisionqa}` | `labels: {app: precisionqa, component: coverage-collector, environment: dev, managed-by: helm, version: v1.0.0}` | 5.1 |

---

## 7. 迁移指南

### 7.1 何时重命名

以下情况应重命名资源：

1. **合规审计**: 安全审查发现命名违规
2. **标准化冲刺**: 专门将所有资源与本文件对齐
3. **新资源引入**: 正在创建或迁移的资源尚未合规
4. **事件根因**: 与命名相关的混乱导致了运维事件

### 7.2 迁移流程

**步骤 1：影响评估**

```
[ ] 识别对当前资源名称的所有引用：
   - Kubernetes 配置
   - Helm Charts
   - CI/CD 流水线
   - 监控和告警配置
   - 文档和运维手册
```

**步骤 2：创建新资源**

1. 使用正确名称在现有资源旁边创建新资源
2. 验证其功能正常且配置相同
3. 对新资源名称运行集成测试

**步骤 3：迁移引用**

1. 更新所有 Helm Charts、CI/CD 配置
2. 更新监控、告警和仪表盘配置
3. 更新文档和运维手册

**步骤 4：验证**

```
[ ] 所有集成测试使用新资源名称通过
[ ] 应用代码中没有对旧资源名称的引用
[ ] Kubernetes 配置中没有对旧资源名称的引用
[ ] 监控指标正在为新资源流动
[ ] 回滚程序已记录并测试
```

**步骤 5：下线旧资源**

1. 验证旧资源流量为零
2. 通过 Helm 或 kubectl 删除旧资源
3. 在团队频道中宣布重命名并更新资产清单

### 7.3 向后兼容性

| 资源类型 | 策略 | 过渡期 |
|----------|------|--------|
| Kubernetes Deployment | 滚动更新 | 0 天 |
| Kubernetes Service | 同时部署新旧服务 | 7 天 |
| Ingress | 将旧路由重定向到新路由 | 30 天 |
| PostgreSQL 数据库 | 使用 pg_dump 迁移 | 14 天 |
| Redis Key | 创建新 Key，设置 TTL | 7 天 |

---

## 页脚

| 字段 | 值 |
|------|-----|
| **版本** | 1.0.0 |
| **最后更新** | 2026-04-25 |
| **下次评审日期** | 2026-07-25（3个月后） |
| **文档负责人** | 平台工程团队 |
| **批准人** | 技术架构师 |
