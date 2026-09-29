"""Core AUnitedAI domain models.

These models are deliberately independent of LangGraph so orchestration state can
be persisted, queried, and reconstructed without serializing a graph runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ObjectiveStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"


class AgentStatus(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    BLOCKED = "blocked"
    REVIEWING = "reviewing"
    FAILED = "failed"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ExecutionMode(str, Enum):
    OBSERVE = "observe"
    SUGGEST = "suggest"
    SUPERVISED = "supervised"
    AUTONOMOUS_SANDBOX = "autonomous_sandbox"


class EventType(str, Enum):
    OBJECTIVE_CREATED = "objective_created"
    PLAN_CREATED = "plan_created"
    AGENT_SPAWNED = "agent_spawned"
    TASK_STARTED = "task_started"
    MESSAGE_SENT = "message_sent"
    TOOL_REQUESTED = "tool_requested"
    TOOL_EXECUTED = "tool_executed"
    DECISION_CREATED = "decision_created"
    TASK_FAILED = "task_failed"
    REPLAN_TRIGGERED = "replan_triggered"
    TASK_COMPLETED = "task_completed"
    AGENT_TERMINATED = "agent_terminated"
    OBJECTIVE_COMPLETED = "objective_completed"


class BlackboardEntryType(str, Enum):
    FACT = "fact"
    HYPOTHESIS = "hypothesis"
    QUESTION = "question"
    EVIDENCE = "evidence"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    RISK = "risk"
    FAILURE = "failure"
    ARTIFACT = "artifact"
    TASK_RESULT = "task_result"
    REQUEST = "request"


class ObjectiveCreate(BaseModel):
    objective: str = Field(min_length=1, max_length=10_000)
    project_id: str = Field(default="default", min_length=1, max_length=200)
    mode: ExecutionMode = ExecutionMode.SUPERVISED
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    budget_usd: float | None = Field(default=None, ge=0.0)


class Objective(ObjectiveCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: ObjectiveStatus = ObjectiveStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)
    verification_requirements: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.BACKLOG
    owner_agent_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def cannot_depend_on_self(self) -> "Task":
        if self.id in self.dependencies:
            raise ValueError("a task cannot depend on itself")
        return self


class TaskGraph(BaseModel):
    tasks: list[Task]

    @model_validator(mode="after")
    def validate_dag(self) -> "TaskGraph":
        task_ids = {task.id for task in self.tasks}
        if len(task_ids) != len(self.tasks):
            raise ValueError("task ids must be unique")
        for task in self.tasks:
            missing = set(task.dependencies) - task_ids
            if missing:
                raise ValueError(f"task {task.id} has missing dependencies: {sorted(missing)}")
        visiting: set[str] = set()
        visited: set[str] = set()
        edges = {task.id: task.dependencies for task in self.tasks}

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("task dependencies contain a cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in edges[task_id]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in task_ids:
            visit(task_id)
        return self

    def ready_tasks(self) -> list[Task]:
        completed = {task.id for task in self.tasks if task.status == TaskStatus.DONE}
        return [
            task for task in self.tasks
            if task.status in {TaskStatus.BACKLOG, TaskStatus.READY}
            and set(task.dependencies).issubset(completed)
        ]


class AgentDNA(BaseModel):
    role: str
    mission: str
    capabilities: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    authority: dict[str, Any] = Field(default_factory=dict)
    model_requirements: dict[str, Any] = Field(default_factory=dict)
    context_access: list[str] = Field(default_factory=list)
    memory_access: list[str] = Field(default_factory=list)
    risk_level: str = "safe"
    communication_permissions: list[str] = Field(default_factory=list)
    verification_responsibilities: list[str] = Field(default_factory=list)
    termination_conditions: list[str] = Field(default_factory=list)


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    name: str
    dna: AgentDNA
    model: str = "auto"
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType
    project_id: str
    objective_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class BlackboardEntryCreate(BaseModel):
    type: BlackboardEntryType
    project_id: str
    # Final deliverables can legitimately contain full reports, campaigns, or
    # source bundles. Verification summaries remain compact at their producer.
    content: str = Field(min_length=1, max_length=500_000)
    objective_id: str | None = None
    task_id: str | None = None
    author_agent_id: str | None = None
    domains: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BlackboardEntry(BlackboardEntryCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=utc_now)


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    task_id: str | None = None
    path: str
    name: str
    kind: str = "file"
    size_bytes: int = Field(default=0, ge=0)
    sha256: str | None = None
    verified: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class IntentSpecification(BaseModel):
    objective: str
    domains: list[str] = Field(default_factory=list)
    complexity: str = "medium"
    estimated_scope: str = "single-stage"
    requires_research: bool = False
    requires_code: bool = False
    requires_testing: bool = False
    requires_external_actions: bool = False
    ambiguities: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    milestones: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)


class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    name: str
    parent_team_id: str | None = None
    agent_ids: list[str] = Field(default_factory=list)


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    PROPOSAL = "proposal"
    CHALLENGE = "challenge"
    EVIDENCE = "evidence"
    REVIEW = "review"
    BLOCKER = "blocker"
    ESCALATION = "escalation"
    HANDOFF = "handoff"


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    type: MessageType
    sender_agent_id: str
    recipient_agent_id: str | None = None
    task_id: str | None = None
    content: str = Field(min_length=1, max_length=20_000)
    reply_to: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Permission(str, Enum):
    READ_FILE = "read_file"
    WRITE_PROJECT_FILE = "write_project_file"
    RUN_SANDBOX_COMMAND = "run_sandbox_command"
    NETWORK_REQUEST = "network_request"
    INSTALL_DEPENDENCY = "install_dependency"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    DELETE_FILE = "delete_file"
    SEND_MESSAGE = "send_message"
    DEPLOY = "deploy"
    PURCHASE = "purchase"
    ACCOUNT_CHANGE = "account_change"


class RiskClass(str, Enum):
    SAFE = "safe"
    REVIEW = "review"
    SENSITIVE = "sensitive"
    PROHIBITED = "prohibited"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EDITED = "edited"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    agent_id: str | None = None
    permission: Permission
    action: str
    risk: RiskClass = RiskClass.REVIEW
    status: ApprovalStatus = ApprovalStatus.PENDING
    rationale: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class UsageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    provider: str
    model: str
    agent_id: str | None = None
    task_id: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class AttemptStatus(str, Enum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    EXHAUSTED = "exhausted"


class ExecutionAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    objective_id: str
    task_id: str
    agent_id: str | None = None
    number: int = Field(default=1, ge=1)
    status: AttemptStatus = AttemptStatus.STARTED
    error_class: str | None = None
    error_message: str | None = None
    recovery_strategy: str | None = None
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ObjectiveControl(BaseModel):
    action: str
    reason: str = ""


class ApprovalResolution(BaseModel):
    status: ApprovalStatus
    edited_action: str | None = None


class CommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2_000)
