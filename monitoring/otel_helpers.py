#!/usr/bin/env python3
"""
otel_helpers.py - OpenTelemetry Integration Helpers
Refactored for better testability, maintainability, and enterprise use
"""

import os
import time
import base64
from typing import Dict, Any, Optional, Union
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


@dataclass
class OTELConfig:
    """OpenTelemetry configuration"""
    service_name: str = "secure-pr-guard"
    service_version: str = "v2.1"
    environment: str = "production"
    namespace: str = "pr-automation"
    endpoint: Optional[str] = None
    username: Optional[str] = None
    api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'OTELConfig':
        """Create config from environment variables"""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "secure-pr-guard"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "v2.1"),
            environment=os.getenv("ENVIRONMENT", "production"),
            namespace=os.getenv("OTEL_NAMESPACE", "pr-automation"),
            endpoint=os.getenv("OTLP_ENDPOINT"),
            username=os.getenv("OTLP_USERNAME", "1299868"),
            api_key=os.getenv("OTLP_API_KEY")
        )


class OTELManager:
    """Manages OpenTelemetry tracing setup and lifecycle"""
    
    def __init__(self, config: Optional[OTELConfig] = None):
        self.config = config or OTELConfig.from_env()
        self.tracer = None
        self.span_processor = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize OpenTelemetry tracing"""
        if not OTEL_AVAILABLE:
            print("⚠️ OpenTelemetry not available - observability disabled")
            return False
        
        if not self.config.endpoint or not self.config.api_key:
            print("⚠️ OTEL endpoint or API key not configured - observability disabled")
            return False
        
        try:
            # Create resource
            resource = Resource(attributes={
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "deployment.environment": self.config.environment,
                "service.namespace": self.config.namespace
            })
            
            # Setup tracer provider
            provider = TracerProvider(resource=resource)
            
            # Configure exporter with authentication
            credentials = base64.b64encode(
                f"{self.config.username}:{self.config.api_key}".encode()
            ).decode()
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{self.config.endpoint}/v1/traces",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "X-Scope-OrgID": self.config.username,
                }
            )
            
            # Setup span processor
            self.span_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(self.span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(self.config.service_name)
            
            self._initialized = True
            print(f"📊 Observability: Connected to {self.config.endpoint}")
            return True
            
        except Exception as e:
            print(f"❌ OTEL initialization failed: {e}")
            return False
    
    def get_tracer(self):
        """Get the configured tracer"""
        if not self._initialized:
            return None
        return self.tracer
    
    def shutdown(self, timeout_ms: int = 5000):
        """Shutdown OTEL and flush remaining spans"""
        if self.span_processor:
            try:
                print("🔭 Flushing telemetry data...")
                self.span_processor.force_flush(timeout_millis=timeout_ms)
                print("✅ Telemetry data flushed successfully")
            except Exception as e:
                print(f"⚠️ Telemetry flush failed: {e}")


class SpanManager:
    """Manages span creation and attribute setting"""
    
    def __init__(self, tracer, pr_url: Optional[str] = None):
        self.tracer = tracer
        self.pr_metadata = self._extract_pr_metadata(pr_url) if pr_url else {}
    
    def _extract_pr_metadata(self, pr_url: str) -> Dict[str, Any]:
        """Extract standardized PR metadata from GitHub URL"""
        metadata = {"pr.url": pr_url}
        
        if pr_url and pr_url.startswith("https://github.com/"):
            try:
                parts = pr_url.rstrip('/').split('/')
                metadata.update({
                    "pr.repository": f"{parts[3]}/{parts[4]}",
                    "pr.owner": parts[3],
                    "pr.repo": parts[4],
                    "pr.number": int(parts[6])
                })
            except (IndexError, ValueError):
                pass
        
        return metadata
    
    def create_span(self, operation_name: str, operation_type: str = None):
        """Create a new span with common attributes"""
        if not self.tracer:
            return nullcontext()
        
        span = self.tracer.start_as_current_span(operation_name)
        
        # Set common attributes
        base_attributes = {
            "operation.name": operation_name,
            "workflow.start_time": datetime.now(timezone.utc).isoformat(),
            **self.pr_metadata
        }
        
        if operation_type:
            base_attributes["operation.type"] = operation_type
        
        span.set_attributes(base_attributes)
        return span
    
    def set_cost_attributes(self, span, cost_info: Dict[str, Any]):
        """Set cost-related attributes on a span"""
        if not span or not cost_info:
            return
        
        cost_attributes = {
            "cost.usd": float(cost_info.get("cost_usd", 0.0)),
            "cost.model": str(cost_info.get("model", "unknown")),
            "cost.tokens.prompt": int(cost_info.get("prompt_tokens", 0)),
            "cost.tokens.completion": int(cost_info.get("completion_tokens", 0)),
            "cost.tokens.total": int(cost_info.get("total_tokens", 0)),
        }
        
        # Add efficiency metrics
        total_tokens = cost_attributes["cost.tokens.total"]
        if total_tokens > 0:
            cost_attributes["tokens.prompt_ratio"] = round(
                cost_attributes["cost.tokens.prompt"] / total_tokens, 3
            )
        
        span.set_attributes(cost_attributes)
    
    def set_performance_attributes(self, span, start_time: float, latency_ms: Optional[int] = None):
        """Set performance-related attributes on a span"""
        if not span:
            return
        
        calculated_latency = int((time.time() - start_time) * 1000)
        actual_latency = latency_ms or calculated_latency
        
        perf_attributes = {
            "latency.ms": actual_latency,
            "latency.calculated_ms": calculated_latency,
        }
        
        # Add latency category
        if actual_latency < 1000:
            perf_attributes["latency.category"] = "fast"
        elif actual_latency < 5000:
            perf_attributes["latency.category"] = "normal"
        else:
            perf_attributes["latency.category"] = "slow"
        
        span.set_attributes(perf_attributes)
    
    def set_result_attributes(self, span, result_info: Dict[str, Any]):
        """Set result-related attributes on a span"""
        if not span or not result_info:
            return
        
        result_attributes = {}
        
        # Issues found
        if "issues" in result_info:
            issues = result_info["issues"]
            result_attributes.update({
                "issues.found": len(issues),
                "issues.security": len([i for i in issues if i.get("type") == "security"]),
                "issues.critical": len([i for i in issues if i.get("severity") == "critical"]),
                "issues.high": len([i for i in issues if i.get("severity") == "high"]),
            })
        
        # Summary information
        if "summary" in result_info:
            summary = result_info["summary"]
            if "risk_level" in summary:
                result_attributes["risk.level"] = summary["risk_level"]
                # Convert risk level to numeric score
                risk_scores = {"low": 1, "medium": 4, "high": 7, "critical": 10}
                result_attributes["risk.score"] = risk_scores.get(summary["risk_level"], 0)
        
        # Analysis summary
        if "analysis_summary" in result_info:
            analysis = result_info["analysis_summary"]
            result_attributes.update({
                "issues.ai_detected": analysis.get("ai_detected", 0),
                "issues.rule_detected": analysis.get("rule_detected", 0),
            })
        
        span.set_attributes(result_attributes)
    
    def set_error_attributes(self, span, error: Exception, error_context: str = ""):
        """Set error-related attributes and status on a span"""
        if not span:
            return
        
        error_attributes = {
            "error.type": type(error).__name__,
            "error.message": str(error),
            "error.context": error_context,
            "error.timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        span.set_attributes(error_attributes)
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))


class OTELInstrumentor:
    """High-level instrumentor for PR Guard operations"""
    
    def __init__(self, pr_url: Optional[str] = None):
        self.otel_manager = OTELManager()
        self.initialized = self.otel_manager.initialize()
        self.span_manager = SpanManager(self.otel_manager.get_tracer(), pr_url) if self.initialized else None
    
    def instrument_operation(self, operation_name: str, operation_type: str = None):
        """Decorator/context manager for instrumenting operations"""
        return OperationInstrumentor(self.span_manager, operation_name, operation_type)
    
    def shutdown(self):
        """Shutdown OTEL"""
        if self.otel_manager:
            self.otel_manager.shutdown()


class OperationInstrumentor:
    """Context manager for individual operations"""
    
    def __init__(self, span_manager: Optional[SpanManager], operation_name: str, operation_type: str = None):
        self.span_manager = span_manager
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.span = None
        self.start_time = None
    
    def __enter__(self):
        if self.span_manager:
            self.start_time = time.time()
            self.span = self.span_manager.create_span(self.operation_name, self.operation_type)
            if hasattr(self.span, '__enter__'):
                self.span = self.span.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span and self.span_manager:
            # Set performance attributes
            if self.start_time:
                self.span_manager.set_performance_attributes(self.span, self.start_time)
            
            # Handle errors
            if exc_type:
                self.span_manager.set_error_attributes(self.span, exc_val, f"Error in {self.operation_name}")
            
            # Exit span context
            if hasattr(self.span, '__exit__'):
                self.span.__exit__(exc_type, exc_val, exc_tb)
    
    def set_cost_info(self, cost_info: Dict[str, Any]):
        """Set cost information on the current span"""
        if self.span and self.span_manager:
            self.span_manager.set_cost_attributes(self.span, cost_info)
    
    def set_result_info(self, result_info: Dict[str, Any]):
        """Set result information on the current span"""
        if self.span and self.span_manager:
            self.span_manager.set_result_attributes(self.span, result_info)
    
    def set_custom_attributes(self, attributes: Dict[str, Any]):
        """Set custom attributes on the current span"""
        if self.span:
            self.span.set_attributes(attributes)


# Convenience functions for backward compatibility
def create_otel_instrumentor(pr_url: Optional[str] = None) -> OTELInstrumentor:
    """Create an OTEL instrumentor for PR Guard operations"""
    return OTELInstrumentor(pr_url)


def instrument_workflow(pr_url: str):
    """Create workflow-level instrumentor"""
    instrumentor = OTELInstrumentor(pr_url)
    return instrumentor.instrument_operation("pr_review.workflow", "workflow")


# Global instrumentor for backward compatibility
_global_instrumentor = None

def get_global_instrumentor() -> Optional[OTELInstrumentor]:
    """Get or create global instrumentor"""
    global _global_instrumentor
    if _global_instrumentor is None:
        _global_instrumentor = OTELInstrumentor()
    return _global_instrumentor


def shutdown_otel():
    """Shutdown global OTEL"""
    global _global_instrumentor
    if _global_instrumentor:
        _global_instrumentor.shutdown()
        _global_instrumentor = None


if __name__ == "__main__":
    # Test the OTEL helpers
    print("🧪 Testing OTEL Helpers")
    
    instrumentor = create_otel_instrumentor("https://github.com/test/repo/pull/123")
    
    with instrumentor.instrument_operation("test.operation", "test") as op:
        time.sleep(0.1)  # Simulate work
        
        op.set_cost_info({
            "cost_usd": 0.001234,
            "model": "gpt-4o-mini",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        })
        
        op.set_result_info({
            "issues": [{"type": "security", "severity": "high"}],
            "summary": {"risk_level": "medium"}
        })
    
    instrumentor.shutdown()
    print("✅ OTEL test completed")