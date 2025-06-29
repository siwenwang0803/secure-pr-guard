#!/usr/bin/env python3
"""
Test script to verify cost attributes are sent to Grafana Cloud
"""

import os
import time
from dotenv import load_dotenv

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

load_dotenv()

def setup_telemetry():
    """Setup OpenTelemetry with cost tracking attributes"""
    resource = Resource(attributes={
        "service.name": "secure-pr-guard",
        "service.version": "v2.0-test",
        "deployment.environment": "test",
        "service.namespace": "pr-automation-test"
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
    
    # Store processor for flush
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer("secure-pr-guard-test"), span_processor

def test_cost_attributes():
    """Test sending cost attributes to Grafana"""
    tracer, processor = setup_telemetry()
    
    print("🧪 Testing cost attributes telemetry...")
    
    # Create a workflow span with cost attributes
    with tracer.start_as_current_span("test.workflow") as workflow_span:
        workflow_span.set_attributes({
            "workflow.name": "secure_pr_guard_test",
            "workflow.version": "2.0",
            "pr.url": "https://github.com/test/repo/pull/123",
            "pr.repository": "test/repo",
            "pr.number": 123
        })
        
        # Simulate nitpicker analysis
        with tracer.start_as_current_span("nitpicker.analyze") as nitpicker_span:
            # Simulate processing time
            time.sleep(0.1)
            
            # Set ALL cost attributes
            nitpicker_span.set_attributes({
                # Operation metadata
                "operation.type": "nitpicker",
                "operation.name": "analyze_code_security",
                
                # Cost metrics (KEY ATTRIBUTES)
                "cost.usd": 0.001234,
                "cost.model": "gpt-4o-mini",
                "cost.tokens.prompt": 150,
                "cost.tokens.completion": 50,
                "cost.tokens.total": 200,
                
                # Performance metrics
                "latency.ms": 1200,
                "latency.api_ms": 1100,
                
                # Issue metrics
                "issues.found": 5,
                "issues.security": 2,
                "issues.ai_detected": 3,
                "issues.rule_detected": 2,
                
                # PR context
                "pr.url": "https://github.com/test/repo/pull/123",
                "pr.repository": "test/repo",
                "pr.number": 123,
                
                # Efficiency metrics
                "tokens.prompt_ratio": 0.75,
                "tokens.per_ms": 0.167
            })
            
            print("✅ Nitpicker span created with cost attributes")
        
        # Simulate patch generation
        with tracer.start_as_current_span("patch.generate") as patch_span:
            time.sleep(0.05)
            
            patch_span.set_attributes({
                # Operation metadata
                "operation.type": "patch",
                "operation.name": "generate_safe_patches",
                
                # Cost metrics (KEY ATTRIBUTES)
                "cost.usd": 0.000567,
                "cost.model": "gpt-4o-mini",
                "cost.tokens.prompt": 80,
                "cost.tokens.completion": 30,
                "cost.tokens.total": 110,
                
                # Performance metrics
                "latency.ms": 800,
                "latency.api_ms": 750,
                
                # Patch metrics
                "patch.generated": True,
                "patch.issues_total": 5,
                "patch.issues_safe": 3,
                "patch.issues_patched": 3,
                
                # PR context
                "pr.url": "https://github.com/test/repo/pull/123",
                "pr.repository": "test/repo",
                "pr.number": 123
            })
            
            print("✅ Patch span created with cost attributes")
        
        # Set workflow summary
        workflow_span.set_attributes({
            # Total metrics
            "cost.total_usd": 0.001801,
            "cost.tokens.total": 310,
            "latency.total_ms": 2000,
            
            # Workflow status
            "workflow.status": "success",
            "issues.total": 5,
            "issues.security": 2,
            "patch.created": True,
            "comment.posted": True
        })
        
        print("✅ Workflow span completed with summary")
    
    # Force flush to ensure spans are sent
    print("🔭 Force flushing spans to Grafana Cloud...")
    processor.force_flush(timeout_millis=10000)
    print("✅ Spans flushed successfully")
    
    # Additional wait to ensure delivery
    time.sleep(3)
    
    print("\n📊 Test completed! Check Grafana Cloud for:")
    print("   - Service: secure-pr-guard")
    print("   - Spans: test.workflow, nitpicker.analyze, patch.generate")
    print("   - Attributes: cost.usd, cost.tokens.total, latency.ms")
    print("\n🔍 TraceQL Query to verify:")
    print('   {service.name="secure-pr-guard"} | select(cost.usd, cost.tokens.total, latency.ms)')

if __name__ == "__main__":
    test_cost_attributes() 