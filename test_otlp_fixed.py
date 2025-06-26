#!/usr/bin/env python3

import os
import time
import base64
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
    
    # Get credentials
    endpoint = os.getenv("OTLP_ENDPOINT")
    api_key = os.getenv("OTLP_API_KEY")
    
    print(f"🔗 Endpoint: {endpoint}")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    # Initialize tracer with correct auth
    resource = Resource(attributes={
        "service.name": "secure-pr-guard",
        "service.version": "v2.0",
        "environment": "test"
    })
    
    provider = TracerProvider(resource=resource)
    
    # Try different auth methods
    
    # Method 1: Bearer token (原来的方法)
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/x-protobuf"
            },
            timeout=30
        )
        
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("test-tracer")
        
        print("✅ Method 1: Bearer token auth")
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
        
        # Method 2: Basic auth (instance_id:api_key)
        try:
            # Extract instance ID from endpoint
            instance_id = endpoint.split("//")[1].split(".")[0].replace("otlp-gateway-", "")
            auth_string = f"{instance_id}:{api_key}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{endpoint}/v1/traces",
                headers={
                    "Authorization": f"Basic {encoded_auth}",
                    "Content-Type": "application/x-protobuf"
                },
                timeout=30
            )
            
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(provider)
            tracer = trace.get_tracer("test-tracer")
            
            print("✅ Method 2: Basic auth")
            
        except Exception as e2:
            print(f"❌ Method 2 failed: {e2}")
            
            # Method 3: Simple API key header
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{endpoint}/v1/traces",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/x-protobuf"
                },
                timeout=30
            )
            
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(provider)
            tracer = trace.get_tracer("test-tracer")
            
            print("✅ Method 3: X-API-Key header")
    
    # Send test span
    print("📊 Sending test spans...")
    
    with tracer.start_as_current_span("test_nitpicker_analysis") as span:
        span.set_attribute("latency_ms", 5000)
        span.set_attribute("total_tokens", 1500)
        span.set_attribute("cost_usd", 0.25)
        span.set_attribute("pr_url", "https://github.com/test/repo/pull/1")
        span.set_attribute("model", "gpt-4o-mini")
        
        print("  📋 Nitpicker span created")
        time.sleep(0.5)
    
    with tracer.start_as_current_span("test_patch_generation") as span:
        span.set_attribute("latency_ms", 7000)
        span.set_attribute("total_tokens", 2000)
        span.set_attribute("cost_usd", 0.35)
        span.set_attribute("patch_generated", True)
        
        print("  🛠️ Patch span created")
        time.sleep(0.5)
    
    # Force flush
    print("📤 Flushing spans...")
    provider.force_flush(timeout_millis=10000)
    
    print("✅ Test completed!")
    print("⏰ Wait 1-2 minutes, then check Grafana Cloud")
    
except ImportError as e:
    print("❌ Import failed:", e)
except Exception as e:
    print("❌ Unexpected error:", e)
    import traceback
    traceback.print_exc() 