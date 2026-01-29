"""HTTP exporter for sending telemetry to Nexarch backend"""
import requests
import json
from typing import Dict, Any, Optional
from .base import Exporter


class HttpExporter(Exporter):
    """
    HTTP exporter that sends telemetry data to Nexarch backend.
    Handles batching and retry logic.
    """
    
    def __init__(self, endpoint: str, api_key: str, batch_size: int = 50, timeout: int = 10):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.batch_size = batch_size
        self.timeout = timeout
        self.batch = []
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def export(self, data: Dict[str, Any]):
        """
        Export data via HTTP to Nexarch backend.
        Supports batching for efficiency.
        """
        if not data:
            return
        
        try:
            # Handle different data types
            data_type = data.get('type', 'span')
            
            if data_type == 'span':
                self._export_span(data)
            elif data_type == 'architecture_discovery':
                self._export_discovery(data)
            elif data_type == 'error':
                self._export_error(data)
            else:
                # Generic export
                self._send_data('/api/v1/ingest', data)
        
        except Exception as e:
            # Don't fail the application if export fails
            print(f"[Nexarch] Failed to export telemetry: {e}")
    
    def _export_span(self, data: Dict[str, Any]):
        """Export span data"""
        span_data = data.get('data', {})
        
        # Add to batch
        self.batch.append(span_data)
        
        # Flush batch if full
        if len(self.batch) >= self.batch_size:
            self.flush()
    
    def _export_discovery(self, data: Dict[str, Any]):
        """Export architecture discovery data"""
        discovery_data = data.get('data', {})
        self._send_data('/api/v1/ingest/architecture-discovery', discovery_data)
    
    def _export_error(self, data: Dict[str, Any]):
        """Export error data (convert to span with error)"""
        error_data = data.get('data', {})
        # Errors are treated as failed spans
        self._send_data('/api/v1/ingest', error_data)
    
    def _send_data(self, path: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """Send data to backend"""
        try:
            url = f"{self.endpoint}{path}"
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 202]:
                return response.json()
            else:
                print(f"[Nexarch] Export failed: {response.status_code} - {response.text[:200]}")
                return None
        
        except requests.exceptions.Timeout:
            print(f"[Nexarch] Export timeout after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print(f"[Nexarch] Cannot connect to {self.endpoint}")
            return None
        except Exception as e:
            print(f"[Nexarch] Export error: {e}")
            return None
    
    def flush(self):
        """Flush batch of spans"""
        if not self.batch:
            return
        
        try:
            self._send_data('/api/v1/ingest/batch', self.batch)
            self.batch = []
        except Exception as e:
            print(f"[Nexarch] Batch flush failed: {e}")
            self.batch = []
    
    def close(self):
        """Close exporter and flush remaining data"""
        self.flush()
        self.session.close()
