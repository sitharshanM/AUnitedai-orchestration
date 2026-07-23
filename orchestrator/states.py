from typing import Annotated, Any, List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field
from operator import add
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

def reduce_keep(left: Any, right: Any) -> Any:
    return right if right is not None else left

class WorkerTask(BaseModel):
    """Represents a single sub-task for a worker agent."""
    task_id: str = Field(description="Unique identifier for the task, e.g., 'task_1'")
    description: str = Field(description="Detailed instructions for the worker")
    worker_type: Optional[Literal[
        "research", "writing", "analysis", "coding", "review", "file_writer", "security_audit",
        "office_hours", "ceo_review", "eng_review", "design_review", "cso_audit", "investigate", "qa_lead", "ship_release", "retro",
        "spec_author", "devex_lead", "diataxis_writer", "canary_sre", "autoplan",
        "silent_failure_hunter", "build_error_resolver", "performance_optimizer", "harness_optimizer",
        "a11y_architect", "e2e_runner", "seo_specialist", "doc_updater"
    ]] = Field(
        default=None,
        description="Type of worker this task is assigned to"
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="What the worker should return"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of task_ids that must be completed before this task can start"
    )
    assigned_tools: Optional[List[str]] = Field(
        default_factory=list,
        description="List of specific tool names assigned dynamically by the Orchestrator AI for this task"
    )

class OrchestratorPlan(BaseModel):
    """Structured output from the Orchestrator/Planner agent."""
    tasks: List[WorkerTask] = Field(
        ...,
        description="List of sub-tasks to be executed by worker agents."
    )
    overall_strategy: Optional[str] = Field(
        default=None,
        description="High-level explanation of the approach and reasoning behind the task breakdown."
    )
    final_goal: str = Field(
        ...,
        description="What successful completion of the entire task looks like."
    )

def reduce_keep(left: Any, right: Any) -> Any:
    return right if right is not None else left

class State(TypedDict):
    topic: Annotated[str, reduce_keep]
    messages: Annotated[List[AnyMessage], add_messages]
    plan: Annotated[Optional[OrchestratorPlan], reduce_keep]
    completed_tasks: Annotated[List[WorkerTask], add]
    results: Annotated[List[dict], add]
    final_report: Annotated[Optional[str], reduce_keep]
    iteration: Annotated[int, reduce_keep]
    status: Annotated[str, reduce_keep]
    feedback: Annotated[Optional[str], reduce_keep]
    uploaded_context: Annotated[Optional[str], reduce_keep]
    decisions: Annotated[Optional[List[dict]], reduce_keep]

class WorkerState(TypedDict):
    task: WorkerTask
    topic: str
    previous_results: List[dict]
    output: Optional[str]
    critic_feedback: Optional[str]
    retries: int
    critic_status: Optional[str]
    completed_tasks: List[WorkerTask]
    results: List[dict]
    uploaded_context: Optional[str]
