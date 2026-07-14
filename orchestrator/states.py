from typing import Annotated, List, Literal, Optional, TypedDict
from pydantic import BaseModel, Field
from operator import add
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class WorkerTask(BaseModel):
    """Represents a single sub-task for a worker agent."""
    task_id: str = Field(description="Unique identifier for the task, e.g., 'task_1'")
    description: str = Field(description="Detailed instructions for the worker")
    worker_type: Optional[Literal["research", "writing", "analysis", "coding", "review", "file_writer"]] = Field(
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

class State(TypedDict):
    topic: str
    messages: Annotated[List[AnyMessage], add_messages]
    plan: Optional[OrchestratorPlan] = None
    completed_tasks: Annotated[List[WorkerTask], add] = []
    results: Annotated[List[dict], add] = []
    final_report: Optional[str] = None
    iteration: int = 0
    status: str = "planning"
    feedback: Optional[str] = None

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
