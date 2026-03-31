"""
memory.py — shared in-process memory for the AI assistant.

Imported by analyzer.py so there is a single source of truth.
"""

from collections import defaultdict


# ── Endpoint memory ──────────────────────────────────────────────
# endpoint_memory[endpoint] = {
#   "attempts": int,
#   "statuses": [int, ...],
#   "params":   {name: [value, ...]}
# }
endpoint_memory: dict = {}


# ── Object graph ─────────────────────────────────────────────────
# Tracks relationships between IDs seen across endpoints.
# object_graph[id_value] = {
#   "endpoints": [str, ...],
#   "params":    [str, ...]
# }
object_graph: dict = {}


# ── Test history ─────────────────────────────────────────────────
# Records every (endpoint, param, payload) combination that has
# already been tried so the AI doesn't suggest the same test twice.
# test_history[endpoint] = [ {"param": str, "payload": str,
#                              "status": int, "result": str}, ... ]
test_history: dict = defaultdict(list)


# ── Parameter frequency ──────────────────────────────────────────
# param_frequency[param_name] = int  (times seen across all traffic)
param_frequency: dict = defaultdict(int)


# ── Auth flow detection ──────────────────────────────────────────
# Stores endpoints that issued Set-Cookie or changed auth state.
auth_endpoints: list = []


# ─────────────────────────────────────────────────────────────────
# Mutators
# ─────────────────────────────────────────────────────────────────

def update_endpoint(endpoint: str, params: dict, status: int) -> None:
    """Record a request/response pair against an endpoint."""
    if endpoint not in endpoint_memory:
        endpoint_memory[endpoint] = {
            "attempts": 0,
            "statuses": [],
            "params":   {}
        }

    mem = endpoint_memory[endpoint]
    mem["attempts"] += 1
    mem["statuses"].append(status)

    for k, v in params.items():
        param_frequency[k] += 1
        if k not in mem["params"]:
            mem["params"][k] = []
        if v not in mem["params"][k]:
            mem["params"][k].append(v)


def record_object(id_value: str, endpoint: str, param: str) -> None:
    """Add an observed ID value to the object graph."""
    if id_value not in object_graph:
        object_graph[id_value] = {"endpoints": [], "params": []}
    node = object_graph[id_value]
    if endpoint not in node["endpoints"]:
        node["endpoints"].append(endpoint)
    if param not in node["params"]:
        node["params"].append(param)


def record_test(endpoint: str, param: str,
                payload: str, status: int, result: str) -> None:
    """Log a completed test so future suggestions skip duplicates."""
    test_history[endpoint].append({
        "param":   param,
        "payload": payload,
        "status":  status,
        "result":  result
    })


def mark_auth_endpoint(endpoint: str) -> None:
    if endpoint not in auth_endpoints:
        auth_endpoints.append(endpoint)


# ─────────────────────────────────────────────────────────────────
# Accessors
# ─────────────────────────────────────────────────────────────────

def get_endpoint_context(endpoint: str) -> dict:
    """Return everything remembered about a single endpoint."""
    return endpoint_memory.get(endpoint, {})


def get_tested_payloads(endpoint: str, param: str) -> list:
    """Return payloads already tried for (endpoint, param)."""
    return [
        t["payload"]
        for t in test_history.get(endpoint, [])
        if t["param"] == param
    ]


def get_top_params(n: int = 10) -> list:
    """Return the n most frequently seen parameter names."""
    return sorted(
        param_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n]


def get_summary() -> dict:
    """Compact snapshot used by the AI prompt for context."""
    return {
        "total_endpoints":  len(endpoint_memory),
        "total_objects":    len(object_graph),
        "top_params":       get_top_params(5),
        "auth_endpoints":   auth_endpoints[-10:],   # last 10
        "total_tests_run":  sum(
            len(v) for v in test_history.values()
        )
    }