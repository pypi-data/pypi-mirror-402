"""CloudWatch client for fetching GenAI spans from aws/spans log group."""

import json
import time
from datetime import datetime, timezone

import boto3

from .models import Span, SpanEvent, Trace


class CloudWatchSpansClient:
    """Client for fetching GenAI traces from CloudWatch aws/spans log group."""

    LOG_GROUP = "aws/spans"

    def __init__(self, profile: str | None = None, region: str | None = None):
        session = boto3.Session(profile_name=profile, region_name=region)
        self.client = session.client("logs")

    def search_genai_traces(
        self,
        filter_query: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search for GenAI traces in aws/spans log group."""
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or end_time.replace(hour=0, minute=0, second=0)

        # Build query for GenAI spans
        base_query = "fields @timestamp, @message, traceId, spanId, name"
        if filter_query:
            query = f"{base_query} | filter {filter_query} | sort @timestamp desc | limit {limit}"
        else:
            # Default: filter for GenAI-related spans
            query = f"{base_query} | filter name like /gen_ai/ or @message like /bedrock/ | sort @timestamp desc | limit {limit}"

        return self._run_query(query, start_time, end_time)

    def fetch_trace(self, trace_id: str, start_time: datetime | None = None, end_time: datetime | None = None) -> Trace | None:
        """Fetch all spans for a specific trace ID."""
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or end_time.replace(hour=0, minute=0, second=0)

        query = f'fields @timestamp, @message | filter traceId = "{trace_id}" | sort @timestamp asc | limit 1000'
        results = self._run_query(query, start_time, end_time)

        if not results:
            return None

        return self._parse_spans_to_trace(trace_id, results)

    def _run_query(self, query: str, start_time: datetime, end_time: datetime) -> list[dict]:
        """Run a CloudWatch Logs Insights query."""
        try:
            resp = self.client.start_query(
                logGroupName=self.LOG_GROUP,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query,
            )
            query_id = resp["queryId"]

            # Poll for results
            while True:
                result = self.client.get_query_results(queryId=query_id)
                status = result["status"]
                if status in ("Complete", "Failed", "Cancelled"):
                    break
                time.sleep(0.5)

            if status != "Complete":
                return []

            # Parse results
            results = []
            for row in result.get("results", []):
                item = {field["field"]: field["value"] for field in row}
                results.append(item)
            return results
        except self.client.exceptions.ResourceNotFoundException:
            return []

    def _parse_spans_to_trace(self, trace_id: str, results: list[dict]) -> Trace:
        """Parse CloudWatch span results into a Trace."""
        spans = []
        services = set()
        has_errors = False

        for row in results:
            msg = row.get("@message", "{}")
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue

            span = self._parse_span(data, trace_id)
            if span:
                spans.append(span)
                if span.service:
                    services.add(span.service)
                if span.status in ("ERROR", "FAULT"):
                    has_errors = True

        return Trace(
            trace_id=trace_id,
            source="cloudwatch",
            format="otel",
            spans=spans,
            services=services,
            has_errors=has_errors,
        )

    def _parse_span(self, data: dict, trace_id: str) -> Span | None:
        """Parse a single span from CloudWatch log entry."""
        span_id = data.get("spanId") or data.get("span_id", "")
        if not span_id:
            return None

        # Extract GenAI attributes
        attrs = data.get("attributes", {})
        resource_attrs = data.get("resource", {}).get("attributes", {})

        service = resource_attrs.get("service.name", attrs.get("service.name", "unknown"))
        name = data.get("name", "")

        # Parse timestamps
        start_ns = data.get("startTimeUnixNano", 0)
        end_ns = data.get("endTimeUnixNano", start_ns)
        start_time = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc) if start_ns else datetime.now(timezone.utc)
        end_time = datetime.fromtimestamp(end_ns / 1e9, tz=timezone.utc) if end_ns else start_time
        duration_ms = (end_ns - start_ns) / 1e6 if start_ns and end_ns else 0

        # Determine status
        status_code = data.get("status", {}).get("code", 0)
        status = "ERROR" if status_code == 2 else "OK"

        # Parse events
        events = []
        for evt in data.get("events", []):
            events.append(SpanEvent(
                name=evt.get("name", ""),
                timestamp=datetime.fromtimestamp(evt.get("timeUnixNano", 0) / 1e9, tz=timezone.utc),
                attributes=evt.get("attributes", {}),
            ))

        # Include GenAI-specific attributes
        genai_attrs = {k: v for k, v in attrs.items() if k.startswith("gen_ai.")}

        return Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=data.get("parentSpanId") or data.get("parent_span_id"),
            name=name,
            service=service,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=status,
            attributes={**attrs, **genai_attrs},
            events=events,
        )
