#!/usr/bin/env python3

import os
import time
from dotenv import load_dotenv

# Load environment
load_dotenv()

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    print("✅ OpenTelemetry imports successful")
    
    # Initialize tracer
    resource = Resource(attributes={
        "service.name": "secure-pr-guard",
        "service.version": "v2.0",
        "environment": "test"
    })
    
    provider = TracerProvider(resource=resource)
    
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTLP_ENDPOINT") + "/v1/traces",
        headers=(("Authorization", f"Bearer {os.getenv('OTLP_API_KEY')}"),),
        timeout=30
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("test-tracer")
    
    print("✅ Tracer initialized successfully")
    
    # Send test span
    with tracer.start_as_current_span("test_nitpicker_analysis") as span:
        span.set_attribute("latency_ms", 5000)
        span.set_attribute("total_tokens", 1500)
        span.set_attribute("cost_usd", 0.25)
        span.set_attribute("pr_url", "https://github.com/test/repo/pull/1")
        span.set_attribute("model", "gpt-4o-mini")
        
        print("📊 Test span created with attributes")
        time.sleep(1)  # Simulate work
    
    # Send another test span
    with tracer.start_as_current_span("test_patch_generation") as span:
        span.set_attribute("latency_ms", 7000)
        span.set_attribute("total_tokens", 2000)
        span.set_attribute("cost_usd", 0.35)
        span.set_attribute("pr_url", "https://github.com/test/repo/pull/1")
        span.set_attribute("model", "gpt-4o-mini")
        span.set_attribute("patch_generated", True)
        
        print("📊 Test patch span created")
        time.sleep(1)
    
    # Force flush
    provider.force_flush(timeout_millis=5000)
    print("✅ Spans sent to Grafana Cloud!")
    print("🔗 Endpoint:", os.getenv("OTLP_ENDPOINT"))
    print("⏰ Wait 30-60 seconds, then check Grafana Cloud Explore")
    
except ImportError as e:
    print("❌ OpenTelemetry import failed:", e)
except Exception as e:
    print("❌ Error:", e) 