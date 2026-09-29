# AUnitedAI 2.0 Architecture Map

## Existing system

| Concern | Existing implementation | Reuse decision |
|---|---|---|
| API | FastAPI in `orchestrator/api.py` | Extend without removing legacy routes. |
| Orchestration | LangGraph in `orchestrator/graph.py` | Keep as execution adapter; move durable state into domain services. |
| Planning and workers | Planner, workers, critic, synthesizer in `orchestrator/agents.py` | Reuse prompts and execution while gradually introducing dynamic Agent DNA. |
| Task concurrency | Dependency-aware `Send` fan-out in `orchestrator/graph.py` | Preserve and strengthen with validated DAG models. |
| Providers | Ollama, Gemini, Groq, OpenAI, Anthropic and compatible endpoints | Extract into a router in Phase 2; do not duplicate adapters. |
| Tools | LangChain tools in `orchestrator/tools.py` | Wrap with permissions and schemas in Phase 4. |
| Memory | JSONL decision/learning store | Preserve; migrate validated knowledge into project memory incrementally. |
| Events | Final-result SSE plus JSONL decisions | Extend with a persisted event stream; later stream events as they occur. |
| Approval | Plan approval node | Preserve; generalize into server-enforced approval gates. |
| Security | Redaction engine and password gate | Reuse; close permissive CORS/auth gaps before external deployment. |
| UI | React/Vite single execution screen | Evolve into workstation panels after stable APIs exist. |

## Target boundaries

```text
FastAPI / SSE
      |
Application services (objective, planning, lifecycle, approvals)
      |
Domain (Objective, Task DAG, Agent DNA, Blackboard, Event)
      |
Orchestration adapters (LangGraph, model router, tools, sandbox)
      |
Persistence (SQLite now; repository interfaces permit later expansion)
```

The domain layer must not depend on LangGraph or a model provider. Every material
state transition emits an append-only event. The Blackboard carries structured,
filtered knowledge; conversational transcripts remain supporting data rather than
the shared source of truth.

## Phase 1 decisions

1. Additive migration: current `/run` and `/run_stream` behavior remains available.
2. SQLite is the local-first baseline because it is transactional, restart-safe,
   requires no service, and ships with Python.
3. Events are append-only and contain redacted payloads.
4. Task graphs reject missing dependencies, duplicate IDs, self-dependencies, and cycles.
5. Blackboard retrieval is scoped and filterable; agents should request only relevant entries.

## Technical debt affecting the roadmap

- Provider construction is repeated in `agents.py`; Phase 2 should centralize it.
- Current graph checkpoints are not persistent, so an in-flight run cannot resume after restart.
- SSE reports start/finish/heartbeat, not granular lifecycle events.
- Tool functions do not yet share a permission-enforced execution boundary.
- Configuration and memory paths depend on the process working directory.
- Run-route authentication remains disabled for development; CORS is now restricted
  to local UI origins unless `AUNITEDAI_CORS_ORIGINS` explicitly adds others.
- The frontend is a monolithic component and should be split by workstation capability.
- Automated coverage was effectively absent before the Phase 1 foundation tests.

## Next implementation slices

1. Connect graph transitions to the event store and add durable LangGraph checkpoints.
2. Persist plans/tasks/agents and implement lifecycle transition services.
3. Add Intent Engine, dynamic Agent Forge, organization generator, and model router.
4. Add communication/critic/judge/observer services with explicit convergence budgets.
5. Place tools behind permissions, approvals, sandboxing, and attempt tracking.
6. Build workstation UI from the stable objective/event/Blackboard APIs.

## Implemented vertical slice

The current migration now provides a working local-first control-plane slice:

- objective interpretation with inferred domains, scope, research/code/test needs;
- validated task DAGs with dependencies, readiness, milestones, risks, artifacts,
  and verification requirements;
- dynamically generated teams and Agent DNA rather than a fixed execution roster;
- capability/privacy/budget-aware model selection metadata;
- durable objectives, plans, tasks, agents, teams, messages, approvals, usage,
  execution attempts, Blackboard entries, and append-only events;
- pause, resume, cancel, replan, agent pause/terminate, task transitions, and
  context-aware workstation commands;
- communication budgets and duplicate-loop detection;
- server-side permission classification and approval records;
- hard objective budgets, retry limits, failure classification, and recovery strategy;
- Observer findings, evidence-bearing completion, replayable event SSE, and a
  queryable objective/task/agent knowledge graph;
- a dark live workstation UI with project navigation, organization graph, agent
  inspector, task board, Blackboard, messages, artifacts, activity, timeline,
  command bar, human controls, and developer state view;
- a compatibility execution bridge that runs the existing LangGraph and records
  task, agent, Blackboard, and objective lifecycle changes around it.

Provider-backed execution still depends on the locally configured provider and
model availability. External actions remain intentionally unavailable until a
specific tool adapter passes the permission and approval boundary.
