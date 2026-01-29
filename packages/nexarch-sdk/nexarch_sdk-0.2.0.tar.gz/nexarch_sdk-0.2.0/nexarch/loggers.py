"""
Nexarch Logger - Handles local JSON logging and future remote export
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import SpanData, ErrorData, MetricData


class NexarchLogger:
    """
    Handles logging of telemetry data to local JSON files.
    Thread-safe singleton logger.
    """
    
    _instance: Optional['NexarchLogger'] = None
    _log_file: Optional[str] = None
    _enable_local_logs: bool = True
    
    @classmethod
    def initialize(cls, log_file: str = "nexarch_telemetry.json", enable_local_logs: bool = True):
        """
        Initialize the logger with configuration.
        
        Args:
            log_file: Path to the JSON log file
            enable_local_logs: Whether to write logs locally
        """
        cls._log_file = log_file
        cls._enable_local_logs = enable_local_logs
        
        if enable_local_logs:
            # Ensure the log file exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize with empty array if file doesn't exist
            if not log_path.exists():
                with open(log_file, 'w') as f:
                    json.dump([], f)
    
    @classmethod
    def _append_to_log(cls, data: dict):
        """
        Append data to the JSON log file.
        """
        if not cls._enable_local_logs or not cls._log_file:
            return
        
        try:
            # Read existing data
            with open(cls._log_file, 'r') as f:
                logs = json.load(f)
            
            # Append new data
            logs.append(data)
            
            # Write back
            with open(cls._log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        
        except json.JSONDecodeError as e:
            # Corrupted JSON file, reinitialize
            print(f"Warning: Corrupted Nexarch log file, reinitializing: {e}")
            with open(cls._log_file, 'w') as f:
                json.dump([data], f, indent=2)
        except Exception as e:
            # Fallback: write to separate error log
            print(f"Warning: Failed to write to Nexarch log: {e}")
    
    @classmethod
    def log_span(cls, span: SpanData):
        """
        Log a span (successful or failed request).
        
        Args:
            span: SpanData instance
        """
        data = {
            "type": "span",
            "timestamp": span.timestamp,
            "data": span.to_dict()
        }
        cls._append_to_log(data)
    
    @classmethod
    def log_error(cls, error: ErrorData):
        """
        Log an error or exception.
        
        Args:
            error: ErrorData instance
        """
        data = {
            "type": "error",
            "timestamp": error.timestamp,
            "data": error.to_dict()
        }
        cls._append_to_log(data)
    
    @classmethod
    def log_metric(cls, metric: MetricData):
        """
        Log a metric.
        
        Args:
            metric: MetricData instance
        """
        data = {
            "type": "metric",
            "timestamp": metric.timestamp,
            "data": metric.to_dict()
        }
        cls._append_to_log(data)
    
    @classmethod
    def get_all_logs(cls) -> list:
        """
        Retrieve all logs from the JSON file.
        
        Returns:
            List of all logged events
        """
        if not cls._log_file or not os.path.exists(cls._log_file):
            return []
        
        try:
            with open(cls._log_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    @classmethod
    def clear_logs(cls):
        """
        Clear all logs from the JSON file.
        """
        if cls._log_file:
            with open(cls._log_file, 'w') as f:
                json.dump([], f)