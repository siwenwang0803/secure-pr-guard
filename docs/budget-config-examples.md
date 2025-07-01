# 🛡️ Budget Configuration Examples

## Quick Configuration Presets

### 🧪 Development/Testing (Current - Sensitive Detection)
```yaml
daily_limit: 2.0           # $2/day - Catch every anomaly
hourly_limit: 0.5          # $0.5/hour - Immediate feedback
warning_threshold: 0.7     # 70% warning
critical_threshold: 0.9    # 90% critical
```
**Use case:** Development, testing, demo purposes

### 🏢 Small Team (10-20 developers)
```yaml
daily_limit: 25.0          # $25/day 
hourly_limit: 5.0          # $5/hour
warning_threshold: 0.8     # 80% warning
critical_threshold: 0.95   # 95% critical
```
**Use case:** Startup, small engineering teams

### 🏭 Enterprise (50+ developers)
```yaml
daily_limit: 100.0         # $100/day
hourly_limit: 20.0         # $20/hour  
warning_threshold: 0.85    # 85% warning
critical_threshold: 0.95   # 95% critical
```
**Use case:** Large enterprises, high-volume CI/CD

### 🚀 High-Performance (ML/AI Teams)
```yaml
daily_limit: 500.0         # $500/day
hourly_limit: 50.0         # $50/hour
spike_threshold: 15.0      # 15x spike tolerance
efficiency_min: 0.30       # $0.30/1K tokens
```
**Use case:** AI research teams, heavy model usage

## 🎛️ Configuration Management

### Dynamic Configuration Updates
```bash
# Update budget limits without restart
docker-compose exec budget-guard python monitoring/budget_guard.py \
  --update-config daily_limit=50.0 hourly_limit=10.0

# Apply preset configuration
docker-compose exec budget-guard python monitoring/budget_guard.py \
  --apply-preset enterprise

# Temporary budget override (emergency)
docker-compose exec budget-guard python monitoring/budget_guard.py \
  --emergency-override 24h
```

### Environment-Based Configuration
```bash
# Development
export BUDGET_PRESET=development

# Staging  
export BUDGET_PRESET=small_team

# Production
export BUDGET_PRESET=enterprise
```

## 📊 Smart Recommendations

The system automatically suggests optimal thresholds based on:
- **Historical usage patterns**
- **Team size and activity**
- **Cost efficiency trends**
- **Peak usage times**

### Auto-Tuning Features
- 📈 **Learning mode**: Observe for 7 days, suggest optimal limits
- 🎯 **Efficiency optimization**: Automatically adjust based on cost/performance
- 🚨 **Anomaly detection**: Smart spike detection vs. normal usage growth
- 📅 **Scheduled adjustments**: Different limits for business hours vs. weekends

## 🎪 Demo Value

**Current sensitive configuration is perfect for demonstrations because:**
- ✅ Shows immediate system response
- ✅ Displays rich monitoring data  
- ✅ Proves real-time budget enforcement
- ✅ Demonstrates configuration flexibility