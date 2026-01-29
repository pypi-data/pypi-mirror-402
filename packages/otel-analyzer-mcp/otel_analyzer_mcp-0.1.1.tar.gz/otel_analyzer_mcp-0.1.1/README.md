# OTEL Analyzer MCP Server

MCP server for analyzing OpenTelemetry traces with performance and error diagnosis.

## Features

- Load traces from files, strings, AWS X-Ray, or CloudWatch GenAI observability
- Auto-detect format (OTLP JSON, Jaeger, Protobuf, X-Ray)
- Performance analysis: latency breakdown, slow spans, critical path
- Error analysis: error detection, exception extraction, context
- GenAI trace analysis: Bedrock AgentCore, token usage, model latency
- MCP sampling for LLM-assisted deep analysis

## Installation

```bash
uv tool install otel-analyzer-mcp
```

Or for development:

```bash
uv sync
```

## Usage

Run the server:

```bash
otel-analyzer-mcp
```

Or add to your MCP client config:

```json
{
  "mcpServers": {
    "otel-analyzer-mcp": {
      "command": "otel-analyzer-mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `load_trace` | Load from file, JSON, X-Ray trace ID, or CloudWatch |
| `search_xray` | Search X-Ray with filter expressions |
| `search_genai_traces` | Search CloudWatch aws/spans for GenAI traces |
| `list_traces` | List all loaded traces |
| `analyze_perf` | Performance analysis (latency, slow spans, critical path) |
| `analyze_errs` | Error analysis (errors, exceptions, context) |
| `summarize_trace` | High-level trace overview |
| `deep_analyze` | LLM-assisted analysis via MCP sampling |

## Examples

Load a trace file:

```text
load_trace(path="/path/to/trace.json")
```

Search X-Ray:

```text
search_xray(filter_expression='service("my-api") AND responseTime > 5', region="us-east-1")
```

Search GenAI traces:

```text
search_genai_traces(filter_query='name like /bedrock/', region="us-east-1")
```

Load from CloudWatch:

```text
load_trace(trace_id="abc123", source="cloudwatch", region="us-east-1")
```

Analyze performance:

```text
analyze_perf(trace_id="abc123")
```

## License

MIT
