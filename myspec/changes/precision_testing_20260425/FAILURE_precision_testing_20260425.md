# 故障模式文档 - PrecisionQA 精准测试平台

**创建日期**: 2026-04-25

**最后更新**: 2026-04-25

**背景**: 精准测试平台建设 - 企业级智能测试推荐平台

**平台**: Kubernetes + Docker

**区域**: 默认区域

---

## 概述

本文档记录了 PrecisionQA 精准测试平台在多环境部署和运维过程中积累的故障经验，涵盖覆盖率采集、依赖分析、影响分析、推荐引擎、CI/CD 集成和 Web Console 等核心组件的常见故障模式。

**核心要点**: 即使有完善的架构设计和自动化测试，没有预部署验证和故障预防措施，新环境仍会遇到相同的问题。

---

## 目录

1. [预部署检查清单](#0-预部署检查清单) ⭐ **从此处开始**
2. [类别 1: 覆盖率采集故障](#1-类别-1-覆盖率采集故障)
3. [类别 2: 依赖分析故障](#2-类别-2-依赖分析故障)
4. [类别 3: 影响分析故障](#3-类别-3-影响分析故障)
5. [类别 4: 推荐引擎故障](#4-类别-4-推荐引擎故障)
6. [类别 5: 数据存储故障](#5-类别-5-数据存储故障)
7. [部署顺序与检查点](#部署顺序与检查点)
8. [快速诊断检查清单](#快速诊断检查清单)

---

## 0. 预部署检查清单

**⚠️ 关键**: 在每个环境部署之前运行此检查清单，以避免常见故障。

### 0.1 基础设施验证

```bash
# 设置环境变量
ENV="dev"  # 修改为：dev、test、staging、prod
NAMESPACE="precisionqa-${ENV}"

echo "=== ${ENV} 环境的预部署检查清单 ==="

# 验证 Kubernetes 集群
kubectl cluster-info
kubectl get nodes
```

**✅ 预期结果**: Kubernetes 集群已连接，节点状态 Ready

### 0.2 数据存储连通性检查

```bash
# PostgreSQL 连接测试
PG_HOST="postgresql-${NAMESPACE}"
PG_PORT=5432
nc -zv $PG_HOST $PG_PORT

# Neo4j 连接测试
NEO4J_HOST="neo4j-${NAMESPACE}"
NEO4J_PORT=7687
nc -zv $NEO4J_HOST $NEO4J_PORT

# ClickHouse 连接测试
CH_HOST="clickhouse-${NAMESPACE}"
CH_PORT=8123
nc -zv $CH_HOST $CH_PORT

# Redis 连接测试
REDIS_HOST="redis-${NAMESPACE}"
REDIS_PORT=6379
nc -zv $REDIS_HOST $REDIS_PORT
```

**✅ 预期结果**: 所有数据库端口可访问

### 0.3 存储验证

```bash
# PVC 状态检查
kubectl get pvc -n $NAMESPACE

# 检查 PVC 是否已绑定
kubectl get pvc -n $NAMESPACE -o json | \
  jq -r '.items[] | select(.status.phase != "Bound") | .metadata.name'
```

**✅ 预期结果**: 所有 PVC 状态为 Bound

### 0.4 配置检查

```bash
# ConfigMap 验证
kubectl get cm -n $NAMESPACE

# Secret 验证
kubectl get secret -n $NAMESPACE

# 检查必需的 ConfigMap
REQUIRED_CONFIGS=("coverage-collector-config" "dependency-analyzer-config")
for config in "${REQUIRED_CONFIGS[@]}"; do
  kubectl get cm $config -n $NAMESPACE || echo "❌ ConfigMap $config 未找到"
done
```

**✅ 预期结果**: 所有配置已创建

### 0.5 镜像可用性检查

```bash
# 验证镜像可用
IMAGES=(
  "registry.example.com/precisionqa/coverage-collector:v1.0.0"
  "registry.example.com/precisionqa/dependency-analyzer:v1.0.0"
  "registry.example.com/precisionqa/impact-analyzer:v1.0.0"
  "registry.example.com/precisionqa/recommendation-engine:v1.0.0"
  "registry.example.com/precisionqa/web-console:v1.0.0"
)

for image in "${IMAGES[@]}"; do
  echo "检查 $image..."
  docker pull $image && echo "  ✅ 可用" || echo "  ❌ 不可用"
done
```

**✅ 预期结果**: 所有镜像可拉取

### 0.N 快速修复命令参考

| 问题 | 快速修复命令 |
|------|-------------|
| PVC 未绑定 | `kubectl describe pvc <pvc-name> -n <namespace>` 查看原因 |
| 镜像拉取失败 | `docker pull <image>` 预拉取镜像 |
| ConfigMap 缺失 | `kubectl create cm <name> --from-file=<file> -n <namespace>` |
| 数据库连接失败 | 检查 Service 和 DNS 解析 |

---

## 1. 类别 1: 覆盖率采集故障

### 问题 1.1: JaCoCo Agent 无法生成覆盖率文件

**症状**:
```
ERROR: Unable to read execution data file /tmp/jacoco.exec
File does not exist
```

**根本原因**: JaCoCo Agent 未正确附加到 JVM，或输出路径配置错误

**解决方案**:
```bash
# 确认 JVM 参数
-javaagent:/path/to/jacocoagent.jar=output=file,destfile=/tmp/jacoco.exec

# 检查文件权限
ls -la /tmp/jacoco.exec

# 确保目录存在
mkdir -p /tmp/jacoco
chmod 777 /tmp/jacoco
```

**预防措施**:
- 在应用启动脚本中添加 JaCoCo Agent 验证
- 检查 JVM 参数是否正确传递
- 确保输出目录有写权限

---

### 问题 1.2: Istanbul 覆盖率数据格式不兼容

**症状**:
```
ERROR: Unable to parse Istanbul coverage data
Invalid JSON format
```

**根本原因**: 不同版本的 Istanbul/nyc 生成的 JSON 格式存在差异

**解决方案**:
```python
# 添加格式转换
import json

def normalize_istanbul_data(raw_data):
    # 处理不同版本的 Istanbul 格式
    if 'coverage' in raw_data:
        return raw_data  # 新版本
    else:
        return {'coverage': raw_data}  # 旧版本
```

**预防措施**:
- 文档化支持的 Istanbul/nyc 版本
- 添加版本检查和警告
- 提供格式转换工具

---

### 问题 1.3: Source Map 解析失败

**症状**:
```
ERROR: Unable to resolve source map
Invalid source map URL
```

**根本原因**: Source Map 文件路径不正确或文件缺失

**解决方案**:
```bash
# 验证 Source Map 文件存在
ls -la /path/to/app.js.map

# 检查 Source Map 引用
head -n 5 /path/to/app.js | grep sourceMappingURL

# 确保构建工具生成 Source Map
# webpack.config.js
module.exports = {
  devtool: 'source-map'  // 或 'inline-source-map'
}
```

**预防措施**:
- 在 CI/CD 中验证 Source Map 文件生成
- 添加 Source Map 完整性检查
- 文档化构建工具配置

---

## 2. 类别 2: 依赖分析故障

### 问题 2.1: Tree-sitter 解析失败

**症状**:
```
ERROR: Tree-sitter parser initialization failed
Language not supported
```

**根本原因**: Tree-sitter 语言库未正确安装或路径配置错误

**解决方案**:
```bash
# 安装 Tree-sitter 语言库
pip install tree-sitter
pip install tree-sitter-java
pip install tree-sitter-javascript
pip install tree-sitter-typescript

# 验证安装
python -c "import tree_sitter_java; print('OK')"
```

**预防措施**:
- 在依赖清单中明确声明 Tree-sitter 语言库
- 添加启动时的语言库验证
- 提供离线安装包

---

### 问题 2.2: Neo4j 连接池耗尽

**症状**:
```
ERROR: Unable to acquire connection from Neo4j pool
Connection pool exhausted
```

**根本原因**: Neo4j 连接未正确释放，或并发请求超过池大小

**解决方案**:
```python
# 调整连接池配置
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://neo4j:7687",
    auth=("neo4j", "password"),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=60
)

# 使用 context manager 确保连接释放
with driver.session() as session:
    result = session.run(query)
```

**预防措施**:
- 监控连接池使用率
- 设置合理的超时时间
- 实施连接泄漏检测

---

### 问题 2.3: 依赖图数据不一致

**症状**:
```
WARNING: Dependency graph data inconsistency detected
Node exists but edge is missing
```

**根本原因**: 静态分析和运行时采集的数据未正确融合

**解决方案**:
```python
# 添加数据一致性检查
def validate_graph_data(neo4j_client):
    query = """
    MATCH (n)
    WHERE NOT (n)-[:DEPENDS_ON]->()
    AND n.type IN ['Class', 'Method']
    RETURN count(n) as isolated_nodes
    """
    result = neo4j_client.execute(query)
    if result['isolated_nodes'] > threshold:
        raise GraphInconsistencyError()
```

**预防措施**:
- 定期运行图数据一致性检查
- 实施数据修复机制
- 记录数据版本和变更历史

---

## 3. 类别 3: 影响分析故障

### 问题 3.1: Git diff 解析超时

**症状**:
```
ERROR: Git diff parsing timeout
Repository too large
```

**根本原因**: 大型仓库的 diff 解析耗时过长，或网络问题

**解决方案**:
```bash
# 使用浅克隆减少数据量
git clone --depth 1 <repo-url>

# 限制 diff 范围
git diff HEAD~10 HEAD -- '*.java' '*.js'

# 使用增量解析
git diff <commit-hash> -- <file-path>
```

**预防措施**:
- 实施超时和重试机制
- 提供 diff 范围限制选项
- 缓存 diff 结果

---

### 问题 3.2: 图遍历性能问题

**症状**:
```
ERROR: Graph traversal too slow
Impact analysis timeout
```

**根本原因**: 大型依赖图的深度遍历耗时过长

**解决方案**:
```cypher
// 使用索引优化
CREATE INDEX ON :Class(name);
CREATE INDEX ON :Method(name);

// 限制遍历深度
MATCH path = (start:Class {name: $class_name})-[:DEPENDS_ON*1..3]->(end:Class)
RETURN end;

// 使用 A* 算法或最短路径
CALL apoc.algo.shortestPath(start, end, 'DEPENDS_ON', 3.0)
YIELD path
RETURN path
```

**预防措施**:
- 设置遍历深度限制
- 使用图分区减少遍历范围
- 实施性能监控和告警

---

## 4. 类别 4: 推荐引擎故障

### 问题 4.1: ML 模型加载失败

**症状**:
```
ERROR: Failed to load ML model
Model file not found or corrupted
```

**根本原因**: 模型文件路径错误或文件损坏

**解决方案**:
```python
import os
import joblib

# 添加模型文件验证
def load_model(model_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        raise ModelLoadError(f"Failed to load model: {e}")

# 使用模型版本管理
MODEL_VERSION = "v1.0.0"
model_path = f"/models/xgboost_{MODEL_VERSION}.pkl"
model = load_model(model_path)
```

**预防措施**:
- 实施模型文件完整性检查
- 使用模型版本管理
- 提供模型回滚机制

---

### 问题 4.2: 规则引擎执行超时

**症状**:
```
ERROR: Rule engine execution timeout
Too many test cases to evaluate
```

**根本原因**: 规则引擎处理大量测试用例时耗时过长

**解决方案**:
```python
# 添加批处理和超时控制
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def execute_rules_with_timeout(test_cases, timeout=30):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(evaluate_rule, tc) for tc in test_cases]
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except TimeoutError:
                results.append(None)  # 超时标记
        return results
```

**预防措施**:
- 实施规则优先级排序
- 添加超时和降级机制
- 提供规则执行性能监控

---

## 5. 类别 5: 数据存储故障

### 问题 5.1: ClickHouse 写入失败

**症状**:
```
ERROR: ClickHouse insert failed
Table not found or database connection error
```

**根本原因**: ClickHouse 表不存在或连接配置错误

**解决方案**:
```bash
# 验证表存在
clickhouse-client --query "SHOW TABLES FROM precisionqa"

# 创建表（如果不存在）
clickhouse-client --query "
CREATE TABLE IF NOT EXISTS precisionqa.line_coverage_dev (
    timestamp DateTime,
    file_path String,
    line_number UInt32,
    covered UInt8
) ENGINE = MergeTree()
ORDER BY (timestamp, file_path, line_number)
"
```

**预防措施**:
- 在部署脚本中自动创建表
- 添加表存在性检查
- 实施数据库迁移管理

---

### 问题 5.2: Redis 内存不足

**症状**:
```
ERROR: Redis OOM command not allowed when memory used > 'maxmemory'
```

**根本原因**: Redis 内存使用超过限制

**解决方案**:
```bash
# 调整 maxmemory 配置
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 或在部署配置中设置
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

**预防措施**:
- 监控 Redis 内存使用率
- 设置合理的内存上限
- 实施数据过期策略

---

## 部署顺序与检查点

### 推荐部署顺序

```
阶段 1: 预部署验证（第 0 节）
├── ✅ 0.1 基础设施验证
├── ✅ 0.2 数据存储连通性检查
├── ✅ 0.3 存储验证
├── ✅ 0.4 配置检查
└── ✅ 0.5 镜像可用性检查

阶段 2: 数据存储部署
├── 部署 PostgreSQL
├── 部署 Neo4j
├── 部署 ClickHouse
├── 部署 Redis
├── ⏸️ 检查点: 验证数据库健康状态
│   └── kubectl get pods -n precisionqa-dev
└── 预期: 所有数据库 Pod 状态 Running

阶段 3: 后端服务部署
├── 部署覆盖率采集服务
├── 部署依赖分析服务
├── 部署影响分析服务
├── 部署推荐引擎服务
├── ⏸️ 检查点: 验证服务健康状态
│   └── kubectl get pods -n precisionqa-dev
└── 预期: 所有服务 Pod 状态 Running

阶段 4: Web Console 部署
├── 部署 Web Console
├── 配置 Ingress
├── ⏸️ 检查点: 验证 Web 可访问性
│   └── curl https://precisionqa-dev.example.com
└── 预期: Web Console 可访问

阶段 5: CI/CD 集成部署
├── 部署 Jenkins 插件
├── 配置 GitLab CI 模板
├── ⏸️ 检查点: 验证 CI/CD 集成
│   └── 运行测试流水线
└── 预期: 流水线成功执行
```

### 故障恢复流程图

```
覆盖率采集失败？
├── 检查 JaCoCo Agent 是否附加 → 修复: 验证 JVM 参数
├── 检查输出文件权限 → 修复: chmod 777 /tmp/jacoco
└── 检查服务可用性 → 修复: 重启服务

依赖分析失败？
├── 检查 Tree-sitter 库 → 修复: pip install tree-sitter-*
├── 检查 Neo4j 连接 → 修复: 验证连接池配置
└── 检查图数据一致性 → 修复: 运行数据修复脚本

影响分析超时？
├── 检查仓库大小 → 修复: 使用浅克隆
├── 检查遍历深度 → 修复: 限制 max_depth
└── 检查 Neo4j 性能 → 修复: 添加索引

推荐引擎失败？
├── 检查 ML 模型文件 → 修复: 重新训练模型
├── 检查规则引擎超时 → 修复: 添加批处理
└── [升级: 使用降级策略]
```

---

## 快速诊断检查清单

当覆盖率采集失败、依赖分析失败或推荐引擎故障时，按以下顺序排查：

### 步骤 1: 检查 Pod 状态

```bash
kubectl get pods -n precisionqa-dev
kubectl describe pod <pod-name> -n precisionqa-dev
```

### 步骤 2: 检查日志

```bash
kubectl logs <pod-name> -n precisionqa-dev --tail=100 -f
```

### 步骤 3: 检查数据库连接

```bash
# PostgreSQL
kubectl exec -it postgresql-0 -n precisionqa-dev -- psql -U postgres -c "SELECT 1"

# Neo4j
kubectl exec -it neo4j-0 -n precisionqa-dev -- cypher-shell -u neo4j -p changeme "RETURN 1"

# ClickHouse
kubectl exec -it clickhouse-0 -n precisionqa-dev -- clickhouse-client --query "SELECT 1"

# Redis
kubectl exec -it redis-0 -n precisionqa-dev -- redis-cli PING
```

### 步骤 4: 检查配置

```bash
kubectl get cm -n precisionqa-dev
kubectl get secret -n precisionqa-dev
```

### 步骤 5: 重启服务

```bash
kubectl rollout restart deployment/<service-name> -n precisionqa-dev
```

---

## 关键经验总结

| 问题 | 快速修复 |
|------|---------|
| JaCoCo Agent 无法生成覆盖率文件 | 验证 JVM 参数，检查输出路径权限 |
| Istanbul 覆盖率数据格式不兼容 | 添加格式转换，支持多版本 |
| Source Map 解析失败 | 验证 Source Map 文件存在，检查构建配置 |
| Tree-sitter 解析失败 | 安装语言库，验证安装 |
| Neo4j 连接池耗尽 | 调整连接池配置，确保连接释放 |
| 依赖图数据不一致 | 运行一致性检查，实施数据修复 |
| Git diff 解析超时 | 使用浅克隆，限制 diff 范围 |
| 图遍历性能问题 | 添加索引，限制遍历深度 |
| ML 模型加载失败 | 验证模型文件路径，实施版本管理 |
| 规则引擎执行超时 | 添加批处理，设置超时控制 |
| ClickHouse 写入失败 | 验证表存在，检查连接配置 |
| Redis 内存不足 | 调整 maxmemory，设置过期策略 |

---

## 相关文档

- 命名规范: `NAMING_precision_testing_20260425.md`
- 基础设施依赖规则: `DEPS_precision_testing_20260425.md`
- 任务清单: `TASKS_precision_testing_20260425.md`

---

*本文档基于精准测试平台建设经验创建*

**文档版本**: 1.0
**最后更新**: 2026-04-25
