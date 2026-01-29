"""Nexarch SDK Client"""
from fastapi import FastAPI
from .middleware import NexarchMiddleware
from .router import nexarch_router
from .loggers import NexarchLogger
from .exporters import LocalJSONExporter, HttpExporter
from .queue import get_log_queue
from .instrumentation import patch_requests, patch_httpx
from .instrumentation.db_patch import patch_all_databases
from typing import Optional


class NexarchSDK:
    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        service_name: Optional[str] = None,
        log_file: str = "nexarch_telemetry.json",
        observation_duration: str = "3h",
        sampling_rate: float = 1.0,
        enable_local_logs: bool = True,
        enable_http_export: bool = False,
        http_endpoint: Optional[str] = None,
        enable_auto_discovery: bool = True,
        enable_db_instrumentation: bool = True
    ):
        self.api_key = api_key
        self.environment = environment
        self.service_name = service_name or environment
        self.log_file = log_file
        self.observation_duration = observation_duration
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))  # Clamp between 0 and 1
        self.enable_local_logs = enable_local_logs
        self.enable_http_export = enable_http_export
        self.http_endpoint = http_endpoint
        self.enable_auto_discovery = enable_auto_discovery
        self.enable_db_instrumentation = enable_db_instrumentation
        
        # Init logger
        NexarchLogger.initialize(
            log_file=log_file,
            enable_local_logs=enable_local_logs
        )
        
        # Setup exporter
        if enable_http_export and http_endpoint:
            exporter = HttpExporter(http_endpoint, api_key)
        else:
            exporter = LocalJSONExporter(log_file)
        
        queue = get_log_queue()
        queue.set_exporter(exporter)
        queue.start()
        
        # Patch HTTP clients
        patch_requests()
        patch_httpx()
        
        # Patch database drivers
        if enable_db_instrumentation:
            patch_all_databases()
            print("[Nexarch] Database instrumentation enabled - capturing all DB queries")
    
    def init(self, app: FastAPI) -> None:
        """Attach SDK to FastAPI"""
        
        # Add middleware with auto-discovery
        app.add_middleware(
            NexarchMiddleware,
            api_key=self.api_key,
            environment=self.environment,
            service_name=self.service_name,
            sampling_rate=self.sampling_rate,
            enable_auto_discovery=self.enable_auto_discovery
        )
        
        # Auto-inject router
        app.include_router(
            nexarch_router,
            prefix="/__nexarch",
            tags=["Nexarch Internal"],
            include_in_schema=False
        )
        
        print(f"[Nexarch] SDK initialized for service '{self.service_name}'")
        print(f"[Nexarch] Auto-discovery: {'enabled' if self.enable_auto_discovery else 'disabled'}")
        print(f"[Nexarch] DB instrumentation: {'enabled' if self.enable_db_instrumentation else 'disabled'}")
    
    @staticmethod
    def start(app: FastAPI, api_key: str, **kwargs) -> None:
        """One-line init"""
        sdk = NexarchSDK(api_key=api_key, **kwargs)
        sdk.init(app)
