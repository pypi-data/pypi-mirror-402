"""AWS X-Ray client for fetching traces."""

import json
from datetime import datetime, timezone

import boto3

from .models import Span, SpanEvent, Trace


class XRayClient:
    """Client for fetching traces from AWS X-Ray."""

    def __init__(self, profile: str | None = None, region: str | None = None):
        session = boto3.Session(profile_name=profile, region_name=region)
        self.client = session.client("xray")

    def fetch_traces(self, trace_ids: list[str]) -> list[Trace]:
        """Fetch full traces by ID."""
        traces = []
        # X-Ray batch_get_traces accepts up to 5 IDs at a time
        for i in range(0, len(trace_ids), 5):
            batch = trace_ids[i : i + 5]
            resp = self.client.batch_get_traces(TraceIds=batch)
            for t in resp.get("Traces", []):
                traces.append(self._parse_trace(t))
        return traces

    def search_traces(
        self,
        filter_expression: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search for traces, returning summaries."""
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or end_time.replace(hour=0, minute=0, second=0)

        params = {"StartTime": start_time, "EndTime": end_time}
        if filter_expression:
            params["FilterExpression"] = filter_expression

        summaries = []
        paginator = self.client.get_paginator("get_trace_summaries")
        for page in paginator.paginate(**params):
            for s in page.get("TraceSummaries", []):
                summaries.append({
                    "trace_id": s.get("Id"),
                    "duration_ms": (s.get("Duration", 0) or 0) * 1000,
                    "has_error": s.get("HasError", False),
                    "has_fault": s.get("HasFault", False),
                    "services": [svc.get("Name") for svc in s.get("ServiceIds", [])],
                    "response_time_ms": (s.get("ResponseTime", 0) or 0) * 1000,
                })
                if len(summaries) >= limit:
                    return summaries
        return summaries

    def _parse_trace(self, trace_data: dict) -> Trace:
        """Parse X-Ray trace response into Trace model."""
        trace_id = trace_data.get("Id", "")
        spans = []
        services = set()
        has_errors = False

        for seg in trace_data.get("Segments", []):
            doc = json.loads(seg.get("Document", "{}"))
            self._parse_segment(doc, spans, services, trace_id)
            if doc.get("fault") or doc.get("error"):
                has_errors = True

        return Trace(
            trace_id=trace_id,
            source="xray",
            format="xray",
            spans=spans,
            services=services,
            has_errors=has_errors,
        )

    def _parse_segment(self, doc: dict, spans: list, services: set, trace_id: str, parent_id: str | None = None):
        """Recursively parse segment and subsegments."""
        service_name = doc.get("name", "unknown")
        services.add(service_name)

        start_time = doc.get("start_time", 0)
        end_time = doc.get("end_time", start_time)
        status = "FAULT" if doc.get("fault") else "ERROR" if doc.get("error") else "OK"

        events = []
        if cause := doc.get("cause"):
            for exc in cause.get("exceptions", []) if isinstance(cause, dict) else []:
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
            self._parse_segment(sub, spans, services, trace_id, parent_id=doc.get("id"))
