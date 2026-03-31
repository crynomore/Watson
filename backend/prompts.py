"""
prompts.py — all AI prompt templates in one place.

Import ANALYZE_PROMPT into analyzer.py instead of inlining raw strings.
"""

import json


def _format_watson_context(memory_ctx: dict) -> str:
    """
    Extracts Watson-side intelligence merged into memory_ctx by ai_reasoning()
    and formats it into a human-readable block for the prompt.
    """
    lines = []

    auth_events = memory_ctx.get("watson_auth_events", [])
    if auth_events:
        lines.append("Auth tokens observed this session:")
        for ev in auth_events[-8:]:
            lines.append(f"  [{ev.get('type','?')}] {ev.get('endpoint','?')} — {ev.get('note','')[:100]}")

    secrets = memory_ctx.get("watson_secrets_found", [])
    if secrets:
        lines.append("Secrets already discovered this session:")
        for s in secrets:
            lines.append(f"  [{s.get('verdict','?')}] {s.get('type','?')} in {s.get('source','?')}")

    endpoints = memory_ctx.get("watson_known_endpoints", [])
    if endpoints:
        lines.append(f"Known endpoints in scope ({len(endpoints)} total, last 10 shown):")
        for ep in endpoints[-10:]:
            lines.append(f"  {ep}")

    obj_rels = memory_ctx.get("watson_object_relationships", 0)
    findings = memory_ctx.get("watson_total_findings", 0)
    if obj_rels or findings:
        lines.append(f"Cross-request object relationships mapped: {obj_rels}")
        lines.append(f"Total findings this session: {findings}")

    return "\n".join(lines) if lines else "No Watson session context yet."


def build_analyze_prompt(features: dict, score: int,
                         severity: str, conf: str,
                         conf_score: int,
                         memory_ctx: dict,
                         already_tested: list) -> str:
    """
    Main analysis prompt.  Mirrors Burp Scanner advisory format.

    Parameters
    ----------
    features      : output of build_features()
    score         : integer from calculate_score()
    severity      : "High" / "Medium" / "Low" / "Info"
    conf          : "Firm" / "Tentative"
    conf_score    : integer
    memory_ctx    : output of memory.get_summary() merged with Watson session context
    already_tested: list of payload strings already tried
    """
    already_str = (
        ", ".join(already_tested[:10])
        if already_tested
        else "none"
    )

    watson_ctx = _format_watson_context(memory_ctx)

    # Strip Watson keys before serialising generic memory to avoid duplication
    generic_memory = {k: v for k, v in memory_ctx.items()
                      if not k.startswith("watson_")}

    return f"""You are an elite bug bounty hunter embedded inside Burp Suite (Watson extension).
Your job: produce a precise, evidence-based security advisory — NOT generic advice.
You have full context from this live testing session — use it to make smarter, non-redundant suggestions.

────────────────────────────────────────────
TRAFFIC FEATURES
────────────────────────────────────────────
{json.dumps(features, indent=2)}

────────────────────────────────────────────
SCORING
────────────────────────────────────────────
Risk score  : {score}
Severity    : {severity}
Confidence  : {conf} ({conf_score}/10)

────────────────────────────────────────────
WATSON SESSION INTELLIGENCE
────────────────────────────────────────────
{watson_ctx}

────────────────────────────────────────────
SERVER-SIDE SESSION MEMORY
────────────────────────────────────────────
{json.dumps(generic_memory, indent=2)}

Already-tested payloads for this endpoint:
{already_str}

────────────────────────────────────────────
INSTRUCTIONS
────────────────────────────────────────────
• Focus only on what the evidence actually shows.
• Cross-reference Watson session intelligence — if a secret or auth token was already
  found this session, prioritise attacks that leverage it (token reuse, credential stuffing,
  privilege escalation using discovered credentials).
• If the same endpoint has been tested before (check already-tested), suggest mutations
  not yet tried — do NOT repeat anything in "already-tested".
• If Watson has mapped object relationships, reason about IDOR across those endpoints.
• issue_detail   — cite exact parameter names, values, status codes.
• attack_ideas   — real attack techniques, not categories. Reference session context.
• next_tests     — exact payloads or mutations to try next.
• remediation    — concise, developer-facing fix.
• If nothing suspicious: severity = "Info", title = "No issue detected".

Return ONLY valid JSON. No markdown fences. No prose outside the object.

{{
  "title": "",
  "issue_type": "",
  "severity": "{severity}",
  "severity_score": {score},
  "confidence": "{conf}",
  "confidence_score": {conf_score},
  "issue_detail": ["..."],
  "issue_background": ["..."],
  "remediation": ["..."],
  "evidence": ["..."],
  "request_markers": ["..."],
  "response_markers": ["..."],
  "attack_ideas": ["..."],
  "next_tests": ["..."]
}}"""


# ── Diff-aware chat prompt ────────────────────────────────────────

def build_chat_prompt(question: str, request: str,
                      response: str, diff: str,
                      memory_ctx: dict) -> str:
    """
    Prompt used when the analyst asks a freeform question in the
    AI Repeater chat box, or when Watson sends a specialised analysis
    task (TOKEN_ANALYSIS, SECRET_SCAN, etc.).
    """
    watson_ctx = _format_watson_context(memory_ctx)
    generic_memory = {k: v for k, v in memory_ctx.items()
                      if not k.startswith("watson_")}

    # Detect Watson-internal task prefixes and give them a sharper instruction
    is_token_task  = question.startswith("TOKEN_ANALYSIS:")
    is_secret_task = question.startswith("SECRET_SCAN:")

    if is_token_task:
        role_line = (
            "You are an expert cryptographer and penetration tester specialising in "
            "authentication and session management vulnerabilities."
        )
        extra = (
            "Decode every JWT completely. Flag weak algorithms, missing expiry, "
            "over-broad scopes, predictable values, and missing security flags. "
            "Cross-reference with Watson session secrets already found."
        )
    elif is_secret_task:
        role_line = (
            "You are an expert in secrets management and cloud security, skilled at "
            "identifying exposed credentials in source code, config files, and JS bundles."
        )
        extra = (
            "Be thorough — secrets are often obfuscated or split across variables. "
            "Note the variable name, context, and first 24 chars of each value found. "
            "Do NOT flag placeholder values (YOUR_KEY, changeme, example, etc.)."
        )
    else:
        role_line = (
            "You are an expert penetration tester helping analyse a live request/response."
        )
        extra = "Answer the analyst's question precisely using all available context."

    return f"""{role_line}

Question / Task:
{question}

────────────────────────────────────────────
REQUEST (truncated to 2000 chars)
────────────────────────────────────────────
{request[:2000]}

────────────────────────────────────────────
RESPONSE (truncated to 2000 chars)
────────────────────────────────────────────
{response[:2000]}

────────────────────────────────────────────
DIFF SUMMARY
────────────────────────────────────────────
{diff or "No diff — first request."}

────────────────────────────────────────────
WATSON SESSION INTELLIGENCE
────────────────────────────────────────────
{watson_ctx}

────────────────────────────────────────────
SERVER-SIDE SESSION MEMORY
────────────────────────────────────────────
{json.dumps(generic_memory, indent=2)}

────────────────────────────────────────────
INSTRUCTIONS
────────────────────────────────────────────
{extra}
Return ONLY valid JSON. No markdown fences.

{{
  "title": "",
  "issue_type": "",
  "severity": "Info",
  "severity_score": 0,
  "confidence": "Tentative",
  "confidence_score": 4,
  "issue_detail": ["..."],
  "issue_background": ["..."],
  "remediation": ["..."],
  "evidence": ["..."],
  "request_markers": ["..."],
  "response_markers": ["..."],
  "attack_ideas": ["..."],
  "next_tests": ["..."]
}}"""