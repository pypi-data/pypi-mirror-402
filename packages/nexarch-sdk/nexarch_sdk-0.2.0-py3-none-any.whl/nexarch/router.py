"""Nexarch Router"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from .loggers import NexarchLogger
from datetime import datetime

nexarch_router = APIRouter()


@nexarch_router.get("/health")
async def health_check():
    """SDK health"""
    return {
        "status": "healthy",
        "service": "nexarch-sdk",
        "timestamp": datetime.utcnow().isoformat()
    }


@nexarch_router.get("/log_fetch")
@nexarch_router.get("/telemetry")
async def get_telemetry():
    """Get all telemetry"""
    logs = NexarchLogger.get_all_logs()
    
    return {
        "total_events": len(logs),
        "events": logs,
        "retrieved_at": datetime.utcnow().isoformat()
    }


@nexarch_router.get("/telemetry/stats")
async def get_telemetry_stats():
    """
    Get statistics about collected telemetry.
    """
    logs = NexarchLogger.get_all_logs()
    
    if not logs:
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "error_rate": 0,
            "average_latency_ms": 0,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    spans = [log for log in logs if log.get("type") == "span"]
    errors = [log for log in logs if log.get("type") == "error"]
    
    # Calculate statistics
    total_requests = len(spans)
    error_count = len(errors)
    success_count = len([s for s in spans if s.get("data", {}).get("status") == "ok"])
    
    avg_latency = 0
    if spans:
        latencies = [s.get("data", {}).get("latency_ms", 0) for s in spans]
        avg_latency = sum(latencies) / len(latencies)
    
    return {
        "total_requests": total_requests,
        "successful_requests": success_count,
        "failed_requests": error_count,
        "error_rate": round(error_count / total_requests * 100, 2) if total_requests > 0 else 0,
        "average_latency_ms": round(avg_latency, 2),
        "collected_at": datetime.utcnow().isoformat()
    }


@nexarch_router.delete("/telemetry")
async def clear_telemetry():
    """
    Clear all collected telemetry data.
    
    Use this to reset local logs.
    """
    try:
        NexarchLogger.clear_logs()
        return {
            "status": "success",
            "message": "All telemetry data cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")


@nexarch_router.get("/telemetry/errors")
async def get_errors():
    """
    Retrieve only error events.
    """
    logs = NexarchLogger.get_all_logs()
    errors = [log for log in logs if log.get("type") == "error"]
    
    return {
        "total_errors": len(errors),
        "errors": errors,
        "retrieved_at": datetime.utcnow().isoformat()
    }


@nexarch_router.get("/telemetry/spans")
async def get_spans():
    """
    Retrieve only span events (requests).
    """
    logs = NexarchLogger.get_all_logs()
    spans = [log for log in logs if log.get("type") == "span"]
    
    return {
        "total_spans": len(spans),
        "spans": spans,
        "retrieved_at": datetime.utcnow().isoformat()
    }