import os
import time
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

load_dotenv()

# 初始化
resource = Resource(attributes={
    "service.name": "secure-pr-guard",
    "service.version": "1.0.0",
    "deployment.environment": "test"
})

provider = TracerProvider(resource=resource)

otlp_exporter = OTLPSpanExporter(
    endpoint=f"{os.getenv('OTLP_ENDPOINT')}/v1/traces",
    headers=(("Authorization", f"Bearer {os.getenv('OTLP_API_KEY')}"),),
)

provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

print("🧪 Testing Grafana Cloud connection...")

# 发送测试数据
for i in range(3):
    with tracer.start_as_current_span("test_operation") as span:
        # 模拟不同的操作
        operation = ["nitpicker", "architect", "patch_generation"][i]
        span.set_attribute("operation", operation)
        
        # 模拟性能数据
        latency = 100 + i * 50
        tokens = 500 + i * 200
        cost = round(0.01 + i * 0.005, 4)
        
        span.set_attribute("latency_ms", latency)
        span.set_attribute("tokens", tokens)
        span.set_attribute("cost_usd", cost)
        
        print(f"✅ Sent test span {i+1}: {operation} (latency={latency}ms, tokens={tokens}, cost=${cost})")
        time.sleep(1)

print("\n⏳ Waiting for data to appear in Grafana...")
print("📊 Go to Grafana Cloud → Explore → Select 'grafanacloud-siwenwang0803-traces'")
print("🔍 Search for service: secure-pr-guard")