from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import os
import sys
import logging
import traceback
import hashlib
import subprocess
import re
from pathlib import Path
from typing import AsyncGenerator

from .domain import (
    Agent,
    AgentMessage,
    AgentStatus,
    ApprovalRequest,
    ApprovalResolution,
    ApprovalStatus,
    Artifact,
    BlackboardEntry,
    BlackboardEntryCreate,
    CommandRequest,
    Event,
    EventType,
    ExecutionAttempt,
    MessageType,
    ObjectiveControl,
    ObjectiveCreate,
    ObjectiveStatus,
    Permission,
    Task,
    TaskStatus,
    UsageRecord,
)
from .foundation_store import default_foundation_store
from .autonomy import default_workstation_service
from .structured_output import ModelRateLimitError

# ── Safe logging setup for graph print() calls ──────────────────────────────
# On Windows, writing to stdout from asyncio.to_thread can cause OSError
# [Errno 22] if the pipe handle is invalid. Use the Python logger instead.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
graph_logger = logging.getLogger("orchestrator.graph")


class _GeneratedFile(BaseModel):
    path: str
    content: str


class _GeneratedBundle(BaseModel):
    files: list[_GeneratedFile]

class _SafeStreamWriter:
    """Wraps sys.stdout to suppress [Errno 22] on Windows pipe writes."""
    def __init__(self, stream):
        self._stream = stream
    def write(self, s):
        try:
            self._stream.write(s)
        except OSError:
            pass  # Swallow Windows [Errno 22] from closed pipe handles
    def flush(self):
        try:
            self._stream.flush()
        except OSError:
            pass
    def __getattr__(self, name):
        return getattr(self._stream, name)

# Patch stdout/stderr globally so all print() inside threads stay safe
if sys.stdout and not isinstance(sys.stdout, _SafeStreamWriter):
    sys.stdout = _SafeStreamWriter(sys.stdout)
if sys.stderr and not isinstance(sys.stderr, _SafeStreamWriter):
    sys.stderr = _SafeStreamWriter(sys.stderr)

# Import the compiled graph (app)
from .graph import app as graph_app

app = FastAPI(title="Orchestrator Backend API", description="LangGraph Orchestration API with Scrapling Web Scraping Integration")


def _frontend_directory() -> Path:
    """Locate the compiled React UI in source and frozen desktop builds."""
    configured = os.getenv("AUNITEDAI_FRONTEND_DIR")
    if configured:
        return Path(configured).resolve()
    frozen_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    frozen_ui = frozen_root / "frontend_dist"
    return frozen_ui if frozen_ui.exists() else Path(__file__).resolve().parents[1] / "frontend" / "dist"

# Local-first CORS policy. Additional origins must be opted in explicitly.
cors_origins = [origin.strip() for origin in os.getenv(
    "AUNITEDAI_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    index = _frontend_directory() / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {
        "status": "online",
        "service": "Orchestrator LangGraph API",
        "documentation": "/docs",
        "health": "/health"
    }

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

# Load locally stored provider keys once when the backend starts. The Settings
# endpoint also updates the current process, but this makes a manual .env edit
# work after a normal backend restart.
dotenv.load_dotenv(override=False)


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
        "CUSTOM_API_KEY": bool(dotenv_vals.get("CUSTOM_API_KEY") or dotenv_vals.get("OPENROUTER_API_KEY") or os.environ.get("CUSTOM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")),
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
# AUnitedAI 2.0 foundation APIs
# ---------------------------------------------------------------------------
@app.post("/api/objectives", status_code=201)
async def create_objective(payload: ObjectiveCreate):
    """Create a durable objective and its first event."""
    objective = default_foundation_store.create_objective(payload)
    default_foundation_store.append_event(Event(
        type=EventType.OBJECTIVE_CREATED,
        project_id=objective.project_id,
        objective_id=objective.id,
        payload={"objective": objective.objective, "mode": objective.mode.value},
    ))
    return objective


@app.post("/api/workspaces", status_code=201)
async def create_autonomous_workspace(payload: ObjectiveCreate):
    """Turn one high-level objective into a persisted plan and dynamic organization."""
    objective = default_foundation_store.create_objective(payload)
    default_foundation_store.append_event(Event(
        type=EventType.OBJECTIVE_CREATED, project_id=objective.project_id,
        objective_id=objective.id, payload={"objective": objective.objective, "mode": objective.mode.value},
    ))
    return default_workstation_service.bootstrap(objective)


@app.get("/api/objectives")
async def list_objectives(project_id: str | None = None, limit: int = 100):
    return default_foundation_store.list_objectives(project_id=project_id, limit=limit)


@app.get("/api/objectives/{objective_id}")
async def get_objective(objective_id: str):
    objective = default_foundation_store.get_objective(objective_id)
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    return objective


@app.get("/api/workspaces/{objective_id}")
async def get_workspace(objective_id: str):
    snapshot = default_workstation_service.snapshot(objective_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    return snapshot


@app.get("/api/workspaces/{objective_id}/artifacts/{artifact_id}")
async def get_workspace_artifact(objective_id: str, artifact_id: str, download: bool = False):
    """Preview or download an artifact without exposing arbitrary filesystem paths."""
    artifact = default_foundation_store.get_entity("artifact", artifact_id, Artifact)
    if artifact is None or artifact.objective_id != objective_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    output_root = (Path.cwd() / "outputs" / objective_id).resolve()
    target = (Path.cwd() / artifact.path).resolve()
    try:
        target.relative_to(output_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Artifact path is outside the objective output directory")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact file is missing")
    if download:
        return FileResponse(target, filename=artifact.name, media_type="application/octet-stream")
    if target.stat().st_size > 1_000_000:
        raise HTTPException(status_code=413, detail="Artifact is too large to preview")
    if target.suffix.lower() not in {".md", ".txt", ".json", ".csv", ".py", ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".yml", ".yaml", ".toml"}:
        raise HTTPException(status_code=415, detail="This artifact can be downloaded but not previewed")
    return {"name": artifact.name, "path": artifact.path, "content": target.read_text(encoding="utf-8", errors="replace")}


@app.get("/api/workspaces/{objective_id}/graph")
async def get_knowledge_graph(objective_id: str):
    if default_foundation_store.get_objective(objective_id) is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    return default_workstation_service.knowledge_graph(objective_id)


@app.post("/api/objectives/{objective_id}/control")
async def control_objective(objective_id: str, payload: ObjectiveControl):
    action_map = {
        "pause": ObjectiveStatus.PAUSED, "resume": ObjectiveStatus.RUNNING,
        "cancel": ObjectiveStatus.CANCELLED, "replan": ObjectiveStatus.PLANNING,
    }
    status = action_map.get(payload.action.lower())
    if status is None:
        raise HTTPException(status_code=422, detail="Action must be pause, resume, cancel, or replan")
    objective = default_foundation_store.update_objective_status(objective_id, status)
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    if payload.action.lower() == "replan":
        result = default_workstation_service.bootstrap(objective)
        default_foundation_store.append_event(Event(
            type=EventType.REPLAN_TRIGGERED, project_id=objective.project_id,
            objective_id=objective.id, payload={"reason": payload.reason},
        ))
        return result
    return objective


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, payload: dict):
    task = default_foundation_store.get_entity("task", task_id, Task)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    allowed = {key: value for key, value in payload.items() if key in {"status", "owner_agent_id", "description"}}
    try:
        updated = task.model_copy(update={**allowed, "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)})
        if "status" in allowed:
            updated = Task.model_validate(updated.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    default_foundation_store.save_entity("task", updated)
    event_type = EventType.TASK_COMPLETED if updated.status == TaskStatus.DONE else EventType.TASK_FAILED if updated.status == TaskStatus.FAILED else EventType.TASK_STARTED
    default_foundation_store.append_event(Event(
        type=event_type, project_id=default_foundation_store.get_objective(updated.objective_id).project_id,
        objective_id=updated.objective_id, task_id=updated.id, agent_id=updated.owner_agent_id,
        payload={"status": updated.status.value},
    ))
    return updated


@app.patch("/api/agents/{agent_id}")
async def update_agent(agent_id: str, payload: dict):
    agent = default_foundation_store.get_entity("agent", agent_id, Agent)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    allowed = {key: value for key, value in payload.items() if key in {"status", "model"}}
    try:
        updated = Agent.model_validate(agent.model_copy(update=allowed).model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    default_foundation_store.save_entity("agent", updated)
    if updated.status == AgentStatus.TERMINATED:
        objective = default_foundation_store.get_objective(updated.objective_id)
        default_foundation_store.append_event(Event(
            type=EventType.AGENT_TERMINATED, project_id=objective.project_id,
            objective_id=objective.id, agent_id=updated.id, payload={"name": updated.name},
        ))
    return updated


@app.post("/api/messages", status_code=201)
async def send_agent_message(payload: AgentMessage):
    existing = default_foundation_store.list_messages(payload.objective_id)
    violation = default_workstation_service.guard.check_message(payload, existing)
    if violation:
        raise HTTPException(status_code=409, detail=violation)
    stored = default_foundation_store.save_entity("message", payload)
    objective = default_foundation_store.get_objective(payload.objective_id)
    default_foundation_store.append_event(Event(
        type=EventType.MESSAGE_SENT, project_id=objective.project_id,
        objective_id=objective.id, task_id=payload.task_id, agent_id=payload.sender_agent_id,
        payload={"message_id": payload.id, "type": payload.type.value, "recipient": payload.recipient_agent_id},
    ))
    return stored


@app.post("/api/approvals", status_code=201)
async def request_approval(payload: ApprovalRequest):
    objective = default_foundation_store.get_objective(payload.objective_id)
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    risk, automatically_allowed = default_workstation_service.permissions.evaluate(payload.permission, objective.mode)
    request = payload.model_copy(update={"risk": risk})
    if automatically_allowed:
        request = request.model_copy(update={"status": ApprovalStatus.APPROVED})
    return default_foundation_store.save_entity("approval", request)


@app.patch("/api/approvals/{approval_id}")
async def resolve_approval(approval_id: str, payload: ApprovalResolution):
    approval = default_foundation_store.resolve_approval(approval_id, payload.status, payload.edited_action)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@app.post("/api/usage", status_code=201)
async def record_usage(payload: UsageRecord):
    try:
        return default_workstation_service.record_usage(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/api/attempts", status_code=201)
async def record_attempt(payload: ExecutionAttempt, max_attempts: int = 3):
    return default_workstation_service.record_attempt(payload, max_attempts=max_attempts)


@app.post("/api/workspaces/{objective_id}/command")
async def run_context_command(objective_id: str, payload: CommandRequest):
    snapshot = default_workstation_service.snapshot(objective_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    command = payload.command.lower()
    if "blocker" in command:
        result = [task for task in snapshot["tasks"] if task.status == TaskStatus.BLOCKED]
    elif "expensive" in command or "cost" in command:
        result = sorted(snapshot["usage"], key=lambda item: item.estimated_cost, reverse=True)
    elif "plan" in command:
        result = snapshot["plan"]
    elif "why" in command:
        result = {"summary": "Actions are derived from the objective, validated DAG dependencies, assigned capabilities, recorded evidence, and execution mode.",
                  "events": snapshot["events"][-5:]}
    else:
        result = {"summary": "Command understood as a workspace query.", "metrics": snapshot["metrics"], "observer": snapshot["observer"]}
    return {"command": payload.command, "result": result}


@app.post("/api/workspaces/{objective_id}/execute")
async def execute_workspace(objective_id: str):
    """Execute through the existing LangGraph while persisting lifecycle evidence."""
    objective = default_foundation_store.get_objective(objective_id)
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found")
    if objective.status in {ObjectiveStatus.CANCELLED, ObjectiveStatus.PAUSED}:
        raise HTTPException(status_code=409, detail=f"Objective is {objective.status.value}")
    tasks = default_foundation_store.list_tasks(objective_id)
    agents = {agent.id: agent for agent in default_foundation_store.list_agents(objective_id)}
    for task in tasks:
        if task.status == TaskStatus.READY:
            running = task.model_copy(update={"status": TaskStatus.RUNNING})
            default_foundation_store.save_entity("task", running)
            default_foundation_store.append_event(Event(
                type=EventType.TASK_STARTED, project_id=objective.project_id,
                objective_id=objective.id, task_id=task.id, agent_id=task.owner_agent_id,
                payload={"title": task.title},
            ))
            if task.owner_agent_id in agents:
                default_foundation_store.save_entity(
                    "agent", agents[task.owner_agent_id].model_copy(update={"status": AgentStatus.WORKING})
                )
    try:
        output_root = (Path.cwd() / "outputs" / objective.id).resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        execution_topic = (
            f"{objective.objective}\n\n"
            f"MANDATORY OUTPUT DIRECTORY: outputs/{objective.id}/\n"
            "All requested source code, manifests, tests, and documentation must be written as real files "
            "inside that directory using write_file_tool. Do not claim creation, builds, or passing tests "
            "unless the corresponding file or tool evidence exists."
        )
        result = await asyncio.to_thread(graph_app.invoke, {"topic": execution_topic})
        serialized = _serialize_result(result)
        raw_report = str(serialized.get("final_report") or "Execution returned no final report.")
        files = [path for path in output_root.rglob("*") if path.is_file()]

        # Some local models can generate good code but do not reliably emit native
        # tool calls. Materialize their structured code output server-side, within
        # the already constrained objective directory, then verify it independently.
        materialization_error = ""
        if not files:
            try:
                from .agents import get_node_llm
                worker_context = json.dumps(serialized.get("results") or [], ensure_ascii=False)[:24_000]
                artifact_prompt = f"""You are the artifact materializer for a local coding workstation.
Create the complete, minimal set of REAL files required for this objective:

{objective.objective}

Prior worker context (may contain unsupported claims; use only useful technical content):
{worker_context}

Return structured files only. Paths must be relative, contain no '..', and be beneath the output directory.
For Python software include working source code, a unittest file named test_*.py containing at least one real test,
and README.md. Prefer the standard library. Do not use Markdown fences inside file content unless the file needs them.
"""
                from langchain_core.prompts import ChatPromptTemplate
                from .agents import invoke_structured_resilient
                materializer_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You materialize safe, minimal project files."),
                    ("user", "{request}"),
                ])
                bundle = await asyncio.to_thread(
                    invoke_structured_resilient,
                    materializer_prompt,
                    get_node_llm("coding"),
                    _GeneratedBundle,
                    {"request": artifact_prompt},
                    "synthesizer",
                )
                for generated in bundle.files:
                    relative_path = Path(generated.path.replace("\\", "/"))
                    if relative_path.is_absolute() or ".." in relative_path.parts:
                        continue
                    target = (output_root / relative_path).resolve()
                    try:
                        target.relative_to(output_root)
                    except ValueError:
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(generated.content, encoding="utf-8")
                files = [path for path in output_root.rglob("*") if path.is_file()]
                if not files:
                    materialization_error = "Coding model returned no safe files."
            except Exception as exc:
                materialization_error = f"Artifact materialization failed: {type(exc).__name__}: {exc}"
        existing_paths = {artifact.path for artifact in default_foundation_store.list_artifacts(objective.id)}
        artifacts = []
        for path in files:
            relative = path.relative_to(Path.cwd()).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            artifact = Artifact(
                objective_id=objective.id, path=relative, name=path.name,
                size_bytes=path.stat().st_size, sha256=digest,
                verified=path.stat().st_size > 0,
            )
            if relative not in existing_paths:
                default_foundation_store.save_entity("artifact", artifact)
            artifacts.append(artifact)

        test_files = [path for path in files if "test" in path.name.lower()]
        test_output = "No executable test suite was discovered."
        test_evidence = False
        python_files = [path for path in files if path.suffix.lower() == ".py"]
        syntax_ok = True
        syntax_messages = []
        for python_file in python_files:
            try:
                compile(python_file.read_text(encoding="utf-8"), str(python_file), "exec")
            except (SyntaxError, UnicodeError) as exc:
                syntax_ok = False
                syntax_messages.append(f"{python_file.name}: {exc}")
        if test_files and syntax_ok:
            completed_tests = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "unittest", "discover", "-s", str(output_root), "-p", "test*.py", "-v"],
                capture_output=True, text=True, timeout=60,
            )
            test_output = (completed_tests.stdout + "\n" + completed_tests.stderr).strip()
            match = re.search(r"Ran\s+(\d+)\s+tests?", test_output)
            test_evidence = completed_tests.returncode == 0 and bool(match) and int(match.group(1)) > 0
        elif syntax_messages:
            test_output = "Syntax verification failed:\n" + "\n".join(syntax_messages)
        tangible_required = any("engineering" in task.required_capabilities for task in tasks)
        artifacts_verified = bool(artifacts) if tangible_required else True
        # Executable projects need executable proof. Research/writing objectives
        # are quality-gated by the worker critic and do not fail merely because
        # they have no unit-test suite.
        verification_ok = artifacts_verified and (
            test_evidence if tangible_required and any(task.verification_requirements for task in tasks) else True
        )
        delivery_status = "verified" if tangible_required and verification_ok else "complete" if verification_ok else "incomplete"

        compact_test_output = test_output
        if len(compact_test_output) > 20_000:
            compact_test_output = compact_test_output[:20_000].rstrip() + "\n[Verification output truncated]"
        verification_summary = (
            f"VERIFICATION STATUS: {'VERIFIED' if verification_ok else 'INCOMPLETE'}\n"
            f"Real artifacts found: {len(artifacts)}\n"
            f"Test files found: {len(test_files)}\n"
            f"Test-pass evidence: {'yes' if test_evidence else 'no'}\n"
            f"Artifact directory: outputs/{objective.id}/\n\n"
            f"Materialization: {materialization_error or 'completed'}\n\n"
            f"REAL TEST OUTPUT:\n{compact_test_output}\n\n"
            "The final model-generated report is stored separately as the delivery."
        )
        updated_tasks = []
        for task in default_foundation_store.list_tasks(objective_id):
            is_implementation = "engineering" in task.required_capabilities
            is_verification = "qa" in task.required_capabilities or bool(task.verification_requirements)
            if verification_ok:
                new_status = TaskStatus.DONE
            elif is_implementation and not artifacts_verified:
                new_status = TaskStatus.FAILED
            elif is_verification:
                new_status = TaskStatus.BLOCKED
            else:
                new_status = TaskStatus.REVIEW
            updated = task.model_copy(update={"status": new_status})
            default_foundation_store.save_entity("task", updated)
            updated_tasks.append(updated)
            event_type = EventType.TASK_COMPLETED if new_status == TaskStatus.DONE else EventType.TASK_FAILED if new_status == TaskStatus.FAILED else EventType.TASK_STARTED
            default_foundation_store.append_event(Event(
                type=event_type, project_id=objective.project_id, objective_id=objective.id,
                task_id=task.id, agent_id=task.owner_agent_id,
                payload={"title": task.title, "status": new_status.value,
                         "evidence": [artifact.path for artifact in artifacts]},
            ))
        for agent in agents.values():
            owned = [task for task in updated_tasks if task.owner_agent_id == agent.id]
            status = AgentStatus.COMPLETED if owned and all(task.status == TaskStatus.DONE for task in owned) else AgentStatus.BLOCKED
            default_foundation_store.save_entity("agent", agent.model_copy(update={"status": status}))
        default_foundation_store.add_blackboard_entry(BlackboardEntry(
            type="task_result", project_id=objective.project_id, objective_id=objective.id,
            content=verification_summary,
            evidence=[artifact.path for artifact in artifacts] + ([compact_test_output] if test_evidence else []),
            confidence=1.0 if verification_ok else 0.2,
        ))
        default_foundation_store.add_blackboard_entry(BlackboardEntry(
            type="task_result", project_id=objective.project_id, objective_id=objective.id,
            content=raw_report,
            evidence=[artifact.path for artifact in artifacts],
            confidence=1.0 if verification_ok else 0.5,
            metadata={
                "kind": "delivery",
                "verification_status": delivery_status,
                "artifact_count": len(artifacts),
                "test_evidence": test_evidence,
            },
        ))
        final_status = ObjectiveStatus.COMPLETED if verification_ok else ObjectiveStatus.FAILED
        default_foundation_store.update_objective_status(objective.id, final_status)
        if verification_ok:
            default_foundation_store.append_event(Event(
                type=EventType.OBJECTIVE_COMPLETED, project_id=objective.project_id,
                objective_id=objective.id, payload={"verified": True, "artifacts": len(artifacts)},
            ))
        else:
            default_foundation_store.append_event(Event(
                type=EventType.TASK_FAILED, project_id=objective.project_id,
                objective_id=objective.id,
                payload={"verified": False, "reason": "Required artifact or test evidence is missing"},
            ))
        return {
            "result": serialized,
            "delivery": {
                "content": raw_report,
                "verification_status": delivery_status,
                "artifacts": [_serialize_result(artifact) for artifact in artifacts],
                "test_evidence": test_evidence,
            },
            "workspace": default_workstation_service.snapshot(objective.id),
        }
    except ModelRateLimitError as exc:
        default_foundation_store.update_objective_status(objective.id, ObjectiveStatus.FAILED)
        raise HTTPException(status_code=429, detail=str(exc))
    except Exception as exc:
        ready = default_foundation_store.list_tasks(objective_id)
        active = next((task for task in ready if task.status == TaskStatus.RUNNING), None)
        if active:
            failed = active.model_copy(update={"status": TaskStatus.FAILED})
            default_foundation_store.save_entity("task", failed)
            default_foundation_store.append_event(Event(
                type=EventType.TASK_FAILED, project_id=objective.project_id,
                objective_id=objective.id, task_id=active.id, agent_id=active.owner_agent_id,
                payload={"error": type(exc).__name__, "recoverable": True},
            ))
        default_foundation_store.update_objective_status(objective.id, ObjectiveStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")


@app.get("/api/workspaces/{objective_id}/events/stream")
async def stream_workspace_events(objective_id: str, after_sequence: int = 0):
    objective = default_foundation_store.get_objective(objective_id)
    if objective is None:
        raise HTTPException(status_code=404, detail="Objective not found")

    async def persisted_events() -> AsyncGenerator[bytes, None]:
        cursor = after_sequence
        idle_ticks = 0
        while idle_ticks < 120:
            events = default_foundation_store.list_events(
                objective.project_id, objective_id=objective_id, after_sequence=cursor, limit=200
            )
            if events:
                idle_ticks = 0
                for event in events:
                    cursor = event["sequence"]
                    yield f"data: {json.dumps(event)}\n\n".encode()
            else:
                idle_ticks += 1
                yield b": keepalive\n\n"
            current = default_foundation_store.get_objective(objective_id)
            if current and current.status in {ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.CANCELLED} and not events:
                break
            await asyncio.sleep(1)

    return StreamingResponse(persisted_events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "X-Accel-Buffering": "no",
    })


@app.get("/api/events")
async def list_events(project_id: str = "default", objective_id: str | None = None,
                      after_sequence: int = 0, limit: int = 200):
    return default_foundation_store.list_events(
        project_id=project_id,
        objective_id=objective_id,
        after_sequence=after_sequence,
        limit=limit,
    )


@app.post("/api/blackboard", status_code=201)
async def add_blackboard_entry(payload: BlackboardEntryCreate):
    entry = default_foundation_store.add_blackboard_entry(BlackboardEntry(**payload.model_dump()))
    if entry.type.value == "decision":
        default_foundation_store.append_event(Event(
            type=EventType.DECISION_CREATED,
            project_id=entry.project_id,
            objective_id=entry.objective_id,
            task_id=entry.task_id,
            agent_id=entry.author_agent_id,
            payload={"blackboard_entry_id": entry.id, "content": entry.content},
        ))
    return entry


@app.get("/api/blackboard")
async def query_blackboard(project_id: str = "default", objective_id: str | None = None,
                           entry_type: str | None = None, task_id: str | None = None,
                           agent_id: str | None = None, domain: str | None = None,
                           min_confidence: float | None = None, limit: int = 100):
    return default_foundation_store.query_blackboard(
        project_id=project_id,
        objective_id=objective_id,
        entry_type=entry_type,
        task_id=task_id,
        agent_id=agent_id,
        domain=domain,
        min_confidence=min_confidence,
        limit=limit,
    )

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

        try:
            inputs = {
                "topic": topic,
                "uploaded_context": context
            }

            def _safe_invoke(graph_inputs: dict):
                """Wraps graph_app.invoke to catch OSError [Errno 22] from Windows pipe writes inside threads and redirects stdout to in-memory buffer."""
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    try:
                        return graph_app.invoke(graph_inputs)
                    except OSError as oe:
                        if oe.errno == 22:
                            import time
                            time.sleep(0.5)
                            return graph_app.invoke(graph_inputs)
                        raise

            # Execute graph.invoke in thread while sending SSE keep-alive heartbeats to keep the connection alive
            loop = asyncio.get_running_loop()
            task_future = loop.create_task(asyncio.to_thread(_safe_invoke, inputs))
            
            while not task_future.done():
                await asyncio.sleep(1.5)
                # SSE heartbeat comment line (ignored by EventSource JSON parsing, prevents browser/proxy drop)
                yield b": keepalive\n\n"

            result = await task_future
            serialized = _serialize_result(result)
            result_msg = json.dumps({"event": "finished", "result": serialized})
            yield f"data: {result_msg}\n\n".encode()
        except Exception as exc:
            tb = traceback.format_exc()
            graph_logger.error("SSE stream error: %s\n%s", exc, tb)
            err_msg = json.dumps({"event": "error", "detail": f"{type(exc).__name__}: {exc}", "traceback": tb})
            yield f"data: {err_msg}\n\n".encode()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

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


# This mount intentionally comes last so every API route takes precedence.
# In the packaged app it lets FastAPI serve the React build on the same private
# loopback origin, removing CORS and visible localhost setup from the UX.
_desktop_frontend = _frontend_directory()
if _desktop_frontend.is_dir():
    app.mount("/", StaticFiles(directory=_desktop_frontend, html=True), name="desktop-ui")

