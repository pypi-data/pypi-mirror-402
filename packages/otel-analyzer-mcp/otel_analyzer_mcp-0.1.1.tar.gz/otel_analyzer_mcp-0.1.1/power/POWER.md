---
name: "otel-analyzer"
displayName: "OTEL Analyzer MCP"
description: "Analyze OpenTelemetry traces for performance issues and errors. Load traces from files, AWS X-Ray, or CloudWatch GenAI observability. Get latency breakdowns, find slow spans, identify errors, and analyze Bedrock agent traces."
keywords: ["opentelemetry", "otel", "traces", "xray", "observability", "performance", "debugging", "bedrock", "genai", "cloudwatch"]
author: "Joshua Samuel"
---

# OTEL Analyzer MCP

## Overview

The OTEL Analyzer MCP server enables AI assistants to analyze OpenTelemetry traces for debugging and performance optimization. Load traces from local files, JSON strings, AWS X-Ray, or CloudWatch GenAI observability (aws/spans), then analyze them for performance bottlenecks and errors.

## When to Use This Power

Use the OTEL Analyzer MCP when you need to:

- Analyze distributed traces for performance issues
- Find slow spans and latency bottlenecks
- Identify errors and exceptions in traces
- Query AWS X-Ray for traces matching filter criteria
- Analyze Bedrock AgentCore and GenAI application traces
- Get LLM-assisted deep analysis of complex traces

Do NOT use this power for:

- Collecting or instrumenting traces (use OpenTelemetry SDK)
- Real-time monitoring dashboards
- Metrics or logs analysis (traces only)

## Onboarding

### Prerequisites

- Python 3.11+ with `uv` or `uvx` available
- AWS credentials configured (for X-Ray/CloudWatch integration)
- Kiro with MCP Support configured

### Installation

The OTEL Analyzer MCP server is automatically configured when you install this power. No additional installation steps required.

## Tool Selection Guide

| Task | Tool | Example |
|------|------|---------|
| Load trace from file | `load_trace` | "Load trace.json" |
| Load from X-Ray | `load_trace` | "Load X-Ray trace 1-abc123" |
| Load from CloudWatch | `load_trace` | "Load trace abc123 from cloudwatch" |
| Search X-Ray traces | `search_xray` | "Find slow traces in us-east-1" |
| Search GenAI traces | `search_genai_traces` | "Find Bedrock agent traces" |
| List loaded traces | `list_traces` | "What traces are loaded?" |
| Get trace overview | `summarize_trace` | "Summarize this trace" |
| Find slow spans | `analyze_perf` | "Why is this trace slow?" |
| Find errors | `analyze_errs` | "What errors occurred?" |
| Deep analysis | `deep_analyze` | "Explain the root cause" |

## Tools Reference

### load_trace

Load a trace from file, JSON string, X-Ray, or CloudWatch. Auto-detects format.

**Parameters**:

- `path` - File path to trace JSON
- `data` - Raw JSON string
- `trace_id` - Trace ID to fetch from X-Ray or CloudWatch
- `source` - Source for trace_id: 'xray' (default) or 'cloudwatch'
- `region` - AWS region
- `profile` - AWS profile name

### search_xray

Search AWS X-Ray for traces matching a filter expression.

**Parameters**:

- `filter_expression` - X-Ray filter (e.g., `service("api") AND responseTime > 5`)
- `region` - AWS region
- `start_time` / `end_time` - Time range (ISO format)
- `limit` - Max results (default: 20)

### search_genai_traces

Search CloudWatch aws/spans for GenAI traces from Bedrock AgentCore.

**Parameters**:

- `filter_query` - CloudWatch Logs Insights filter (e.g., `name like /bedrock/`)
- `region` - AWS region
- `start_time` / `end_time` - Time range (ISO format)
- `limit` - Max results (default: 20)

Returns GenAI traces with model info, token usage, and latency.

### analyze_perf

Analyze trace performance: latency breakdown, slow spans, critical path.

**Parameters**:

- `trace_id` - ID of loaded trace
- `slow_threshold_ms` - Threshold for slow span detection

### analyze_errs

Analyze trace errors: error spans, exceptions, failure context.

**Parameters**:

- `trace_id` - ID of loaded trace

### deep_analyze

Use MCP sampling for LLM-assisted trace analysis.

**Parameters**:

- `trace_id` - ID of loaded trace
- `question` - Specific question about the trace

## Common Workflows

### Workflow 1: Analyze Local Trace File

```text
1. "Load the trace from ./traces/slow-request.json"
2. "Summarize this trace"
3. "Why is it slow? Analyze performance"
```

### Workflow 2: Debug X-Ray Traces

```text
1. "Search X-Ray for traces where responseTime > 5 seconds in us-east-1"
2. "Load the slowest trace"
3. "Analyze errors and performance"
```

### Workflow 3: Analyze Bedrock Agent Traces

```text
1. "Search for GenAI traces from the last hour"
2. "Load trace abc123 from cloudwatch"
3. "Analyze performance - check token usage and model latency"
```

### Workflow 4: Root Cause Analysis

```text
1. "Load trace 1-abc123-def456 from X-Ray"
2. "What errors occurred in this trace?"
3. "Deep analyze: what's the root cause of the failure?"
```

## Filter Expression Examples

### X-Ray Filters

```text
service("my-api")
service("my-api") AND responseTime > 5
service("my-api") AND error = true
annotation.user_id = "12345"
http.status = 500
```

### CloudWatch GenAI Filters

```text
name like /bedrock/
@message like /InvokeModel/
name like /gen_ai/ and @message like /claude/
```

## GenAI Trace Attributes

When analyzing GenAI traces, look for these OpenTelemetry semantic convention attributes:

- `gen_ai.system` - AI system (e.g., "aws.bedrock")
- `gen_ai.request.model` - Model ID
- `gen_ai.request.max_tokens` - Max tokens requested
- `gen_ai.usage.input_tokens` - Input token count
- `gen_ai.usage.output_tokens` - Output token count
- `gen_ai.response.finish_reasons` - Completion reason

## Best Practices

- Load traces before analyzing them
- Use `summarize_trace` first to understand trace structure
- Use `analyze_perf` for latency issues, `analyze_errs` for failures
- Use `deep_analyze` for complex root cause analysis
- For GenAI traces, check token usage for cost optimization
- Filter searches to reduce noise

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [AWS X-Ray Filter Expressions](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html)
- [CloudWatch GenAI Observability](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html)
- [GitHub Repository](https://github.com/jsamuel1/otel-analyzer-mcp)

---

**Package**: `otel-analyzer-mcp`
**MCP Server**: `otel-analyzer`
