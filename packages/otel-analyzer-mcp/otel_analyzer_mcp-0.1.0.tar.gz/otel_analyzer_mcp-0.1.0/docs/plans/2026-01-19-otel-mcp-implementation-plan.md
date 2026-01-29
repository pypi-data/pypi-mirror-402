# OTEL MCP Server Implementation Plan

## Phase 1: Project Setup & Core Models

1. Initialize project with `uv init` and configure `pyproject.toml`
2. Create package structure (`src/otel_mcp/`)
3. Implement `models.py` with Pydantic models (Span, SpanEvent, Trace)

## Phase 2: Parsers

4. Implement `parsers.py` with format detection
5. Add JSON (OTLP) parser
6. Add Jaeger format parser
7. Add Protobuf parser using `opentelemetry-proto`

## Phase 3: X-Ray Integration

8. Implement `xray.py` with boto3 client wrapper
9. Add trace fetching by ID
10. Add trace search with filter expressions

## Phase 4: Analyzers

11. Implement `analyzers/performance.py` (latency breakdown, slow spans, critical path)
12. Implement `analyzers/errors.py` (error detection, context extraction)

## Phase 5: MCP Server

13. Implement `server.py` with FastMCP
14. Add trace store and loading tools (`load_trace`, `list_traces`)
15. Add X-Ray tools (`search_xray`)
16. Add analysis tools (`analyze_performance`, `analyze_errors`, `summarize_trace`)
17. Add resources (`trace://{id}`, `trace://{id}/spans`)
18. Add `deep_analyze` with MCP sampling

## Phase 6: Testing & Polish

19. Add sample trace files for testing (JSON, Jaeger, X-Ray formats)
20. Manual testing of all tools
21. Add README with usage instructions

## Estimated Steps: 21

Each phase builds on the previous. Phases 2-4 can be partially parallelized.
