import os
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    if os.getenv("OTLP_ENDPOINT"):
        resource = Resource(attributes={
            "service.name": "secure-pr-guard-test",
            "service.version": "v2.0"
        })
        
        provider = TracerProvider(resource=resource)
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_ENDPOINT") + "/v1/traces",
            headers=(("Authorization", f"Bearer {os.getenv('OTLP_API_KEY')}"),),
        )
        
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("test")
        
        print("📊 Testing Grafana Cloud connection...")
        
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test_metric", 123)
            span.set_attribute("latency_ms", 1500)
            span.set_attribute("cost_usd", 0.05)
            time.sleep(0.1)  # Simulate work
        
        print("✅ Test span sent to Grafana Cloud")
        time.sleep(2)  # Wait for export
        
    else:
        print("❌ OTLP_ENDPOINT not configured")
        
except Exception as e:
    print(f"❌ Error: {e}")
