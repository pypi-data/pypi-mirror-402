"""OTEL Trace Analysis MCP Server."""

import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .analyzers import analyze_errors, analyze_performance
from .cloudwatch import CloudWatchSpansClient
from .models import Trace
from .parsers import parse_file, parse_string
from .xray import XRayClient

mcp = FastMCP("otel-analyzer-mcp")
traces: dict[str, Trace] = {}


@mcp.tool()
def load_trace(
    path: str | None = None,
    data: str | None = None,
    trace_id: str | None = None,
    source: str = "xray",
    profile: str | None = None,
    region: str | None = None,
) -> str:
    """Load a trace from file, string, X-Ray, or CloudWatch. Auto-detects format.
    
    Args:
        path: File path to trace JSON
        data: Raw JSON string
        trace_id: Trace ID to fetch from X-Ray or CloudWatch
        source: Source for trace_id lookup: 'xray' or 'cloudwatch' (default: xray)
        profile: AWS profile name
        region: AWS region
    """
    if path:
        trace = parse_file(path)
        key = trace.trace_id or path.split("/")[-1].rsplit(".", 1)[0]
    elif data:
        trace = parse_string(data)
        key = trace.trace_id or str(hash(data))[:8]
    elif trace_id:
        if source == "cloudwatch":
            client = CloudWatchSpansClient(profile=profile, region=region)
            trace = client.fetch_trace(trace_id)
            if not trace:
                return f"No trace found in CloudWatch for ID: {trace_id}"
        else:
            client = XRayClient(profile=profile, region=region)
            fetched = client.fetch_traces([trace_id])
            if not fetched:
                return f"No trace found in X-Ray for ID: {trace_id}"
            trace = fetched[0]
        key = trace_id
    else:
        return "Provide path, data, or trace_id"

    traces[key] = trace
    return json.dumps({
        "id": key,
        "trace_id": trace.trace_id,
        "format": trace.format,
        "source": trace.source,
        "services": list(trace.services),
        "span_count": len(trace.spans),
        "has_errors": trace.has_errors,
    })


@mcp.tool()
def search_xray(
    filter_expression: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 20,
    profile: str | None = None,
    region: str | None = None,
) -> str:
    """Search X-Ray for traces matching filter expression."""
    client = XRayClient(profile=profile, region=region)
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    results = client.search_traces(filter_expression, start, end, limit)
    return json.dumps(results)


@mcp.tool()
def search_genai_traces(
    filter_query: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 20,
    profile: str | None = None,
    region: str | None = None,
) -> str:
    """Search CloudWatch aws/spans for GenAI traces from Bedrock AgentCore.
    
    Args:
        filter_query: CloudWatch Logs Insights filter (e.g., 'name like /bedrock/')
        start_time: ISO format start time
        end_time: ISO format end time
        limit: Max results (default: 20)
        profile: AWS profile name
        region: AWS region
    
    Returns GenAI traces with model info, token usage, and latency.
    """
    client = CloudWatchSpansClient(profile=profile, region=region)
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    results = client.search_genai_traces(filter_query, start, end, limit)
    return json.dumps(results)


@mcp.tool()
def list_traces() -> str:
    """List all loaded traces with summaries."""
    return json.dumps([
        {"id": k, "trace_id": t.trace_id, "services": list(t.services), "span_count": len(t.spans), "has_errors": t.has_errors}
        for k, t in traces.items()
    ])


@mcp.tool()
def analyze_perf(trace_id: str, slow_threshold_ms: float | None = None) -> str:
    """Analyze trace performance: latency breakdown, slow spans, critical path."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"
    return json.dumps(analyze_performance(traces[trace_id], slow_threshold_ms))


@mcp.tool()
def analyze_errs(trace_id: str) -> str:
    """Analyze trace errors: error spans, exceptions, failure context."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"
    return json.dumps(analyze_errors(traces[trace_id]))


@mcp.tool()
def summarize_trace(trace_id: str) -> str:
    """High-level trace overview."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"
    t = traces[trace_id]
    return json.dumps({
        "trace_id": t.trace_id,
        "format": t.format,
        "source": t.source,
        "services": list(t.services),
        "span_count": len(t.spans),
        "duration_ms": t.duration_ms,
        "has_errors": t.has_errors,
        "root_span": {"name": t.root_span.name, "service": t.root_span.service} if t.root_span else None,
    })


@mcp.tool()
async def deep_analyze(trace_id: str, question: str | None = None) -> str:
    """Use MCP sampling for LLM-assisted trace analysis."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"

    t = traces[trace_id]
    context = json.dumps(t.model_dump(), default=str, indent=2)
    prompt = question or "Analyze this trace for performance issues and errors. Provide actionable insights."

    result = await mcp.get_context().session.create_message(
        messages=[{"role": "user", "content": f"Trace data:\n```json\n{context}\n```\n\n{prompt}"}],
        max_tokens=1000,
    )
    return result.content.text if hasattr(result.content, "text") else str(result.content)


@mcp.resource("trace://{trace_id}")
def get_trace(trace_id: str) -> str:
    """Get full trace data."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"
    return json.dumps(traces[trace_id].model_dump(), default=str)


@mcp.resource("trace://{trace_id}/spans")
def get_spans(trace_id: str) -> str:
    """Get spans for a trace."""
    if trace_id not in traces:
        return f"Trace not found: {trace_id}"
    return json.dumps([s.model_dump() for s in traces[trace_id].spans], default=str)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
