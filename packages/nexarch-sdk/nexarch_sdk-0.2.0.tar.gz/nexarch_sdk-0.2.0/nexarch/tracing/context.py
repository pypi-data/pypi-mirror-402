"""Trace context propagation"""
from contextvars import ContextVar
from typing import Optional

# Context vars
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_span_id: ContextVar[Optional[str]] = ContextVar('span_id', default=None)
_parent_span_id: ContextVar[Optional[str]] = ContextVar('parent_span_id', default=None)


def set_trace_context(trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
    """Set trace context"""
    _trace_id.set(trace_id)
    _span_id.set(span_id)
    _parent_span_id.set(parent_span_id)


def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return _trace_id.get()


def get_span_id() -> Optional[str]:
    """Get current span ID"""
    return _span_id.get()


def get_parent_span_id() -> Optional[str]:
    """Get parent span ID"""
    return _parent_span_id.get()


def clear_trace_context():
    """Clear trace context"""
    _trace_id.set(None)
    _span_id.set(None)
    _parent_span_id.set(None)
