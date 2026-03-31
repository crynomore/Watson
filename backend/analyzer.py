"""
analyzer.py — core analysis engine for Watson.

Supports three AI providers via a unified interface:
  • openai   — OpenAI GPT-4.1-mini  [DEFAULT]
  • claude   — Anthropic Claude Sonnet (best quality)
  • gemini   — Google Gemini 2.0 Flash (free tier, generous limits)

Set AI_PROVIDER in .env to switch. See README for recommendations.
"""

import os, re, json, base64
import memory, prompts

PROVIDER = os.getenv("AI_PROVIDER", "openai").lower().strip()

# ── Client init ───────────────────────────────────────────────────────────────
_client = None

def get_client():
    global _client
    if _client is not None:
        return _client
    if PROVIDER == "openai":
        from openai import OpenAI
        _client = OpenAI(
            api_key  = os.getenv("OPENAI_API_KEY"),
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    elif PROVIDER == "claude":
        try:
            import anthropic
            _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise RuntimeError("Run: pip install anthropic")
    elif PROVIDER == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            _client = genai
        except ImportError:
            raise RuntimeError("Run: pip install google-generativeai")
    else:
        raise ValueError(f"Unknown AI_PROVIDER='{PROVIDER}'. Valid: openai, claude, gemini")
    return _client

MODEL_DEFAULTS = {
    "openai": "gpt-4.1-mini",
    "claude": "claude-sonnet-4-5",
    "gemini": "gemini-2.0-flash",
}

def get_model():
    return os.getenv("MODEL", MODEL_DEFAULTS.get(PROVIDER, "gpt-4.1-mini"))

# ── Unified completion ────────────────────────────────────────────────────────
def complete(prompt: str) -> str:
    client = get_client()
    model  = get_model()
    if PROVIDER == "openai":
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=0.1, timeout=30,
        )
        return resp.choices[0].message.content.strip()
    elif PROVIDER == "claude":
        resp = client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    elif PROVIDER == "gemini":
        import google.generativeai as genai
        m = genai.GenerativeModel(model)
        resp = m.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=4096),
        )
        return resp.text.strip()
    raise ValueError(f"Unhandled provider: {PROVIDER}")

# ── Score bands ───────────────────────────────────────────────────────────────
SCORE_BANDS = [(8,"High","Firm",9),(5,"Medium","Firm",7),(3,"Low","Tentative",5),(0,"Info","Tentative",3)]

def score_to_bands(score):
    for t,sev,conf,cs in SCORE_BANDS:
        if score >= t: return sev,conf,cs
    return "Info","Tentative",3

# ── Parsing ───────────────────────────────────────────────────────────────────
def extract_endpoint(r):
    try:    return r.split("\n")[0].split(" ")[1]
    except: return "unknown"

def extract_method(r):
    try:    return r.split("\n")[0].split(" ")[0]
    except: return ""

def extract_status(r):
    try:    return int(r.split("\n")[0].split(" ")[1])
    except: return 0

def extract_headers(raw):
    h = {}
    try:
        for line in raw.split("\n"):
            if ":" in line:
                k,v = line.split(":",1); h[k.strip()] = v.strip()
    except: pass
    return h

def extract_params(request):
    p = {}
    try:
        if "?" in request:
            q = request.split("?",1)[1].split(" ")[0]
            for part in q.split("&"):
                if "=" in part: k,v = part.split("=",1); p[k] = v
    except: pass
    return p

def extract_cookies(headers):
    c = {}
    if "Cookie" not in headers: return c
    try:
        for chunk in headers["Cookie"].split(";"):
            chunk = chunk.strip()
            if "=" in chunk: k,v = chunk.split("=",1); c[k.strip()] = v.strip()
    except: pass
    return c

_B64 = re.compile(r'^[A-Za-z0-9+/=]+$')

def detect_encoding(value):
    if value.count(".")==2 and all(re.match(r'^[A-Za-z0-9\-_=]+$',s) for s in value.split(".")): return "JWT-like"
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',value,re.I): return "UUID"
    if re.match(r'^[0-9a-f]{32,64}$',value,re.I): return "Hash-like"
    if value.isdigit(): return "Numeric identifier"
    if len(value)>=8 and len(value)%4==0 and _B64.match(value):
        try: base64.b64decode(value,validate=True); return "Base64-like"
        except: pass
    return "Unknown"

# ── Feature extraction ────────────────────────────────────────────────────────
def build_features(request, response, diff):
    endpoint = extract_endpoint(request)
    params   = extract_params(request)
    headers  = extract_headers(request)
    cookies  = extract_cookies(headers)
    status   = extract_status(response)
    pf = {}
    for k,v in params.items():
        enc = detect_encoding(v); pf[k] = {"value":v,"encoding":enc,"length":len(v)}
        if enc in ("Numeric identifier","UUID","Hash-like"): memory.record_object(v,endpoint,k)
    cf = {k:{"encoding":detect_encoding(v),"length":len(v)} for k,v in extract_cookies(headers).items()}
    signals = []
    if status==200: signals.append("200 OK")
    if status==302: signals.append("302 redirect")
    if status==403: signals.append("403 access control")
    if status==401: signals.append("401 auth required")
    if status==500: signals.append("500 server error")
    if "authorization" in request.lower(): signals.append("Auth header present")
    if "set-cookie" in response.lower(): signals.append("Session cookie issued"); memory.mark_auth_endpoint(endpoint)
    if diff: signals.append(f"Diff: {diff}")
    return {"endpoint":endpoint,"method":extract_method(request),"params":pf,"cookies":cf,
            "signals":signals,"status":status,"param_count":len(params),"cookie_count":len(cf),
            "provider":PROVIDER,"model":get_model()}

def calculate_score(features):
    score = 0
    for p in features["params"]:
        pl = p.lower()
        if "id" in pl: score += 3
        if "token" in pl or "key" in pl: score += 2
        if "role" in pl or "admin" in pl or "perm" in pl: score += 3
        if "redirect" in pl or "url" in pl or "next" in pl: score += 2
    for _,meta in features["params"].items():
        enc = meta.get("encoding","")
        if enc=="Numeric identifier": score += 2
        if enc=="UUID":               score += 1
        if enc=="JWT-like":           score += 2
    for s in features["signals"]:
        if "403" in s: score += 2
        if "401" in s: score += 1
        if "500" in s: score += 3
        if "200" in s: score += 1
        if "Auth"    in s: score += 1
        if "Session" in s: score += 1
        if "Diff"    in s: score += 2
    return score

# ── AI reasoning ─────────────────────────────────────────────────────────────
def ai_reasoning(features, score, endpoint, question="", session_context=None):
    severity,conf,conf_score = score_to_bands(score)
    memory_ctx     = memory.get_summary()
    already_tested = memory.get_tested_payloads(endpoint,"")
    if session_context and isinstance(session_context,dict):
        memory_ctx["watson_auth_events"]         = session_context.get("auth_events",[])
        memory_ctx["watson_known_endpoints"]     = session_context.get("known_endpoints",[])
        memory_ctx["watson_secrets_found"]       = session_context.get("secrets_found",[])
        memory_ctx["watson_object_relationships"]= session_context.get("object_relationships",0)
        memory_ctx["watson_total_findings"]      = session_context.get("total_findings",0)
    if question:
        prompt = prompts.build_chat_prompt(question=question,
            request=features.get("_raw_request",""), response=features.get("_raw_response",""),
            diff=features.get("_diff",""), memory_ctx=memory_ctx)
    else:
        prompt = prompts.build_analyze_prompt(features=features, score=score,
            severity=severity, conf=conf, conf_score=conf_score,
            memory_ctx=memory_ctx, already_tested=already_tested)
    raw = complete(prompt)
    raw = re.sub(r"^```[a-z]*\n?","",raw); raw = re.sub(r"\n?```$","",raw); raw = raw.strip()
    parsed = json.loads(raw)
    missing = {"title","severity","confidence","issue_detail","attack_ideas","next_tests"} - parsed.keys()
    if missing: raise ValueError(f"LLM missing keys: {missing}")
    return json.dumps(parsed)

FALLBACK = {
    "title":"Analysis fallback","issue_type":"Informational","severity":"Info","severity_score":0,
    "confidence":"Tentative","confidence_score":4,"issue_detail":["AI reasoning failed."],
    "issue_background":[],"remediation":["Retry manually."],"evidence":[],"request_markers":[],
    "response_markers":[],"attack_ideas":["Manual review."],"next_tests":["Parameter mutation."],
}

def analyze_request(data: dict) -> dict:
    request  = data.get("request","");  response = data.get("response","")
    diff     = data.get("diff","");     question = data.get("question","")
    session_context = data.get("session_context",{})
    endpoint = extract_endpoint(request); params = extract_params(request); status = extract_status(response)
    memory.update_endpoint(endpoint,params,status)
    if isinstance(session_context,dict):
        for ae in session_context.get("auth_events",[]):
            ep = ae.get("endpoint",endpoint); memory.mark_auth_endpoint(ep)
            if ep not in memory.endpoint_memory: memory.update_endpoint(ep,{},0)
    features = build_features(request,response,diff)
    features.update({"_raw_request":request,"_raw_response":response,"_diff":diff,"_session_context":session_context})
    score = calculate_score(features)
    try:
        return json.loads(ai_reasoning(features,score,endpoint,question,session_context))
    except Exception as e:
        fb = dict(FALLBACK); fb["issue_background"] = [str(e)]; fb["severity_score"] = score; return fb
