# MALCOM LangGraph Multi-Agent Orchestrator — Project Technical Documentation

Welcome to the technical documentation for **MALCOM**, an advanced, privacy-first, multi-agent AI orchestration platform built on top of **LangGraph**, **FastAPI**, **React**, and local **Ollama** + **Gemini** models.

This document details every module, function signature, tool, safety engine, event-sourced decision store, state schema, REST API endpoint, and UI component within our codebase.

---

## 📐 System Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                 React Frontend UI                                 |
|          (GStack Presets, Redactor Sandbox, Memory Timeline, Config Panel)         |
+-----------------------------------------------------------------------------------+
                                          |
                                   SSE Stream & REST API
                                          v
+-----------------------------------------------------------------------------------+
|                              FastAPI Server (api.py)                               |
+-----------------------------------------------------------------------------------+
                                          |
                                 LangGraph Pipeline
                                          v
+-----------------------+      +------------------------+      +--------------------+
|  Orchestrator Node    | ---> |   Specialized Workers  | ---> |  Synthesizer Node  |
| (Topic Breakdown)     |      |  (18 Agent Workflow)   |      |  (Final Synthesis) |
+-----------------------+      +------------------------+      +--------------------+
                                           |
                              +------------+------------+
                              |                         |
                              v                         v
                   +--------------------+    +---------------------+
                   | RedactEngine       |    | DecisionMemoryStore |
                   | (Secret Masking)   |    | (JSONL Store)       |
                   +--------------------+    +---------------------+
```

---

## 🛠️ Module-by-Module Technical Reference

### 1. Secret Redaction Engine — `orchestrator/redact_engine.py`

Guarantees zero secret leakage across all worker inputs, outputs, log streams, and audit targets.

#### Functions & Classes:

- **`shannon_entropy(s: str) -> float`**
  - *Description*: Calculates the Shannon entropy (in bits/char) of a string `s`. Used to differentiate random secret tokens/passwords from human-readable placeholders.
  - *Returns*: Floating point entropy value.

- **`luhn_valid(span: str) -> bool`**
  - *Description*: Validates credit card numbers using the Luhn checksum algorithm after stripping spaces and dashes.

- **`is_placeholder_span(span: str) -> bool`**
  - *Description*: Inspects matching spans to ignore structural and substring placeholders (e.g., `<your-key>`, `AKIAIOSFODNN7EXAMPLE`, `changeme`, `dummy`).

- **`RedactEngine` (Class)**
  - *Description*: Core engine containing regex patterns and validation rules for OpenAI, Anthropic, AWS, GitHub PATs, JWTs, Stripe keys, SendGrid keys, PEM private keys, DB connection URIs, credit cards, SSNs, and emails.
  - **`redact(self, text: str) -> Dict[str, Any]`**: Scans input text and replaces sensitive spans with replacement tokens (`<REDACTED-OPENAI-KEY>`, `<REDACTED-EMAIL>`, etc.).
  - *Returns*: `{"sanitized_text": str, "findings_count": int, "findings": List[Dict]}`.

- **`redact_text(text: str) -> str`**
  - *Description*: Utility wrapper returning only the sanitized string.

---

### 2. Event-Sourced Decision Memory — `orchestrator/decision_memory.py`

Maintains institutional memory, project patterns, and strategic decision logs.

#### Functions & Classes:

- **`DecisionMemoryStore` (Class)**
  - **`record_decision(decision: str, rationale: str = "", alternatives: str = "", scope: str = "repo", source: str = "agent", confidence: float = 0.9, workflow_role: str = "general") -> Dict[str, Any]`**:
    Appends an immutable, sanitized decision event to `knowledge_base/gstack_decisions.jsonl`.
  - **`record_learning(category: str, pattern: str, pitfall_or_guideline: str) -> Dict[str, Any]`**:
    Appends a project pattern or pitfall to `knowledge_base/gstack_learnings.jsonl`.
  - **`get_active_decisions(limit: int = 20) -> List[Dict[str, Any]]`**:
    Retrieves the latest recorded active technical decisions.
  - **`get_learnings(limit: int = 20) -> List[Dict[str, Any]]`**:
    Retrieves accumulated project learnings and guidelines.

---

### 3. Extended gstack Utilities — `orchestrator/gstack_extended.py`

Implements path protection, spec authoring, Diataxis documentation, DevEx audits, and canary benchmarks.

#### Functions & Classes:

- **`GStackExtendedEngine` (Class)**
  - **`freeze_path(filepath: str) -> Dict[str, Any]`**: Adds a file or directory path to `knowledge_base/frozen_files.json` to prevent edits/deletions.
  - **`unfreeze_path(filepath: str) -> Dict[str, Any]`**: Removes a path from frozen storage.
  - **`is_frozen(filepath: str) -> bool`**: Returns `True` if `filepath` is frozen.
  - **`create_spec(feature_name: str, problem_statement: str, technical_scope: str) -> str`**: Generates a quality-gated Markdown technical spec document (`/spec`).
  - **`generate_diataxis_docs(component_name: str, doc_type: str = "all") -> Dict[str, str]`**: Generates documentation formatted according to the Diataxis framework (Tutorial, How-To, Reference, Explanation).
  - **`run_devex_audit(onboarding_flow_description: str) -> str`**: Audits Time-To-Hello-World (TTHW) and developer onboarding friction points.
  - **`run_canary_benchmark(url_or_endpoint: str) -> str`**: Benchmarks latency, Core Web Vitals, and console error rates.

---

### 4. Custom LangChain Tools — `orchestrator/tools.py`

Exposes 24 specialized tools bound to worker agents:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `write_file_tool` | `file_path`, `content` | Writes content to a file on disk. |
| `read_file_tool` | `file_path` | Reads file content with dummy path detection. |
| `fetch_webpage_tool` | `url` | Fetches webpage text via HTTP & BeautifulSoup. |
| `query_knowledge_base` | `query` | Queries local Chroma vector database. |
| `list_directory_tool` | `directory_path` | Lists subdirectories and files on disk. |
| `scan_dependencies_tool` | `manifest_path` | Scans package manifests (`requirements.txt`, `package.json`, `pyproject.toml`). |
| `fetch_github_repo_tool` | `repo_url` | Clones/inspects external GitHub repositories. |
| `geoip_lookup_tool` | `ip_address` | Resolves country, city, and ISP for IP addresses. |
| `threat_intel_lookup_tool` | `ip_or_domain` | Checks IPs/domains against threat indicators. |
| `neural_threat_score_tool` | `packet_rate`, `packet_size_kb`, `connection_duration_hours`, `port_number` | Runs neural network traffic threat model. |
| `domain_category_tool` | `domain` | Classifies domain risk, TLD, and phishing keywords. |
| `redact_sensitive_content_tool` | `text` | Scans and redacts credentials from raw text. |
| `cso_security_scanner_tool` | `code_or_filepath` | Runs OWASP Top 10 + STRIDE threat analysis. |
| `investigate_root_cause_tool` | `symptom_description`, `file_context` | Executes Iron Law hypothesis-driven debugging. |
| `record_decision_tool` | `decision`, `rationale`, `scope` | Logs a decision into the decision store. |
| `query_gstack_memory_tool` | `query` | Fetches active decisions and project learnings. |
| `generate_ascii_architecture_tool` | `component_name`, `state_flow_description` | Generates ASCII architecture state diagrams. |
| `freeze_file_path_tool` | `filepath` | Freezes file path from edits. |
| `unfreeze_file_path_tool` | `filepath` | Unfreezes protected file path. |
| `create_technical_spec_tool` | `feature_name`, `problem_statement`, `technical_scope` | Authors quality-gated spec (/spec). |
| `generate_diataxis_docs_tool` | `component_name`, `doc_type` | Generates Diataxis framework documentation. |
| `devex_audit_tool` | `onboarding_flow_description` | Audits DevEx & TTHW friction points. |
| `canary_benchmark_tool` | `url_or_endpoint` | Measures Core Web Vitals & response latency. |
| `autoplan_pipeline_tool` | `feature_idea` | Runs automated CEO → Design → Eng review chain. |

---

### 5. Orchestrator Graph & Nodes — `orchestrator/agents.py`

Defines LLM initializations, worker delegation, critic evaluations, and synthesis.

#### Functions:

- **`get_node_llm(node_type: str)`**: Resolves LLM configuration for a worker node from `worker_config.json` (supports Ollama, Gemini, Groq, OpenAI, Anthropic, DeepSeek, TogetherAI, and Custom API).
- **`orchestrator(state: State) -> dict`**: Planner node that breaks down the topic into sub-tasks with worker assignments.
- **`human_approval(state: State) -> dict`**: Human-in-the-loop review node.
- **`worker_step(state: WorkerState) -> dict`**: Executes worker tasks, handles tool execution, and sanitizes output through `RedactEngine`.
- **`critic_step(state: WorkerState) -> dict`**: Evaluates worker output quality; auto-approves outputs >150 chars to avoid infinite loops.
- **`finalize_worker(state: WorkerState) -> dict`**: Formats completed task results for parent graph.
- **`synthesizer(state: State) -> dict`**: Synthesizes all completed worker results into a final Markdown report. Handles list/dict content formats and API rate limits cleanly.

---

### 6. State Definitions & Reducers — `orchestrator/states.py`

- **`reduce_keep(left: Any, right: Any) -> Any`**: Reducer function that updates scalar state fields without raising `InvalidConcurrentGraphUpdate` during parallel execution.
- **`WorkerTask` (Pydantic Model)**: Defines `task_id`, `description`, `worker_type`, `expected_output`, `dependencies`.
- **`OrchestratorPlan` (Pydantic Model)**: Defines `tasks`, `overall_strategy`, `final_goal`.
- **`State` (TypedDict)**: Parent graph state containing `topic`, `messages`, `plan`, `completed_tasks`, `results`, `final_report`, `iteration`, `status`, `feedback`, `uploaded_context`, `decisions`. All fields wrapped with `Annotated[..., reducer]`.
- **`WorkerState` (TypedDict)**: Subgraph worker state.

---

### 7. REST API Endpoints — `orchestrator/api.py`

- **`GET /health`**: Returns system health status, active graph nodes, and password configuration.
- **`POST /verify_password`**: Authenticates user against environment `APP_PASSWORD`.
- **`GET /config`**: Returns worker model settings and masked API key presence.
- **`POST /config/workers`**: Updates `worker_config.json` settings dynamically.
- **`POST /run`**: Executes the orchestrator synchronously.
- **`GET /run_stream`**: SSE endpoint streaming live execution logs, node steps, and synthesis reports.
- **`POST /api/redact`**: Accepts `{"text": "..."}` and returns sanitized text with secret findings count.
- **`GET /api/decisions`**: Returns active decisions from the decision store.
- **`GET /api/memory`**: Returns active decisions and accumulated project learnings.

---

### 8. React Frontend Application — `frontend/src/App.jsx`

- **GStack Workflow Launcher**: 15 preset workflow chips (`/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/autoplan`, `/spec`, `/plan-devex-review`, `/cso`, `/investigate`, `/document-generate`, `/canary`, `/freeze`, `/qa`, `/ship`, `/retro`).
- **GStack Memory & Secret Redactor Drawer**: Live timeline of recorded decisions and an interactive secret redaction testing sandbox.
- **Worker Config Manager**: UI panel allowing real-time switching of model backends (Ollama vs Gemini vs OpenAI) and temperature adjustments per agent.
- **Live SSE Event Stream**: Streams execution updates and renders synthesized Markdown reports.

---

## 🚀 Quick Run Commands

```powershell
# 1. Start FastAPI Backend Server
uv run uvicorn orchestrator.api:app --host 127.0.0.1 --port 8000 --reload

# 2. Start React Frontend UI (in /frontend)
cd frontend
npm run dev
```
