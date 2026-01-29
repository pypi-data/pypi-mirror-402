"""Normalized trace data models."""

from datetime import datetime
from pydantic import BaseModel, Field


class SpanEvent(BaseModel):
    """An event within a span (logs, exceptions)."""

    name: str
    timestamp: datetime
    attributes: dict = Field(default_factory=dict)


class Span(BaseModel):
    """A single span in a trace."""

    span_id: str
    trace_id: str
    parent_id: str | None = None
    name: str
    service: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status: str = "OK"  # OK, ERROR, FAULT
    attributes: dict = Field(default_factory=dict)
    events: list[SpanEvent] = Field(default_factory=list)


class Trace(BaseModel):
    """A complete trace with all spans."""

    trace_id: str
    source: str  # file path, "xray", "string"
    format: str  # json, jaeger, protobuf, xray
    spans: list[Span] = Field(default_factory=list)
    services: set[str] = Field(default_factory=set)
    has_errors: bool = False

    @property
    def root_span(self) -> Span | None:
        """Find the root span (no parent)."""
        for span in self.spans:
            if span.parent_id is None:
                return span
        return None

    @property
    def duration_ms(self) -> float:
        """Total trace duration from root span."""
        if root := self.root_span:
            return root.duration_ms
        if self.spans:
            start = min(s.start_time for s in self.spans)
            end = max(s.end_time for s in self.spans)
            return (end - start).total_seconds() * 1000
        return 0.0

    class Config:
        arbitrary_types_allowed = True
