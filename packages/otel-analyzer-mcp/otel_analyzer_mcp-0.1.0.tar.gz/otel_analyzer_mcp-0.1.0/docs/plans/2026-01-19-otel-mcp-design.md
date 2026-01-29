# OTEL Trace Analysis MCP Server Design

## Overview

A Python-based MCP server for analyzing OpenTelemetry traces. Supports loading traces from files, strings, or directly from AWS X-Ray. Provides performance analysis, error diagnosis, and LLM-assisted deep analysis via MCP sampling.

## Use Cases

- **Performance Analysis**: Identify slow spans, latency breakdown, critical path through distributed traces
- **Error Diagnosis**: Find error spans, understand failure context, detect patterns

## Input Formats

| Format | Source |
|--------|--------|
| JSON (OTLP) | Standard OpenTelemetry JSON export |
| Jaeger | Jaeger UI JSON export |
| Protobuf | Binary OTLP format |
| X-Ray | Direct fetch via AWS SDK |

## Architecture

```text
otel-mcp/
├── pyproject.toml
├── src/
│   └── otel_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP server, tools, resources
│       ├── parsers.py         # Format detection and parsing
│       ├── models.py          # Normalized trace data structures
│       ├── xray.py            # X-Ray client wrapper
│       └── analyzers/
│           ├── __init__.py
│           ├── performance.py # Latency, critical path, slow spans
│           └── errors.py      # Error detection, context extraction
```

## Data Model

```python
@dataclass
class SpanEvent:
    name: str
    timestamp: datetime
    attributes: dict

@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_id: str | None
    name: str
    service: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status: str  # OK, ERROR, FAULT
    attributes: dict
    events: list[SpanEvent]

@dataclass
class Trace:
    trace_id: str
    source: str  # file path, "xray", "string"
    format: str  # json, jaeger, protobuf, xray
    spans: list[Span]
    root_span: Span | None
    services: set[str]
    has_errors: bool
```

All parsers normalize into this common model.

## MCP Tools (7)

| Tool | Description |
|------|-------------|
| `load_trace` | Load trace from file path, JSON string, or X-Ray trace ID. Auto-detects format. Optional: `profile`, `region` for X-Ray. |
| `search_xray` | Search X-Ray for traces. Params: `filter_expression`, `start_time`, `end_time`, `profile`, `region`. |
| `list_traces` | List all loaded traces with summaries (ID, services, duration, error count). |
| `analyze_performance` | Performance analysis: latency breakdown by service, slow spans, critical path. |
| `analyze_errors` | Error analysis: all error spans with context, exception details, failure patterns. |
| `summarize_trace` | High-level overview: services involved, total duration, span count, error summary. |
| `deep_analyze` | Uses MCP sampling for LLM-assisted analysis. Optional `question` param for focused inquiry. |

## MCP Resources (2)

| Resource | Description |
|----------|-------------|
| `trace://{trace_id}` | Full normalized trace data as JSON |
| `trace://{trace_id}/spans` | List of spans for a trace |

## Dependencies

```toml
[project]
name = "otel-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0.0",
    "opentelemetry-proto>=1.20.0",
    "boto3>=1.34.0",
    "pydantic>=2.0.0",
    "networkx>=3.0",
]

[project.scripts]
otel-mcp = "otel_mcp.server:main"
```

## Trace Store

In-memory dictionary keyed by trace ID:

```python
traces: dict[str, Trace] = {}
```

- File loads use filename (without extension) as ID
- X-Ray loads use the X-Ray trace ID
- String loads use a hash of the content

## Analysis Details

### Performance Analysis

- **Latency breakdown**: Aggregate duration by service
- **Slow spans**: Spans exceeding threshold (default: p95 or explicit ms)
- **Critical path**: Longest path through trace graph using networkx

### Error Analysis

- **Error detection**: Spans with ERROR/FAULT status or error events
- **Context extraction**: Parent/child spans around errors
- **Exception details**: Extract exception type, message, stack trace from events

## MCP Sampling

The `deep_analyze` tool uses MCP's `sampling/createMessage` to request LLM analysis:

1. Format trace data as structured context
2. Include specific question or use default analysis prompt
3. Return LLM's insights about patterns, root causes, recommendations

## Future Extensions

- Cost analysis (span counts, payload sizes)
- Trace comparison (diff two traces)
- Anomaly detection across multiple traces
