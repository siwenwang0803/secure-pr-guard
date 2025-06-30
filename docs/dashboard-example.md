# Grafana Cloud 仪表盘示例

## 📊 实时可观测性仪表盘

### 仪表盘概览
```
Dashboard: "Secure-PR-Guard Observability"
Service: secure-pr-guard v2.0
Environment: production
```

### 核心指标展示

#### 1. 平均延迟趋势图 (Time Series)
```
Current Values:
- Nitpicker Analysis: 6.8s avg
- Patch Generation: 8.0s avg
- Total Pipeline: 14.8s avg

Trend: Stable over last 24h
```

#### 2. Token 使用统计 (Stat Panel)
```
Current Session:
- Total Tokens: 2,300
- Prompt Tokens: 1,586 (69%)
- Completion Tokens: 714 (31%)

Daily Average: 1,850 tokens/operation
```

#### 3. 成本分析柱状图 (Bar Chart)
```
Cost Breakdown:
- Nitpicker: $0.131 (38%)
- Patch Gen: $0.214 (62%)
- Total: $0.345

Monthly Budget: On track (< $50/month)
```

### 关键 KPI 总结
- **平均成本**: $0.31 per PR review
- **响应时间**: 14.8 seconds end-to-end
- **Token 效率**: 70% prompt, 30% completion
- **成功率**: 95% (patches + comments)

## 📈 性能指标
```
Metrics exported to: otlp-gateway-prod-us-west-0.grafana.net
Traces: ✅ Active
Spans: nitpicker_analysis, patch_generation
Attributes: latency_ms, total_tokens, cost_usd, pr_url
```

*注意: 实际截图需要在你的 Grafana Cloud 实例中创建仪表盘后生成* 