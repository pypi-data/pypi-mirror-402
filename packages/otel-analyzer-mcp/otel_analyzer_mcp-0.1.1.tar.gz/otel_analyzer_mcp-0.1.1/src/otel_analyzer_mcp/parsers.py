"""Trace format parsers with auto-detection."""

import json
from datetime import datetime, timezone
from pathlib import Path

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.trace.v1.trace_pb2 import TracesData

from .models import Span, SpanEvent, Trace


def detect_format(data: str | bytes) -> str:
    """Detect trace format from content."""
    if isinstance(data, bytes):
        try:
            TracesData().ParseFromString(data)
            return "protobuf"
        except Exception:
            data = data.decode("utf-8")

    try:
        parsed = json.loads(data)
        if "resourceSpans" in parsed:
            return "json"
        if "data" in parsed and isinstance(parsed["data"], list):
            return "jaeger"
        if "Traces" in parsed or "traces" in parsed:
            return "xray"
    except json.JSONDecodeError:
        pass
    return "unknown"


def parse_file(path: str) -> Trace:
    """Parse trace from file, auto-detecting format."""
    p = Path(path)
    content = p.read_bytes()
    fmt = detect_format(content)

    if fmt == "protobuf":
        return parse_protobuf(content, source=path)
    content_str = content.decode("utf-8")
    if fmt == "json":
        return parse_otlp_json(content_str, source=path)
    if fmt == "jaeger":
        return parse_jaeger(content_str, source=path)
    if fmt == "xray":
        return parse_xray_json(content_str, source=path)
    raise ValueError(f"Unknown trace format in {path}")


def parse_string(data: str, fmt: str | None = None, source: str = "string") -> Trace:
    """Parse trace from string with optional format hint."""
    fmt = fmt or detect_format(data)
    if fmt == "json":
        return parse_otlp_json(data, source)
    if fmt == "jaeger":
        return parse_jaeger(data, source)
    if fmt == "xray":
        return parse_xray_json(data, source)
    raise ValueError(f"Unknown or unsupported format: {fmt}")


def _ns_to_datetime(ns: int) -> datetime:
    """Convert nanoseconds to datetime."""
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc)


def parse_otlp_json(data: str, source: str = "string") -> Trace:
    """Parse OTLP JSON format."""
    parsed = json.loads(data)
    spans = []
    services = set()
    has_errors = False
    trace_id = ""

    for rs in parsed.get("resourceSpans", []):
        service = rs.get("resource", {}).get("attributes", [])
        service_name = next(
            (a["value"].get("stringValue", "") for a in service if a.get("key") == "service.name"),
            "unknown",
        )
        services.add(service_name)

        for ss in rs.get("scopeSpans", []):
            for s in ss.get("spans", []):
                trace_id = trace_id or s.get("traceId", "")
                status = s.get("status", {}).get("code", 0)
                status_str = "ERROR" if status == 2 else "OK"
                has_errors = has_errors or status_str == "ERROR"

                events = [
                    SpanEvent(
                        name=e.get("name", ""),
                        timestamp=_ns_to_datetime(int(e.get("timeUnixNano", 0))),
                        attributes={a["key"]: a.get("value", {}) for a in e.get("attributes", [])},
                    )
                    for e in s.get("events", [])
                ]

                start_ns = int(s.get("startTimeUnixNano", 0))
                end_ns = int(s.get("endTimeUnixNano", 0))
                spans.append(
                    Span(
                        span_id=s.get("spanId", ""),
                        trace_id=s.get("traceId", ""),
                        parent_id=s.get("parentSpanId") or None,
                        name=s.get("name", ""),
                        service=service_name,
                        start_time=_ns_to_datetime(start_ns),
                        end_time=_ns_to_datetime(end_ns),
                        duration_ms=(end_ns - start_ns) / 1e6,
                        status=status_str,
                        attributes={a["key"]: a.get("value", {}) for a in s.get("attributes", [])},
                        events=events,
                    )
                )

    return Trace(
        trace_id=trace_id,
        source=source,
        format="json",
        spans=spans,
        services=services,
        has_errors=has_errors,
    )


def parse_jaeger(data: str, source: str = "string") -> Trace:
    """Parse Jaeger JSON format."""
    parsed = json.loads(data)
    spans = []
    services = set()
    has_errors = False
    trace_id = ""

    for trace_data in parsed.get("data", []):
        trace_id = trace_id or trace_data.get("traceID", "")
        processes = trace_data.get("processes", {})

        for s in trace_data.get("spans", []):
            proc = processes.get(s.get("processID", ""), {})
            service_name = proc.get("serviceName", "unknown")
            services.add(service_name)

            tags = {t["key"]: t["value"] for t in s.get("tags", [])}
            status_str = "ERROR" if tags.get("error") or tags.get("otel.status_code") == "ERROR" else "OK"
            has_errors = has_errors or status_str == "ERROR"

            start_us = s.get("startTime", 0)
            duration_us = s.get("duration", 0)
            events = [
                SpanEvent(
                    name=log.get("fields", [{}])[0].get("value", "event"),
                    timestamp=datetime.fromtimestamp(log.get("timestamp", 0) / 1e6, tz=timezone.utc),
                    attributes={f["key"]: f["value"] for f in log.get("fields", [])},
                )
                for log in s.get("logs", [])
            ]

            refs = s.get("references", [])
            parent_id = next((r["spanID"] for r in refs if r.get("refType") == "CHILD_OF"), None)

            spans.append(
                Span(
                    span_id=s.get("spanID", ""),
                    trace_id=s.get("traceID", ""),
                    parent_id=parent_id,
                    name=s.get("operationName", ""),
                    service=service_name,
                    start_time=datetime.fromtimestamp(start_us / 1e6, tz=timezone.utc),
                    end_time=datetime.fromtimestamp((start_us + duration_us) / 1e6, tz=timezone.utc),
                    duration_ms=duration_us / 1000,
                    status=status_str,
                    attributes=tags,
                    events=events,
                )
            )

    return Trace(
        trace_id=trace_id,
        source=source,
        format="jaeger",
        spans=spans,
        services=services,
        has_errors=has_errors,
    )


def parse_protobuf(data: bytes, source: str = "string") -> Trace:
    """Parse OTLP Protobuf format."""
    traces_data = TracesData()
    traces_data.ParseFromString(data)
    as_dict = MessageToDict(traces_data)
    return parse_otlp_json(json.dumps(as_dict), source)


def parse_xray_json(data: str, source: str = "string") -> Trace:
    """Parse X-Ray JSON export format."""
    parsed = json.loads(data)
    traces_list = parsed.get("Traces", parsed.get("traces", []))
    spans = []
    services = set()
    has_errors = False
    trace_id = ""

    for trace_data in traces_list:
        trace_id = trace_id or trace_data.get("Id", "")
        for seg in trace_data.get("Segments", []):
            doc = json.loads(seg.get("Document", "{}")) if isinstance(seg.get("Document"), str) else seg.get("Document", {})
            _parse_xray_segment(doc, spans, services, trace_id)
            if doc.get("fault") or doc.get("error"):
                has_errors = True

    return Trace(
        trace_id=trace_id,
        source=source,
        format="xray",
        spans=spans,
        services=services,
        has_errors=has_errors,
    )


def _parse_xray_segment(doc: dict, spans: list, services: set, trace_id: str, parent_id: str | None = None):
    """Recursively parse X-Ray segment and subsegments."""
    service_name = doc.get("name", "unknown")
    services.add(service_name)

    start_time = doc.get("start_time", 0)
    end_time = doc.get("end_time", start_time)
    status = "FAULT" if doc.get("fault") else "ERROR" if doc.get("error") else "OK"

    events = []
    if cause := doc.get("cause"):
        exceptions = cause.get("exceptions", []) if isinstance(cause, dict) else []
        for exc in exceptions:
            events.append(
                SpanEvent(
                    name="exception",
                    timestamp=datetime.fromtimestamp(start_time, tz=timezone.utc),
                    attributes={"type": exc.get("type", ""), "message": exc.get("message", "")},
                )
            )

    spans.append(
        Span(
            span_id=doc.get("id", ""),
            trace_id=trace_id,
            parent_id=parent_id,
            name=doc.get("name", ""),
            service=service_name,
            start_time=datetime.fromtimestamp(start_time, tz=timezone.utc),
            end_time=datetime.fromtimestamp(end_time, tz=timezone.utc),
            duration_ms=(end_time - start_time) * 1000,
            status=status,
            attributes=doc.get("annotations", {}),
            events=events,
        )
    )

    for sub in doc.get("subsegments", []):
        _parse_xray_segment(sub, spans, services, trace_id, parent_id=doc.get("id"))
