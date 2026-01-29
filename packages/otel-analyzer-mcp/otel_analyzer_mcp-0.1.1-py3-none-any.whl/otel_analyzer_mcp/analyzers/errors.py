"""Error analysis for traces."""

from ..models import Trace


def analyze_errors(trace: Trace) -> dict:
    """Comprehensive error analysis of a trace."""
    if not trace.spans:
        return {"error": "No spans in trace"}

    span_map = {s.span_id: s for s in trace.spans}
    error_spans = [s for s in trace.spans if s.status in ("ERROR", "FAULT")]

    errors = []
    for span in error_spans:
        # Extract exception details from events
        exceptions = []
        for event in span.events:
            if event.name == "exception" or "exception" in event.name.lower():
                exceptions.append({
                    "type": event.attributes.get("type", event.attributes.get("exception.type", "")),
                    "message": event.attributes.get("message", event.attributes.get("exception.message", "")),
                })

        # Get parent context
        parent = span_map.get(span.parent_id) if span.parent_id else None
        # Get child spans
        children = [s for s in trace.spans if s.parent_id == span.span_id]

        errors.append({
            "span_id": span.span_id,
            "name": span.name,
            "service": span.service,
            "status": span.status,
            "duration_ms": span.duration_ms,
            "exceptions": exceptions,
            "attributes": span.attributes,
            "parent": {"span_id": parent.span_id, "name": parent.name, "service": parent.service} if parent else None,
            "children": [{"span_id": c.span_id, "name": c.name, "service": c.service} for c in children],
        })

    # Group errors by service
    errors_by_service = {}
    for e in errors:
        svc = e["service"]
        errors_by_service.setdefault(svc, []).append(e["name"])

    return {
        "has_errors": trace.has_errors,
        "error_count": len(error_spans),
        "total_spans": len(trace.spans),
        "error_rate": len(error_spans) / len(trace.spans) if trace.spans else 0,
        "errors_by_service": {k: len(v) for k, v in errors_by_service.items()},
        "error_spans": errors,
    }
