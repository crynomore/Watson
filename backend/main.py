"""
main.py — Watson FastAPI backend.
Run: uvicorn main:app --host 127.0.0.1 --port 8000
"""
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from analyzer import analyze_request, PROVIDER, get_model

app = FastAPI(title="Watson AI Backend")

@app.post("/analyze")
async def analyze(data: dict) -> JSONResponse:
    return JSONResponse(content=analyze_request(data))

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": PROVIDER, "model": get_model()}

@app.get("/memory")
async def memory_snapshot() -> dict:
    import memory as mem
    return {"endpoints": list(mem.endpoint_memory.keys()),
            "object_graph_size": len(mem.object_graph),
            "summary": mem.get_summary()}
