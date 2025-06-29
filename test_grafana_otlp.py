"""
Test Grafana Cloud OTLP connection with proper authentication
"""

import os
import time
import base64
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Load environment variables
load_dotenv()

def test_grafana_cloud_otlp():
    """Test OTLP connection to Grafana Cloud"""
    
    print("🔍 Testing Grafana Cloud OpenTelemetry Configuration")
    print("=" * 50)
    
    # Configuration
    endpoint = os.getenv("OTLP_ENDPOINT", "https://otlp-gateway-prod-us-west-0.grafana.net/otlp")
    username = os.getenv("OTLP_USERNAME", "1251973")  # From your screenshot
    api_key = os.getenv("OTLP_API_KEY")
    
    print(f"OTLP Endpoint: {endpoint}")
    print(f"Username: {username}")
    print(f"API Key: {api_key[:20]}...{api_key[-10:] if api_key else 'Not set'}")
    print("=" * 50)
    
    # Create Basic Auth credentials
    credentials = base64.b64encode(f"{username}:{api_key}".encode()).decode()
    
    try:
        # Create resource
        resource = Resource.create({
            "service.name": "secure-pr-guard-test",
            "service.version": "1.0.0",
            "deployment.environment": "test"
        })
        
        # Setup tracer
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter with Basic Auth
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers={
                "Authorization": f"Basic {credentials}",
                "X-Scope-OrgID": username,  # Sometimes required by Grafana
            }
        )
        
        # Add span processors
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
        # Set tracer provider
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)
        
        # Create test spans
        print("\n📤 Sending test traces...")
        
        with tracer.start_as_current_span("test_grafana_connection") as span:
            span.set_attributes({
                "test.timestamp": time.time(),
                "test.message": "Hello from secure-pr-guard",
                "test.environment": "development"
            })
            
            # Create a child span
            with tracer.start_as_current_span("test_child_operation") as child_span:
                child_span.set_attributes({
                    "operation.type": "test",
                    "operation.name": "connection_test"
                })
                time.sleep(0.1)  # Simulate some work
        
        # Force flush to ensure export
        print("⏳ Flushing spans...")
        provider.force_flush()
        
        print("✅ Traces sent successfully!")
        print("\n📊 Check your Grafana Cloud:")
        print(f"   1. Go to: https://siwenwang0803.grafana.net/")
        print("   2. Navigate to Explore")
        print("   3. Select 'grafanacloud-siwenwang0803-traces' data source")
        print("   4. Search for: service.name='secure-pr-guard-test'")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify your API key is correct")
        print("   2. Check if your Grafana Cloud instance is active")
        print("   3. Try regenerating the API token")

def test_alternative_auth():
    """Test alternative authentication methods"""
    
    print("\n\n🔐 Testing Alternative Authentication")
    print("=" * 50)
    
    endpoint = os.getenv("OTLP_ENDPOINT")
    api_key = os.getenv("OTLP_API_KEY")
    
    # Test direct API key as password
    try:
        resource = Resource.create({"service.name": "auth-test-direct"})
        provider = TracerProvider(resource=resource)
        
        # Use API key directly as Bearer token
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers={
                "Authorization": f"Bearer {api_key}",
            }
        )
        
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("auth_test_bearer"):
            pass
            
        provider.force_flush()
        print("✅ Bearer token auth test completed")
        
    except Exception as e:
        print(f"❌ Bearer token auth failed: {str(e)}")

if __name__ == "__main__":
    # Test main connection
    test_grafana_cloud_otlp()
    
    # Test alternative auth
    test_alternative_auth()
    
    print("\n\n📝 Next Steps:")
    print("1. If still getting 401, regenerate your Grafana Cloud API token")
    print("2. Make sure the token has 'MetricsPublisher' role")
    print("3. Check https://grafana.com/orgs/siwenwang0803/api-keys")