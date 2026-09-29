"""Autonomous control-plane services for AUnitedAI 2.0.

The control plane is deterministic and provider-independent. Model-backed planners
can replace individual strategies later without changing persistence or APIs.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .domain import (
    Agent, AgentDNA, AgentMessage, AgentStatus, ApprovalRequest, Artifact, BlackboardEntry,
    BlackboardEntryType, Event, EventType, ExecutionMode, IntentSpecification,
    ExecutionAttempt, AttemptStatus, MessageType, Objective, ObjectiveStatus,
    Permission, Plan, RiskClass, Task, TaskStatus, Team, UsageRecord, utc_now,
)
from .foundation_store import FoundationStore, default_foundation_store
from .config import load_config


DOMAIN_KEYWORDS = {
    "python": ("python", "fastapi", "django", "flask"),
    "frontend": ("react", "frontend", "web ui", "dashboard", "website"),
    "c++": ("c++", "cpp"),
    "windows": ("windows", "win32", "desktop"),
    "security": ("security", "audit", "vulnerability", "auth"),
    "data": ("data", "analytics", "machine learning", "database"),
    "research": ("research", "compare", "investigate", "evidence"),
    "documentation": ("documentation", "docs", "guide"),
}


class IntentEngine:
    def understand(self, objective: Objective) -> IntentSpecification:
        text = objective.objective.lower()
        domains = [name for name, words in DOMAIN_KEYWORDS.items() if any(word in text for word in words)]
        requires_code = any(word in text for word in ("build", "implement", "code", "app", "fix", "refactor"))
        requires_research = "research" in domains or any(word in text for word in ("compare", "latest", "choose"))
        requires_testing = requires_code or any(word in text for word in ("test", "verify", "reliable"))
        external = any(word in text for word in ("deploy", "publish", "send", "purchase"))
        score = len(domains) + sum((requires_code, requires_research, requires_testing, external))
        complexity = "high" if score >= 5 else "medium" if score >= 2 else "low"
        criteria = list(objective.success_criteria)
        if requires_code and not criteria:
            criteria = ["Requested artifact exists", "Relevant verification passes", "Result is documented"]
        return IntentSpecification(
            objective=objective.objective,
            domains=domains or ["general"],
            complexity=complexity,
            estimated_scope="multi-stage" if complexity == "high" else "single-stage",
            requires_research=requires_research,
            requires_code=requires_code,
            requires_testing=requires_testing,
            requires_external_actions=external,
            constraints=objective.constraints,
            success_criteria=criteria,
        )


class AutonomousPlanner:
    def create_plan(self, objective: Objective, intent: IntentSpecification) -> Plan:
        tasks: list[Task] = []

        def add(key: str, title: str, description: str, capabilities: list[str],
                dependencies: list[str] | None = None, artifacts: list[str] | None = None,
                verification: list[str] | None = None) -> str:
            task_id = f"{key}-{objective.id[:8]}"
            tasks.append(Task(
                id=task_id, objective_id=objective.id, title=title, description=description,
                dependencies=dependencies or [], required_capabilities=capabilities,
                expected_artifacts=artifacts or [], verification_requirements=verification or [],
                status=TaskStatus.READY if not dependencies else TaskStatus.BACKLOG,
            ))
            return task_id

        discovery = add("understand", "Clarify objective", "Convert the objective into explicit requirements and constraints.", ["analysis"])
        research = None
        if intent.requires_research:
            research = add("research", "Research solution space", "Gather and validate relevant evidence.", ["research", "evidence-validation"], [discovery])
        architecture = add("architecture", "Design solution", "Select an architecture and record key decisions.", ["architecture"], [research or discovery], ["architecture decision"])
        implementation = None
        if intent.requires_code:
            implementation = add("implementation", "Implement deliverables", "Produce the requested implementation safely.", [*intent.domains, "engineering"], [architecture], ["source artifacts"])
        verify_dependency = implementation or architecture
        verification = add("verification", "Verify results", "Test claims and artifacts using empirical evidence.", ["qa", "criticism"], [verify_dependency], ["verification report"], intent.success_criteria)
        add("synthesis", "Synthesize outcome", "Present results, evidence, limitations, and next actions.", ["synthesis", "documentation"], [verification], ["final report"])
        return Plan(
            objective_id=objective.id,
            milestones=["Understand", "Plan", "Execute", "Verify", "Synthesize"],
            tasks=tasks,
            risks=["Insufficient evidence", "Tool or provider failure", "Scope ambiguity"],
        )


class OrganizationGenerator:
    ROLE_MAP = {
        "analysis": ("Objective Analyst", "analyst"),
        "research": ("Evidence Researcher", "researcher"),
        "architecture": ("Solution Architect", "architect"),
        "engineering": ("Implementation Engineer", "engineer"),
        "qa": ("Verification Engineer", "reviewer"),
        "synthesis": ("Delivery Coordinator", "coordinator"),
    }

    def form(self, objective: Objective, plan: Plan) -> tuple[list[Team], list[Agent], list[Task]]:
        agents: list[Agent] = []
        capability_owner: dict[str, Agent] = {}
        updated_tasks: list[Task] = []
        for task in plan.tasks:
            primary = next((cap for cap in task.required_capabilities if cap in self.ROLE_MAP), task.required_capabilities[0])
            group = "engineering" if primary not in self.ROLE_MAP and "engineering" in task.required_capabilities else primary
            if group not in capability_owner:
                name, role = self.ROLE_MAP.get(group, (f"{primary.title()} Specialist", "specialist"))
                dna = AgentDNA(
                    role=role, mission=f"Own {group} outcomes for: {objective.objective}",
                    capabilities=list(dict.fromkeys(task.required_capabilities)),
                    allowed_tools=["read_file_tool", "query_knowledge_base", "verification_loop_tool"],
                    authority={"delegate": False, "external_actions": False},
                    context_access=["objective", "assigned_tasks", "relevant_blackboard"],
                    memory_access=["working", "project"], risk_level="safe",
                    communication_permissions=[kind.value for kind in MessageType],
                    verification_responsibilities=task.verification_requirements,
                    termination_conditions=["assigned tasks complete", "objective cancelled"],
                )
                capability_owner[group] = Agent(
                    objective_id=objective.id, name=name, dna=dna, status=AgentStatus.IDLE,
                )
                agents.append(capability_owner[group])
            owner = capability_owner[group]
            updated_tasks.append(task.model_copy(update={"owner_agent_id": owner.id}))
        team = Team(objective_id=objective.id, name="Objective Team", agent_ids=[agent.id for agent in agents])
        return [team], agents, updated_tasks


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    capabilities: frozenset[str]
    local: bool
    relative_cost: float
    speed: float


class ModelRouter:
    WORKER_BY_CAPABILITY = {
        "analysis": "analysis",
        "research": "research",
        "architecture": "code_architect",
        "engineering": "coding",
        "qa": "qa_lead",
        "criticism": "critic",
        "synthesis": "synthesizer",
        "documentation": "doc_updater",
        "security": "security_audit",
    }
    CANDIDATES = (
        ModelCandidate("ollama", "qwen2.5-coder:7b", frozenset({"coding", "local", "structured_output"}), True, 0, .6),
        ModelCandidate("ollama", "llama3.1:latest", frozenset({"reasoning", "local", "long_context"}), True, 0, .5),
        ModelCandidate("openai", "configured", frozenset({"reasoning", "coding", "tool_calling", "structured_output"}), False, .7, .8),
        ModelCandidate("anthropic", "configured", frozenset({"reasoning", "coding", "long_context", "tool_calling"}), False, .8, .7),
        ModelCandidate("gemini", "configured", frozenset({"reasoning", "vision", "long_context", "structured_output"}), False, .5, .9),
    )

    def route(self, capabilities: list[str], privacy_local: bool = False, budget_remaining: float | None = None) -> ModelCandidate:
        config = load_config()
        worker_name = next((self.WORKER_BY_CAPABILITY[cap] for cap in capabilities if cap in self.WORKER_BY_CAPABILITY), "orchestrator")
        configured = config.get(worker_name) or config.get("orchestrator")
        if configured and (not privacy_local or str(configured.get("backend", "")).lower() == "ollama"):
            backend = str(configured.get("backend", "Custom API"))
            model = str(configured.get("model", "openrouter/free"))
            return ModelCandidate(backend, model, frozenset(capabilities), backend.lower() == "ollama", 0, .8)
        required = {"coding" if cap in {"engineering", "python", "c++", "frontend"} else cap for cap in capabilities}
        candidates = [item for item in self.CANDIDATES if not privacy_local or item.local]
        if budget_remaining is not None and budget_remaining <= .25:
            candidates = [item for item in candidates if item.local] or candidates
        return max(candidates, key=lambda item: len(required & item.capabilities) * 3 + item.speed - item.relative_cost)


class PermissionEngine:
    RISK = {
        Permission.READ_FILE: RiskClass.SAFE, Permission.WRITE_PROJECT_FILE: RiskClass.SAFE,
        Permission.RUN_SANDBOX_COMMAND: RiskClass.REVIEW, Permission.NETWORK_REQUEST: RiskClass.REVIEW,
        Permission.INSTALL_DEPENDENCY: RiskClass.SENSITIVE, Permission.GIT_COMMIT: RiskClass.REVIEW,
        Permission.GIT_PUSH: RiskClass.SENSITIVE, Permission.DELETE_FILE: RiskClass.SENSITIVE,
        Permission.SEND_MESSAGE: RiskClass.SENSITIVE, Permission.DEPLOY: RiskClass.SENSITIVE,
        Permission.PURCHASE: RiskClass.PROHIBITED, Permission.ACCOUNT_CHANGE: RiskClass.PROHIBITED,
    }

    def evaluate(self, permission: Permission, mode: ExecutionMode) -> tuple[RiskClass, bool]:
        risk = self.RISK[permission]
        allowed = risk == RiskClass.SAFE and mode in {ExecutionMode.SUPERVISED, ExecutionMode.AUTONOMOUS_SANDBOX}
        return risk, allowed


class AntiChaosGuard:
    def __init__(self, conversation_limit: int = 30, duplicate_limit: int = 2):
        self.conversation_limit = conversation_limit
        self.duplicate_limit = duplicate_limit

    def check_message(self, candidate: AgentMessage, existing: list[AgentMessage]) -> str | None:
        if len(existing) >= self.conversation_limit:
            return "conversation budget exhausted"
        normalized = re.sub(r"\s+", " ", candidate.content.strip().lower())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        duplicates = sum(hashlib.sha256(re.sub(r"\s+", " ", item.content.strip().lower()).encode()).hexdigest() == digest for item in existing)
        return "duplicate message loop detected" if duplicates >= self.duplicate_limit else None


class Observer:
    def inspect(self, tasks: list[Task], messages: list[AgentMessage]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if tasks and not any(task.status in {TaskStatus.READY, TaskStatus.RUNNING} for task in tasks) and any(task.status != TaskStatus.DONE for task in tasks):
            findings.append({"severity": "high", "kind": "stalled", "recommendation": "Re-evaluate blocked dependencies."})
        signatures = Counter(re.sub(r"\s+", " ", item.content.lower().strip()) for item in messages)
        if any(count > 2 for count in signatures.values()):
            findings.append({"severity": "medium", "kind": "message_loop", "recommendation": "Stop discussion and escalate to a judge."})
        failed = sum(task.status == TaskStatus.FAILED for task in tasks)
        if failed:
            findings.append({"severity": "high", "kind": "task_failure", "recommendation": f"Recover or replan {failed} failed task(s)."})
        return findings


class BudgetExceededError(RuntimeError):
    pass


class BudgetEngine:
    def total(self, usage: list[UsageRecord]) -> float:
        return sum(item.estimated_cost for item in usage)

    def accept(self, objective: Objective, existing: list[UsageRecord], record: UsageRecord) -> None:
        if objective.budget_usd is not None and self.total(existing) + record.estimated_cost > objective.budget_usd:
            raise BudgetExceededError("hard objective budget would be exceeded")


class RecoveryEngine:
    def decide(self, attempt: ExecutionAttempt, max_attempts: int = 3) -> ExecutionAttempt:
        if attempt.status != AttemptStatus.FAILED:
            return attempt
        if attempt.number >= max_attempts:
            return attempt.model_copy(update={"status": AttemptStatus.EXHAUSTED, "recovery_strategy": "escalate_to_human", "updated_at": utc_now()})
        error = (attempt.error_message or "").lower()
        strategy = "reduce_scope_and_retry" if "timeout" in error else "diagnose_patch_and_retry"
        return attempt.model_copy(update={"status": AttemptStatus.RETRYING, "recovery_strategy": strategy, "updated_at": utc_now()})


class WorkstationService:
    def __init__(self, store: FoundationStore = default_foundation_store):
        self.store = store
        self.intent_engine = IntentEngine()
        self.planner = AutonomousPlanner()
        self.organization = OrganizationGenerator()
        self.router = ModelRouter()
        self.permissions = PermissionEngine()
        self.guard = AntiChaosGuard()
        self.observer = Observer()
        self.budgets = BudgetEngine()
        self.recovery = RecoveryEngine()

    def bootstrap(self, objective: Objective) -> dict[str, Any]:
        intent = self.intent_engine.understand(objective)
        plan = self.planner.create_plan(objective, intent)
        teams, agents, tasks = self.organization.form(objective, plan)
        plan = plan.model_copy(update={"tasks": tasks})
        self.store.update_objective_status(objective.id, ObjectiveStatus.PLANNING)
        self.store.save_plan(plan)
        for team in teams:
            self.store.save_entity("team", team)
        for agent in agents:
            routed = self.router.route(agent.dna.capabilities, privacy_local=False)
            stored = agent.model_copy(update={"model": f"{routed.provider}/{routed.model}"})
            self.store.save_entity("agent", stored)
            self.store.append_event(Event(type=EventType.AGENT_SPAWNED, project_id=objective.project_id,
                                          objective_id=objective.id, agent_id=stored.id,
                                          payload={"name": stored.name, "role": stored.dna.role, "model": stored.model}))
        self.store.append_event(Event(type=EventType.PLAN_CREATED, project_id=objective.project_id,
                                      objective_id=objective.id,
                                      payload={"plan_id": plan.id, "task_count": len(tasks), "version": plan.version}))
        for risk in plan.risks:
            self.store.add_blackboard_entry(BlackboardEntry(
                type=BlackboardEntryType.RISK, project_id=objective.project_id,
                objective_id=objective.id, content=risk, relevance=.8,
            ))
        updated = self.store.update_objective_status(objective.id, ObjectiveStatus.RUNNING)
        return {"objective": updated, "intent": intent, "plan": plan, "teams": teams,
                "agents": self.store.list_agents(objective.id)}

    def snapshot(self, objective_id: str) -> dict[str, Any] | None:
        objective = self.store.get_objective(objective_id)
        if not objective:
            return None
        tasks = self.store.list_tasks(objective_id)
        agents = self.store.list_agents(objective_id)
        messages = self.store.list_messages(objective_id)
        usage = self.store.list_usage(objective_id)
        total_cost = self.budgets.total(usage)
        done = sum(task.status == TaskStatus.DONE for task in tasks)
        progress = round(done / len(tasks) * 100) if tasks else 0
        return {
            "objective": objective, "plan": self.store.get_plan(objective_id), "tasks": tasks,
            "agents": agents, "teams": self.store.list_teams(objective_id), "messages": messages,
            "approvals": self.store.list_approvals(objective_id), "usage": usage,
            "attempts": self.store.list_attempts(objective_id),
            "artifacts": self.store.list_artifacts(objective_id),
            "blackboard": self.store.query_blackboard(objective.project_id, objective_id=objective_id),
            "events": self.store.list_events(objective.project_id, objective_id=objective_id),
            "observer": self.observer.inspect(tasks, messages),
            "metrics": {"progress": progress, "tasks_done": done, "tasks_total": len(tasks),
                        "agents": len(agents), "active_agents": sum(a.status == AgentStatus.WORKING for a in agents),
                        "cost": round(total_cost, 6)},
        }

    def record_usage(self, record: UsageRecord) -> UsageRecord:
        objective = self.store.get_objective(record.objective_id)
        if objective is None:
            raise ValueError("objective not found")
        self.budgets.accept(objective, self.store.list_usage(record.objective_id), record)
        return self.store.save_entity("usage", record)

    def record_attempt(self, attempt: ExecutionAttempt, max_attempts: int = 3) -> ExecutionAttempt:
        resolved = self.recovery.decide(attempt, max_attempts)
        self.store.save_entity("attempt", resolved)
        return resolved

    def knowledge_graph(self, objective_id: str) -> dict[str, list[dict]]:
        snapshot = self.snapshot(objective_id)
        if not snapshot:
            return {"nodes": [], "edges": []}
        nodes = [{"id": objective_id, "type": "objective", "label": snapshot["objective"].objective}]
        edges: list[dict] = []
        for task in snapshot["tasks"]:
            nodes.append({"id": task.id, "type": "task", "label": task.title, "status": task.status.value})
            edges.append({"source": objective_id, "target": task.id, "type": "contains"})
            for dependency in task.dependencies:
                edges.append({"source": dependency, "target": task.id, "type": "precedes"})
            if task.owner_agent_id:
                edges.append({"source": task.owner_agent_id, "target": task.id, "type": "owns"})
        for agent in snapshot["agents"]:
            nodes.append({"id": agent.id, "type": "agent", "label": agent.name, "status": agent.status.value})
            edges.append({"source": objective_id, "target": agent.id, "type": "formed"})
        return {"nodes": nodes, "edges": edges}


default_workstation_service = WorkstationService()
