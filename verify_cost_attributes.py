#!/usr/bin/env python3
"""
Verify Cost Attributes in Grafana Cloud
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

load_dotenv()

def setup_telemetry():
    """Setup OpenTelemetry"""
    resource = Resource(attributes={
        "service.name": "secure-pr-guard",
        "service.version": "v2.0-verify",
        "deployment.environment": "test"
    })
    
    provider = TracerProvider(resource=resource)
    
    # Grafana Cloud Basic Auth
    import base64
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
    
    return trace.get_tracer("secure-pr-guard-verify"), span_processor

def send_test_span_with_cost():
    """Send a test span with cost attributes"""
    tracer, processor = setup_telemetry()
    
    print("🧪 Sending test span with cost attributes...")
    
    with tracer.start_as_current_span("cost.verification.test") as span:
        # Set cost attributes with explicit values
        span.set_attributes({
            # Cost metrics - KEY ATTRIBUTES FOR VERIFICATION
            "cost.usd": 0.123456,
            "cost.model": "gpt-4o-mini",
            "cost.tokens.prompt": 500,
            "cost.tokens.completion": 150,
            "cost.tokens.total": 650,
            
            # Performance metrics
            "latency.ms": 2500,
            "latency.api_ms": 2300,
            
            # Operation info
            "operation.type": "verification",
            "operation.name": "cost_attribute_test",
            
            # Test metadata
            "test.timestamp": datetime.now().isoformat(),
            "test.purpose": "verify_cost_attributes_visible",
            
            # PR context for filtering
            "pr.url": "https://github.com/test/verify/pull/999",
            "pr.repository": "test/verify",
            "pr.number": 999
        })
        
        print("✅ Test span created with cost attributes")
        
        # Simulate some work
        time.sleep(0.1)
    
    # Force flush
    print("🔭 Force flushing to Grafana Cloud...")
    processor.force_flush(timeout_millis=10000)
    
    return datetime.now()

def main():
    """Send test data and provide verification instructions"""
    print("🔍 Cost Attributes Verification Tool")
    print("=" * 50)
    
    # Send test span
    timestamp = send_test_span_with_cost()
    
    print("✅ Test span sent successfully!")
    print(f"🕐 Timestamp: {timestamp.isoformat()}")
    print()
    
    print("📋 HOW TO VERIFY IN GRAFANA CLOUD:")
    print("=" * 50)
    print()
    
    print("1️⃣ BASIC SEARCH:")
    print("   - Go to Grafana Cloud → Explore → Tempo")
    print("   - Query: {service.name=\"secure-pr-guard\"}")
    print("   - Look for spans from the last few minutes")
    print()
    
    print("2️⃣ VERIFY COST ATTRIBUTES:")
    print("   在TraceQL中运行以下查询:")
    print()
    print("   # 查看所有cost attributes")
    print("   {service.name=\"secure-pr-guard\"} | select(cost.usd, cost.tokens.total)")
    print()
    print("   # 查看具体的cost值")
    print("   {service.name=\"secure-pr-guard\" && cost.usd > 0}")
    print()
    print("   # 查看verification测试span")
    print("   {service.name=\"secure-pr-guard\" && operation.type=\"verification\"}")
    print()
    
    print("3️⃣ CLICK SPAN FOR DETAILS:")
    print("   - 点击任意span (如 nitpicker.analyze)")
    print("   - 在右侧panel中向下滚动")
    print("   - 查看 'Attributes' 或 'Tags' 部分")
    print("   - 你应该看到:")
    print("     • cost.usd: 0.123456")
    print("     • cost.tokens.total: 650") 
    print("     • cost.tokens.prompt: 500")
    print("     • latency.ms: 2500")
    print()
    
    print("4️⃣ 如果还是看不到cost attributes:")
    print("   - 确保选择了正确的时间范围")
    print("   - 尝试刷新页面")
    print("   - 检查span是否确实包含attributes")
    print()
    
    print("🔍 EXPECTED RESULTS:")
    print("   - cost.usd = 0.123456")
    print("   - cost.tokens.total = 650")
    print("   - latency.ms = 2500")
    print("   - operation.type = verification")
    print()
    
    print("💡 TROUBLESHOOTING:")
    print("   如果attributes仍然不可见，可能是:")
    print("   - Grafana Cloud UI需要点击具体span查看")
    print("   - 使用TraceQL查询而不是UI浏览")
    print("   - 等待几分钟让数据传播")

if __name__ == "__main__":
    main() 