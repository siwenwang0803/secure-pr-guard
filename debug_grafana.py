#!/usr/bin/env python3
"""
Grafana Tempo Debug Script
Debug OTEL trace delivery and query issues
"""

import os
import json
import time
import requests
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv()

def check_environment():
    """检查OTEL环境变量配置"""
    print("🔧 Environment Configuration Check")
    print("=" * 50)
    
    required_vars = {
        "OTLP_ENDPOINT": os.getenv("OTLP_ENDPOINT"),
        "OTLP_USERNAME": os.getenv("OTLP_USERNAME"),
        "OTLP_API_KEY": os.getenv("OTLP_API_KEY"),
    }
    
    for var, value in required_vars.items():
        status = "✅ SET" if value else "❌ MISSING"
        print(f"  {var}: {status}")
        if value and var != "OTLP_API_KEY":
            print(f"    Value: {value}")
        elif value and var == "OTLP_API_KEY":
            print(f"    Value: {value[:8]}...")
    
    return all(required_vars.values())

def test_tempo_connection():
    """测试Grafana Cloud Tempo连接"""
    print("\n🌐 Testing Tempo Connection")
    print("=" * 50)
    
    endpoint = os.getenv("OTLP_ENDPOINT")
    username = os.getenv("OTLP_USERNAME", "1299868")
    password = os.getenv("OTLP_API_KEY")
    
    if not all([endpoint, username, password]):
        print("❌ Missing required environment variables")
        return False
    
    # Create authorization header
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "X-Scope-OrgID": username,
        "Content-Type": "application/x-protobuf"
    }
    
    # Test endpoint connectivity
    test_url = f"{endpoint}/v1/traces"
    
    try:
        print(f"📡 Testing endpoint: {test_url}")
        
        # Just test if endpoint is reachable (don't send actual data)
        response = requests.head(test_url, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 400, 401, 405]:  # 405 = Method Not Allowed is expected for HEAD
            print("✅ Endpoint is reachable")
            return True
        else:
            print("❌ Endpoint unreachable or misconfigured")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def send_test_trace():
    """发送测试trace到Tempo"""
    print("\n🧪 Sending Test Trace")
    print("=" * 50)
    
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # Create resource
        resource = Resource(attributes={
            "service.name": "secure-pr-guard-debug",
            "service.version": "debug",
            "deployment.environment": "test",
            "service.namespace": "pr-automation"
        })
        
        # Setup tracer
        provider = TracerProvider(resource=resource)
        
        username = os.getenv("OTLP_USERNAME", "1299868")
        password = os.getenv("OTLP_API_KEY")
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_ENDPOINT") + "/v1/traces",
            headers={
                "Authorization": f"Basic {credentials}",
                "X-Scope-OrgID": username,
            }
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("secure-pr-guard-debug")
        
        # Create test span with all your attributes
        print("📤 Creating test span...")
        with tracer.start_as_current_span("debug.test") as span:
            span.set_attributes({
                # Test all your key attributes
                "operation.type": "debug",
                "operation.name": "test_trace",
                "cost.usd": 0.001234,
                "cost.model": "gpt-4o-mini",
                "cost.tokens.prompt": 100,
                "cost.tokens.completion": 50,
                "cost.tokens.total": 150,
                "latency.ms": 1500,
                "pr.url": "https://github.com/test/test/pull/1",
                "pr.repository": "test/test",
                "pr.number": 1,
                "issues.found": 5,
                "risk.level": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            print("   ✅ Span created with test attributes")
            time.sleep(0.1)  # Small delay
        
        # Force flush
        print("📡 Flushing spans to Tempo...")
        span_processor.force_flush(timeout_millis=10000)
        print("   ✅ Flush completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test trace failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_grafana_queries():
    """提供Grafana查询建议"""
    print("\n📊 Grafana Query Suggestions")
    print("=" * 50)
    
    queries = [
        {
            "name": "Find all secure-pr-guard traces",
            "query": '{resource.service.name="secure-pr-guard"}',
            "description": "基础查询 - 查找所有PR Guard的traces"
        },
        {
            "name": "Find debug traces",
            "query": '{resource.service.name="secure-pr-guard-debug"}',
            "description": "查找刚才发送的测试traces"
        },
        {
            "name": "Cost analysis",
            "query": '{resource.service.name="secure-pr-guard"} | select(span.cost.usd)',
            "description": "成本分析 - 选择包含成本的spans"
        },
        {
            "name": "Performance analysis", 
            "query": '{resource.service.name="secure-pr-guard"} | select(span.latency.ms)',
            "description": "性能分析 - 选择包含延迟的spans"
        },
        {
            "name": "Recent traces (last 1h)",
            "query": '{resource.service.name="secure-pr-guard"} && duration > 0ms',
            "description": "最近1小时的traces"
        },
        {
            "name": "Traces with attributes",
            "query": '{resource.service.name="secure-pr-guard"} | select(span.cost.usd, span.latency.ms, span.operation.type)',
            "description": "选择特定属性的traces"
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query['name']}")
        print(f"   Query: {query['query']}")
        print(f"   用途: {query['description']}")
        print()

def debug_trace_attributes():
    """分析你代码中的trace属性"""
    print("\n🔍 Trace Attributes Analysis")
    print("=" * 50)
    
    # 从你的代码中提取的关键属性
    key_attributes = [
        "cost.usd",
        "cost.model", 
        "cost.tokens.prompt",
        "cost.tokens.completion",
        "cost.tokens.total",
        "latency.ms",
        "latency.api_ms",
        "operation.type",
        "operation.name",
        "pr.url",
        "pr.repository", 
        "pr.number",
        "issues.found",
        "issues.security",
        "risk.level",
        "patch.created"
    ]
    
    print("📋 Key attributes that should appear in Grafana:")
    for attr in key_attributes:
        print(f"   - span.{attr}")
    
    print(f"\n🎯 总共 {len(key_attributes)} 个关键属性")
    print("如果这些属性在Grafana中不可见，可能的原因：")
    print("1. Traces还没有到达Tempo (网络/权限问题)")
    print("2. Grafana查询语法错误")
    print("3. 时间范围设置问题")
    print("4. Grafana Cloud免费版限制")

def main():
    """主测试流程"""
    print("🚀 Grafana Tempo Debug Tool")
    print("=" * 60)
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix configuration.")
        return
    
    # Step 2: Test connection
    if not test_tempo_connection():
        print("\n❌ Connection test failed. Check endpoint and credentials.")
        return
    
    # Step 3: Send test trace
    if not send_test_trace():
        print("\n❌ Test trace failed. Check OTEL configuration.")
        return
    
    # Step 4: Provide query suggestions
    check_grafana_queries()
    
    # Step 5: Attribute analysis
    debug_trace_attributes()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. 等待2-3分钟让traces传输到Grafana")
    print("2. 在Grafana Explore中使用上面的查询")
    print("3. 检查时间范围是否正确 (last 1 hour)")
    print("4. 如果还是看不到，可能是Grafana Cloud免费版限制")
    print("=" * 60)

if __name__ == "__main__":
    main()