"""Local JSON exporter"""
import json
from pathlib import Path
from typing import Dict, Any
from .base import Exporter


class LocalJSONExporter(Exporter):
    """Local JSON file exporter"""
    
    def __init__(self, log_file: str = "nexarch_telemetry.json"):
        self.log_file = log_file
        self._init_file()
    
    def _init_file(self):
        """Init log file"""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not log_path.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def export(self, data: Dict[str, Any]):
        """Export to JSON"""
        if not data:
            return
        
        try:
            # Read existing
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Append
            logs.append(data)
            
            # Write back
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        
        except Exception:
            pass  # Silent fail
    
    def close(self):
        """Close"""
        pass
