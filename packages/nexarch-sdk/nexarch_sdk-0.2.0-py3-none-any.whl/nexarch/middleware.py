"""Nexarch Middleware"""
import time
import traceback
import uuid
import threading
from datetime import datetime
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .loggers import NexarchLogger
from .models import SpanData, ErrorData
from .tracing import set_trace_context, clear_trace_context, Span, Sampler
from .queue import get_log_queue
from .auto_discovery import ArchitectureDiscovery, DependencyMapper, TrafficAnalyzer


class NexarchMiddleware(BaseHTTPMiddleware):
    """Captures all requests and auto-discovers architecture"""
    
    # Class-level instances for architecture discovery
    _discovery: Optional[ArchitectureDiscovery] = None
    _dependency_mapper: DependencyMapper = DependencyMapper()
    _traffic_analyzer: TrafficAnalyzer = TrafficAnalyzer()
    _discovery_sent: bool = False
    _discovery_lock: threading.Lock = threading.Lock()
    
    def __init__(
        self,
        app,
        api_key: str,
        environment: str = "production",
        sampling_rate: float = 1.0,
        service_name: Optional[str] = None,
        enable_auto_discovery: bool = True
    ):
        super().__init__(app)
        self.api_key = api_key
        self.environment = environment
        self.service_name = service_name or environment
        self.sampler = Sampler(sampling_rate)
        self.enable_auto_discovery = enable_auto_discovery
        
        # Initialize architecture discovery
        if enable_auto_discovery and not NexarchMiddleware._discovery:
            NexarchMiddleware._discovery = ArchitectureDiscovery(app, self.service_name)
            # Run discovery on startup
            self._run_discovery()
    
    def _run_discovery(self):
        """Run architecture auto-discovery and send to backend"""
        with NexarchMiddleware._discovery_lock:
            try:
                if NexarchMiddleware._discovery and not NexarchMiddleware._discovery_sent:
                    discovery_data = NexarchMiddleware._discovery.discover_all()
                    
                    # Enqueue discovery data
                    get_log_queue().enqueue({
                        "type": "architecture_discovery",
                        "timestamp": datetime.now().isoformat(),
                        "data": discovery_data
                    })
                    
                    NexarchMiddleware._discovery_sent = True
                    print(f"[Nexarch] Architecture discovery completed: {len(discovery_data.get('endpoints', []))} endpoints discovered")
            except Exception as e:
                print(f"[Nexarch] Warning: Architecture discovery failed: {e}")
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """Intercept and log"""
        
        # Skip internal
        if request.url.path.startswith("/__nexarch"):
            return await call_next(request)
        
        # Sampling decision
        if not self.sampler.should_sample():
            return await call_next(request)
        
        # Generate IDs
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        # Set context
        set_trace_context(trace_id, span_id)
        
        # Create span
        span = Span.create_server_span(
            trace_id=trace_id,
            span_id=span_id,
            service=self.environment,
            operation=f"{request.method} {request.url.path}"
        )
        span.tags = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params)
        }
        
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record traffic pattern
            latency_ms = round((time.time() - start_time) * 1000, 2)
            NexarchMiddleware._traffic_analyzer.record_request(
                endpoint=request.url.path,
                latency_ms=latency_ms,
                status_code=response.status_code
            )
            
            # Detect database and external calls from span tags
            downstream_deps = []
            span_tags = span.tags if span.tags else {}
            if span_tags.get("db.statement"):
                downstream_deps.append({
                    "type": "database",
                    "target": span_tags.get("db.system", "unknown"),
                    "operation": span_tags.get("db.statement", "")[:100]
                })
            
            if span_tags.get("http.url"):
                downstream_deps.append({
                    "type": "external_http",
                    "target": span_tags.get("http.url", ""),
                    "method": span_tags.get("http.method", "GET")
                })
            
            # Build dependency chain
            if downstream_deps:
                chain = [self.service_name, request.url.path] + [dep["target"] for dep in downstream_deps]
                NexarchMiddleware._dependency_mapper.add_latency_chain(chain, latency_ms)
            
            # Finish span
            span.finish(status_code=response.status_code)
            
            # Enhanced span data with architecture info
            span_dict = span.to_dict()
            span_dict["downstream_dependencies"] = downstream_deps
            span_dict["service_name"] = self.service_name
            span_dict["architecture_metadata"] = {
                "endpoint_pattern": request.url.path,
                "calls_database": len([d for d in downstream_deps if d["type"] == "database"]) > 0,
                "calls_external": len([d for d in downstream_deps if d["type"] == "external_http"]) > 0,
                "latency_breakdown": {
                    "total_ms": latency_ms,
                    "downstream_ms": sum(span_tags.get(f"{dep['type']}_latency", 0) for dep in downstream_deps)
                }
            }
            
            # Enqueue span
            get_log_queue().enqueue({
                "type": "span",
                "timestamp": timestamp,
                "data": span_dict
            })
            
            # Legacy format
            latency_ms = round((time.time() - start_time) * 1000, 2)
            legacy_span = SpanData(
                trace_id=trace_id,
                span_id=span_id,
                parent_id=None,
                service=self.environment,
                operation=f"{request.method} {request.url.path}",
                kind="server",
                timestamp=timestamp,
                latency_ms=latency_ms,
                status_code=response.status_code,
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                status="ok" if response.status_code < 400 else "error",
                error=None,
                downstream=[]
            )
            
            NexarchLogger.log_span(legacy_span)
            
            return response
        
        except Exception as e:
            # Finish span with error
            span.finish(status_code=500, error=str(e))
            
            # Enqueue span
            get_log_queue().enqueue({
                "type": "span",
                "timestamp": timestamp,
                "data": span.to_dict()
            })
            
            # Log error
            latency_ms = round((time.time() - start_time) * 1000, 2)
            error_data = ErrorData(
                trace_id=trace_id,
                span_id=span_id,
                timestamp=timestamp,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                service=self.environment,
                operation=f"{request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params)
            )
            
            NexarchLogger.log_error(error_data)
            
            # Legacy span
            legacy_span = SpanData(
                trace_id=trace_id,
                span_id=span_id,
                parent_id=None,
                service=self.environment,
                operation=f"{request.method} {request.url.path}",
                kind="server",
                timestamp=timestamp,
                latency_ms=latency_ms,
                status_code=500,
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                status="error",
                error=str(e),
                downstream=[]
            )
            
            NexarchLogger.log_span(legacy_span)
            
            raise
        
        finally:
            # Clear context
            clear_trace_context()
