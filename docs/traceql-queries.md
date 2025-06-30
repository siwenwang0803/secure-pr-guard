# TraceQL 查询示例 - Secure PR Guard

## 核心监控查询

### 1. 平均延迟 (P95)
```traceql
# 查询所有操作的延迟分布
{service.name="secure-pr-guard"}
| select(latency.ms)

# 按操作类型分组的P95延迟
{service.name="secure-pr-guard" && operation.type=~"nitpicker|patch|architect"}
| select(latency.ms)
| group_by(operation.type)

# 查看具体的延迟值
{service.name="secure-pr-guard"}
| select(span.latency.ms, operation.type, span.name)
```

### 2. 成本按模型分析
```traceql
# 总成本按模型分组
{service.name="secure-pr-guard" && cost.model=~"gpt-4o-mini|gpt-4o"}
| select(cost.usd)
| group_by(cost.model)

# 每次操作的成本分布
{service.name="secure-pr-guard"}
| select(cost.usd, cost.model, operation.type)

# 高成本操作识别 (>$0.01)
{service.name="secure-pr-guard" && cost.usd > 0.01}
| select(cost.usd, operation.type, pr.repository)
```

### 3. Token 使用分析
```traceql
# 总Token使用情况
{service.name="secure-pr-guard"}
| select(cost.tokens.total)

# Prompt vs Completion Token比例
{service.name="secure-pr-guard"}
| select(cost.tokens.prompt, cost.tokens.completion, cost.tokens.total, operation.type)

# Token效率分析
{service.name="secure-pr-guard"}
| select(tokens.prompt_ratio, tokens.per_ms, operation.type)
```

### 4. 业务指标查询
```traceql
# 安全问题发现情况
{service.name="secure-pr-guard" && operation.type="nitpicker"}
| select(issues.security, issues.total, pr.repository)

# 补丁生成成功率
{service.name="secure-pr-guard" && operation.type="patch"}
| select(patch.generated, patch.issues_patched)

# 工作流程成功率
{service.name="secure-pr-guard" && span.name="pr_review.workflow"}
| select(workflow.status, cost.total_usd, latency.total_ms)
```

### 5. 错误和性能问题排查
```traceql
# 失败的操作
{service.name="secure-pr-guard" && status=error}
| select(span.name, operation.type, pr.url)

# 高延迟操作 (>3秒)
{service.name="secure-pr-guard" && latency.ms > 3000}
| select(latency.ms, operation.type, cost.tokens.total)

# 高成本操作 (>$0.005)
{service.name="secure-pr-guard" && cost.usd > 0.005}
| select(cost.usd, cost.tokens.total, operation.type, pr.repository)
```

## Grafana 面板配置

### Panel 1: Average/P95 Latency by Operation
- **查询**: `{service.name="secure-pr-guard"} | select(latency.ms) | group_by(operation.type)`
- **可视化**: Time series graph
- **聚合**: avg(), p95()
- **分组**: operation.type

### Panel 2: Total Cost by Model  
- **查询**: `{service.name="secure-pr-guard"} | select(cost.usd) | group_by(cost.model)`
- **可视化**: Stat panel / Bar chart
- **聚合**: sum(cost.usd)
- **分组**: cost.model

### Panel 3: Token Split (Prompt vs Completion)
- **查询**: `{service.name="secure-pr-guard"} | select(cost.tokens.prompt, cost.tokens.completion)`
- **可视化**: Pie chart
- **聚合**: sum() for both metrics
- **标签**: "Prompt Tokens", "Completion Tokens"

## 实用过滤器

### 按时间范围
```traceql
{service.name="secure-pr-guard" && span.start_time > 1h}
| select(cost.usd, latency.ms)
```

### 按存储库
```traceql
{service.name="secure-pr-guard" && pr.repository="owner/repo"}
| select(cost.usd, issues.security)
```

### 按风险级别
```traceql
{service.name="secure-pr-guard" && risk.level=~"high|critical"}
| select(issues.security, cost.usd, pr.url)
``` 