"""Performance analysis for traces."""

from collections import defaultdict

import networkx as nx

from ..models import Trace


def analyze_performance(trace: Trace, slow_threshold_ms: float | None = None) -> dict:
    """Comprehensive performance analysis of a trace."""
    if not trace.spans:
        return {"error": "No spans in trace"}

    # Latency breakdown by service
    service_durations = defaultdict(float)
    for span in trace.spans:
        service_durations[span.service] += span.duration_ms

    # Find slow spans (default: > p95 or explicit threshold)
    durations = sorted(s.duration_ms for s in trace.spans)
    p95 = durations[int(len(durations) * 0.95)] if durations else 0
    threshold = slow_threshold_ms or p95

    slow_spans = [
        {"span_id": s.span_id, "name": s.name, "service": s.service, "duration_ms": s.duration_ms}
        for s in trace.spans
        if s.duration_ms >= threshold
    ]

    # Critical path using networkx
    critical_path = _find_critical_path(trace)

    return {
        "total_duration_ms": trace.duration_ms,
        "span_count": len(trace.spans),
        "latency_by_service": dict(service_durations),
        "slow_threshold_ms": threshold,
        "slow_spans": sorted(slow_spans, key=lambda x: -x["duration_ms"]),
        "critical_path": critical_path,
    }


def _find_critical_path(trace: Trace) -> list[dict]:
    """Find the critical path through the trace."""
    if not trace.spans:
        return []

    G = nx.DiGraph()
    span_map = {s.span_id: s for s in trace.spans}

    # Add nodes with duration as weight
    for span in trace.spans:
        G.add_node(span.span_id, duration=span.duration_ms)

    # Add edges from parent to child
    for span in trace.spans:
        if span.parent_id and span.parent_id in span_map:
            G.add_edge(span.parent_id, span.span_id)

    # Find root(s) and leaf nodes
    roots = [n for n in G.nodes() if G.in_degree(n) == 0]
    leaves = [n for n in G.nodes() if G.out_degree(n) == 0]

    if not roots or not leaves:
        return []

    # Find longest path by duration
    longest_path = []
    max_duration = 0

    for root in roots:
        for leaf in leaves:
            try:
                for path in nx.all_simple_paths(G, root, leaf):
                    path_duration = sum(G.nodes[n]["duration"] for n in path)
                    if path_duration > max_duration:
                        max_duration = path_duration
                        longest_path = path
            except nx.NetworkXNoPath:
                continue

    return [
        {"span_id": sid, "name": span_map[sid].name, "service": span_map[sid].service, "duration_ms": span_map[sid].duration_ms}
        for sid in longest_path
        if sid in span_map
    ]
