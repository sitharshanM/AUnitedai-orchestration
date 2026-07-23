from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

# Import the compiled graph (app)
from .graph import app as graph_app

app = FastAPI()

# Enable CORS so the React app (on port 5173) can reach the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Security & Password Verification
# ---------------------------------------------------------------------------
class PasswordPayload(BaseModel):
    password: str

@app.post("/verify_password")
async def verify_password(payload: PasswordPayload):
    """Verifies user password against the environment APP_PASSWORD."""
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        return {"status": "authorized", "required": False}
        
    if payload.password == app_password:
        return {"status": "authorized", "required": True}
    else:
        raise HTTPException(status_code=401, detail="Access Denied: Incorrect Password")

def verify_token(password: str = ""):
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        return
    if password != app_password:
        raise HTTPException(status_code=401, detail="Access Denied: Password Required")

# ---------------------------------------------------------------------------
# Config Management Endpoints
# ---------------------------------------------------------------------------
from .config import load_config as get_worker_config, save_config as put_worker_config
import dotenv


class APIKeysPayload(BaseModel):
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""
    CUSTOM_API_KEY: str = ""
    CUSTOM_BASE_URL: str = ""

@app.get("/config")
async def get_config():
    """Returns both the worker models configuration and current API key presence (masked)."""
    env_file = dotenv.find_dotenv() or ".env"
    dotenv_vals = dotenv.dotenv_values(env_file)
    
    # Check key presence without revealing values for security
    keys_status = {
        "GOOGLE_API_KEY": bool(dotenv_vals.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "GROQ_API_KEY": bool(dotenv_vals.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")),
        "OPENAI_API_KEY": bool(dotenv_vals.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(dotenv_vals.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")),
        "DEEPSEEK_API_KEY": bool(dotenv_vals.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")),
        "TOGETHER_API_KEY": bool(dotenv_vals.get("TOGETHER_API_KEY") or os.environ.get("TOGETHER_API_KEY")),
        "CUSTOM_API_KEY": bool(dotenv_vals.get("CUSTOM_API_KEY") or os.environ.get("CUSTOM_API_KEY")),
        "CUSTOM_BASE_URL": dotenv_vals.get("CUSTOM_BASE_URL") or os.environ.get("CUSTOM_BASE_URL") or ""
    }
    
    return {
        "workers": get_worker_config(),
        "keys": keys_status
    }

@app.post("/config/workers")
async def update_worker_config(payload: dict, password: str = ""):
    """Updates the worker JSON configuration file."""
    verify_token(password)
    try:
        put_worker_config(payload)
        # Force reload current worker configuration in agents module
        from . import agents
        agents.worker_config = payload
        return {"status": "success", "message": "Worker configuration updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class APIKeysUpdatePayload(APIKeysPayload):
    password: str = ""

@app.post("/config/keys")
async def update_api_keys(payload: APIKeysUpdatePayload):
    """Updates the API keys inside the local .env file."""
    verify_token(payload.password)
    try:
        env_file = dotenv.find_dotenv()
        if not env_file:
            env_file = ".env"
            Path(env_file).touch()
            
        data = payload.model_dump()
        for k, v in data.items():
            if k == "password":
                continue
            if v.strip() or k == "CUSTOM_BASE_URL":  # update if non-empty or config url
                dotenv.set_key(env_file, k, v.strip())
                os.environ[k] = v.strip()
                
        return {"status": "success", "message": "API keys saved to .env file."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Serialization helper – graph results contain Pydantic & LangChain objects
# ---------------------------------------------------------------------------
def _serialize_result(obj):
    """Recursively converts a graph result dict into JSON-safe primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: _serialize_result(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_result(item) for item in obj]
    # LangChain message objects have a .content attribute
    if hasattr(obj, "content"):
        return {"type": getattr(obj, "type", "message"), "content": obj.content}
    # Fallback
    try:
        return str(obj)
    except Exception:
        return repr(obj)

# ---------------------------------------------------------------------------
# Health endpoint (already used by the UI)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    # graph_app is the compiled StateGraph. It has nodes, not agent_names directly.
    nodes = list(graph_app.nodes.keys()) if hasattr(graph_app, "nodes") else []
    
    # Check if a password is configured in the environment
    password_required = bool(os.getenv("APP_PASSWORD"))
    return {"status": "ok", "nodes": nodes, "password_required": password_required}

# ---------------------------------------------------------------------------
# Simple run endpoint (synchronous) – kept for compatibility
# ---------------------------------------------------------------------------
class RunPayload(BaseModel):
    topic: str
    password: str = ""

@app.post("/run")
async def run_topic(payload: RunPayload):
    # verify_token(payload.password)  # disabled for development
    init_state = {"topic": payload.topic}
    try:
        result = await asyncio.to_thread(graph_app.invoke, init_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return _serialize_result(result)

# ---------------------------------------------------------------------------
# Streaming run endpoint – Server‑Sent Events (SSE)
# ---------------------------------------------------------------------------
@app.get("/run_stream")
async def run_topic_stream(topic: str, context: str = "", password: str = ""):
    """Streams the orchestrator execution back to the client.

    Allows appending security audit context (e.g. uploaded files, target URL).
    """
    # verify_token(password)  # disabled for development

    async def event_generator() -> AsyncGenerator[bytes, None]:
        # Send a start event
        start_msg = json.dumps({"event": "started", "topic": topic})
        yield f"data: {start_msg}\n\n".encode()


        # Run the orchestrator in a thread to avoid blocking the event loop
        try:
            # Construct the graph inputs, matching the key structure expected by the workflow
            inputs = {
                "topic": topic,
                "uploaded_context": context
            }
            result = await asyncio.to_thread(graph_app.invoke, inputs)
            # Send the final result — serialize Pydantic objects
            serialized = _serialize_result(result)
            result_msg = json.dumps({"event": "finished", "result": serialized})
            yield f"data: {result_msg}\n\n".encode()
        except Exception as exc:
            err_msg = json.dumps({"event": "error", "detail": str(exc)})
            yield f"data: {err_msg}\n\n".encode()




    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ---------------------------------------------------------------------------
# gstack API Endpoints (Redaction, Decisions, Memory)
# ---------------------------------------------------------------------------
class RedactPayload(BaseModel):
    text: str

@app.post("/api/redact")
async def api_redact_text(payload: RedactPayload):
    from .redact_engine import default_redactor
    return default_redactor.redact(payload.text)

@app.get("/api/decisions")
async def api_get_decisions():
    from .decision_memory import default_memory_store
    return {"decisions": default_memory_store.get_active_decisions(limit=50)}

@app.get("/api/memory")
async def api_get_memory():
    from .decision_memory import default_memory_store
    return {
        "decisions": default_memory_store.get_active_decisions(limit=50),
        "learnings": default_memory_store.get_learnings(limit=50)
    }

@app.get("/api/tools")
async def api_get_tools_catalog():
    """Returns catalog of all available AI tools and descriptions for UI dropdown."""
    from .agents import GLOBAL_TOOL_REGISTRY
    tools_list = []
    seen = set()
    for key, tool in GLOBAL_TOOL_REGISTRY.items():
        tool_name = getattr(tool, "name", key)
        if tool_name in seen:
            continue
        seen.add(tool_name)
        desc = str(getattr(tool, "description", "No description available."))
        
        n_lower = tool_name.lower()
        if any(k in n_lower for k in ["sec", "scan", "threat", "cso", "geoip", "redact", "domain"]):
            cat = "🔒 Security & Threat Intel"
        elif any(k in n_lower for k in ["file", "directory", "freeze"]):
            cat = "💻 Filesystem & Code"
        elif any(k in n_lower for k in ["web", "fetch", "search", "github", "knowledge"]):
            cat = "🌐 Web Research & RAG"
        elif any(k in n_lower for k in ["spec", "diataxis", "ascii", "decision", "gstack"]):
            cat = "📐 Architecture & Docs"
        elif any(k in n_lower for k in ["test", "verification", "e2e", "investigate", "silent"]):
            cat = "🧪 QA & Debugging"
        else:
            cat = "⚡ Optimization & Harness"

        tools_list.append({
            "id": tool_name,
            "name": tool_name,
            "description": desc,
            "category": cat
        })
    return {"tools": tools_list}

