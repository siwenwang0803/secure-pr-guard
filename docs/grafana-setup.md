# Grafana Cloud 可观测性设置指南

## 📊 创建 Secure-PR-Guard 仪表盘

### 1. 访问 Grafana Cloud
1. 登录你的 Grafana Cloud 账户
2. 导航到 **Dashboards** → **New** → **New Dashboard**

### 2. 图表 1: 平均延迟监控
```
Panel Type: Time Series
Title: "AI Analysis Latency (Average)"
Query: 
  - Service: secure-pr-guard
  - Span Name: nitpicker_analysis, patch_generation
  - Metric: latency_ms
  - Aggregation: avg()
Unit: milliseconds (ms)
```

### 3. 图表 2: Token 使用量统计
```
Panel Type: Stat
Title: "Token Usage (Total)"
Query:
  - Service: secure-pr-guard
  - Span Name: nitpicker_analysis, patch_generation
  - Metric: total_tokens
  - Aggregation: sum()
Unit: tokens
```

### 4. 图表 3: 成本分析
```
Panel Type: Bar Chart
Title: "Cost Breakdown by Operation"
Query:
  - Service: secure-pr-guard
  - Span Name: nitpicker_analysis, patch_generation
  - Metric: cost_usd
  - Group by: span.name
Unit: currency (USD)
```

### 5. 预期指标范围
基于我们的测试运行：
- **平均延迟**: 6-8 秒
- **Token 使用**: 800-1500 per operation
- **成本**: $0.13-0.21 per operation

### 6. 告警设置 (可选)
```
Alert Rule: "High Cost Alert"
Condition: cost_usd > 0.50 for any operation
Notification: Email/Slack
```

## 🎯 关键 KPI 示例
完成后你可以向面试官展示：
- "我的 Agent 一次审查平均花 $0.31、延迟 14.8 秒"
- "Token 效率: 70.3% prompt tokens, 29.7% completion"
- "成本分布: Nitpicker 38%, Patch Gen 62%" 