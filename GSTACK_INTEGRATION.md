# 🚀 gstack Function Reference & Integration Manual

Comprehensive reference documentation detailing all extracted functions, modules, safety engines, institutional decision stores, specialized agent roles, and tools from [`garrytan/gstack`](https://github.com/garrytan/gstack) integrated into the **LangGraph** multi-agent orchestration system.

---

## 📐 1. Architecture Overview

`gstack` turns a generic AI assistant into a virtual software factory. The extracted codebase in `langgraph` consists of 5 primary core layers:

```mermaid
graph TD
    A[React Frontend UI & REST API] --> B[LangGraph Multi-Agent Orchestrator]
    B --> C[Safety & Secret Redaction Engine]
    B --> D[Event-Sourced Decision Memory]
    B --> E[Extended gstack Tool Suite]
    E --> F[Local Ollama & Multi-Model Backends]
```

---

## 🛡️ 2. Secret Redaction Engine (`orchestrator/redact_engine.py`)

Ported from `gstack/lib/redact-patterns.ts` and `redact-engine.ts`. Scans and masks sensitive credentials, API keys, passwords, and PII before data is passed to LLMs or written to logs.

### Functions:

#### `shannon_entropy(s: str) -> float`
- **Description**: Calculates Shannon entropy in bits per character. Used to filter out low-entropy variable assignments (e.g. `KEY=changeme`) while flagging high-entropy secrets.

#### `luhn_valid(span: str) -> bool`
- **Description**: Validates credit card numbers using the Luhn checksum algorithm.

#### `is_placeholder_span(span: str) -> bool`
- **Description**: Evaluates whether a matched secret string is a structural or substring placeholder (e.g. `<REDACTED-*>`, `AKIAIOSFODNN7EXAMPLE`, `your-key-here`).

#### `RedactEngine.redact(text: str) -> Dict[str, Any]`
- **Description**: Core scanner method. Applies 17 regex pattern groups (OpenAI, Anthropic, AWS, GitHub PATs, SendGrid, Stripe, Slack webhooks, JWTs, DB URIs with passwords, credit cards, SSNs, emails) and replaces matches with masked tokens.
- **Returns**: `{"sanitized_text": str, "findings_count": int, "findings": List[Dict]}`

#### `redact_text(text: str) -> str`
- **Description**: Convenience global function wrapper for `RedactEngine.redact()`. Used automatically across all worker node outputs in `agents.py`.

---

## 🧠 3. Event-Sourced Decision Memory Store (`orchestrator/decision_memory.py`)

Ported from `gstack/lib/gstack-decision.ts` and `gstack/lib/gstack-memory-helpers.ts`. Maintains an append-only JSONL log of technical decisions and compounding project learnings.

### Functions:

#### `DecisionMemoryStore.record_decision(decision, rationale, alternatives, scope, source, confidence, workflow_role) -> Dict[str, Any]`
- **Description**: Appends a structured decision event (`gstack_decisions.jsonl`). Automatically sanitizes text fields using `redact_text()`.
- **Scopes**: `repo`, `branch`, `issue`.

#### `DecisionMemoryStore.record_learning(category, pattern, pitfall_or_guideline) -> Dict[str, Any]`
- **Description**: Logs compounding project patterns or guidelines (`gstack_learnings.jsonl`) so AI agents improve over time.

#### `DecisionMemoryStore.get_active_decisions(limit=20) -> List[Dict[str, Any]]`
- **Description**: Retrieves the latest active decisions stored in the append-only event log.

#### `DecisionMemoryStore.get_learnings(limit=20) -> List[Dict[str, Any]]`
- **Description**: Retrieves recorded project patterns and guidelines.

---

## 🧰 4. Extended gstack Engine (`orchestrator/gstack_extended.py`)

Ported from `gstack` specialized tools (`/freeze`, `/spec`, `/document-generate`, `/plan-devex-review`, `/canary`).

### Functions:

#### `GStackExtendedEngine.freeze_path(filepath: str) -> Dict[str, Any]`
- **Description**: Adds a file or directory path to the frozen paths registry (`frozen_files.json`), protecting it against accidental overwrite or deletion.

#### `GStackExtendedEngine.unfreeze_path(filepath: str) -> Dict[str, Any]`
- **Description**: Removes a file or directory path from the frozen paths registry.

#### `GStackExtendedEngine.create_spec(feature_name, problem_statement, technical_scope) -> str`
- **Description**: Generates an executable technical specification document (`/spec`) structured with Executive Summary, Scope Boundaries, Architecture, and Acceptance Criteria. Automatically logs a decision event.

#### `GStackExtendedEngine.generate_diataxis_docs(component_name, doc_type) -> Dict[str, str]`
- **Description**: Authors technical documentation adhering strictly to the **Diataxis framework** (`Tutorial`, `How-To Guide`, `Reference Manual`, `Explanation`).

#### `GStackExtendedEngine.run_devex_audit(onboarding_flow_description) -> str`
- **Description**: Audits Developer Experience (DX) and benchmarks Time-To-Hello-World (TTHW) friction points.

#### `GStackExtendedEngine.run_canary_benchmark(url_or_endpoint) -> str`
- **Description**: Measures Core Web Vitals, API latency, and health regression indicators.

---

## 🛠️ 5. LangGraph Tools Reference (`orchestrator/tools.py`)

Custom `@tool` functions bound to worker nodes:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `redact_sensitive_content_tool` | `text: str` | Redacts API keys, credentials, and PII using `RedactEngine`. |
| `cso_security_scanner_tool` | `code_or_filepath: str` | Performs OWASP Top 10 + STRIDE threat analysis. |
| `investigate_root_cause_tool` | `symptom_description: str` | Hypothesis-driven root cause debugging (Iron Law). |
| `record_decision_tool` | `decision, rationale, scope` | Logs technical decision into `gstack_decisions.jsonl`. |
| `query_gstack_memory_tool` | `query: str` | Queries active decisions and compounding project learnings. |
| `generate_ascii_architecture_tool` | `component_name, state_flow` | Generates ASCII architecture state machine diagrams. |
| `freeze_file_path_tool` | `filepath: str` | Freezes file path from modification (`/freeze`). |
| `unfreeze_file_path_tool` | `filepath: str` | Unfreezes protected file path (`/unfreeze`). |
| `create_technical_spec_tool` | `feature_name, problem, scope` | Creates executable spec document (`/spec`). |
| `generate_diataxis_docs_tool` | `component_name, doc_type` | Authors Diataxis framework documentation. |
| `devex_audit_tool` | `onboarding_flow_description` | Audits DX and TTHW onboarding friction. |
| `canary_benchmark_tool` | `url_or_endpoint: str` | Measures Core Web Vitals and latency. |
| `autoplan_pipeline_tool` | `feature_idea: str` | Runs automated CEO → Design → Eng Review chain (`/autoplan`). |

---

## 👥 6. 14 Specialized Worker Roles (`orchestrator/states.py` & `agents.py`)

1. **`office_hours`**: YC Office Hours product interrogation & 6 forcing questions (`/office-hours`).
2. **`ceo_review`**: CEO Strategic Review & scope challenge (`/plan-ceo-review`).
3. **`eng_review`**: Architecture lock, state machines, and ASCII data flow (`/plan-eng-review`).
4. **`design_review`**: Senior Designer UI scoring (0-10) and AI Slop detection (`/plan-design-review`).
5. **`autoplan`**: Automated review pipeline chaining (`/autoplan`).
6. **`spec_author`**: Executable spec authoring (`/spec`).
7. **`devex_lead`**: Developer Experience & TTHW friction audit (`/plan-devex-review`).
8. **`cso_audit`**: Chief Security Officer OWASP Top 10 + STRIDE audit (`/cso`).
9. **`investigate`**: Iron Law root-cause debugging methodology (`/investigate`).
10. **`diataxis_writer`**: Diataxis documentation authoring (`/document-generate`).
11. **`canary_sre`**: Canary post-deploy monitoring & Core Web Vitals benchmark (`/canary`).
12. **`qa_lead`**: QA Lead test execution & bug reporting (`/qa`).
13. **`ship_release`**: Release Engineer pre-flight checks & PR generation (`/ship`).
14. **`retro`**: Weekly shipping velocity & test health retrospective (`/retro`).

---

## 🌐 7. REST API Endpoints (`orchestrator/api.py`)

- `POST /api/redact`: Pass `{"text": "..."}` to receive sanitized text and detected findings.
- `GET /api/decisions`: Returns active logged decisions from `gstack_decisions.jsonl`.
- `GET /api/memory`: Returns active decisions and compounding project learnings.
- `GET /run_stream`: SSE streaming endpoint for multi-agent graph execution.

---

## 💻 8. Multi-Model Hybrid Configuration (`worker_config.json`)

100% offline local model assignment table:

```json
{
    "coding": "Ollama (qwen2.5-coder:7b)",
    "file_writer": "Ollama (qwen2.5-coder:7b)",
    "eng_review": "Ollama (qwen2.5-coder:7b)",
    "spec_author": "Ollama (qwen2.5-coder:7b)",
    "ship_release": "Ollama (qwen2.5-coder:7b)",
    "security_audit": "Ollama (devstral:latest)",
    "cso_audit": "Ollama (devstral:latest)",
    "qa_lead": "Ollama (devstral:latest)",
    "canary_sre": "Ollama (devstral:latest)",
    "research": "Ollama (llama3.1:latest)",
    "analysis": "Ollama (llama3.1:latest)",
    "investigate": "Ollama (llama3.1:latest)",
    "devex_lead": "Ollama (llama3.1:latest)",
    "orchestrator": "Ollama (llama3.1:latest)",
    "synthesizer": "Ollama (llama3.1:latest)",
    "review": "Ollama (qwen2.5:latest)",
    "critic": "Ollama (qwen2.5:latest)",
    "office_hours": "Ollama (qwen2.5:latest)",
    "design_review": "Ollama (qwen2.5:latest)",
    "retro": "Ollama (qwen2.5:latest)"
}
```
