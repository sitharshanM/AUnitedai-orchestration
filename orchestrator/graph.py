import builtins
_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _print(*args, **kwargs)

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from .states import State
from .agents import orchestrator, human_approval, worker_app, synthesizer

def route_tasks(state: State):
    """Route ready tasks to workers or go to synthesizer."""
    if state.get("status") == "planning":
        return "orchestrator"

    if not state.get("plan") or not state["plan"].tasks:
        return "synthesizer"

    completed_ids = {t.task_id for t in state.get("completed_tasks", [])}
    ready_tasks = []
    all_done = True

    for task in state["plan"].tasks:
        if task.task_id not in completed_ids:
            all_done = False
            if all(dep in completed_ids for dep in task.dependencies):
                ready_tasks.append(task)

    if all_done or not ready_tasks:
        return "synthesizer"

    return [
        Send("worker", {
            "task": task,
            "topic": state["topic"],
            "previous_results": state.get("results", []),
            "uploaded_context": state.get("uploaded_context", "")
        }) for task in ready_tasks
    ]

# Define the StateGraph
workflow = StateGraph(State)

# Add our nodes
workflow.add_node("orchestrator", orchestrator)
workflow.add_node("human_approval", human_approval)
workflow.add_node("worker", worker_app)
workflow.add_node("synthesizer", synthesizer)

# Set the entry point
workflow.set_entry_point("orchestrator")

# Route from orchestrator to human_approval
workflow.add_edge("orchestrator", "human_approval")

# Route conditionally from human_approval to orchestrator (if edit/n) or workers/synthesizer (if approved)
workflow.add_conditional_edges(
    "human_approval",
    route_tasks,
    ["orchestrator", "worker", "synthesizer"]
)

# Route conditionally from worker back to route_tasks
workflow.add_conditional_edges(
    "worker",
    route_tasks,
    ["orchestrator", "worker", "synthesizer"]
)

# Connect synthesizer to the end
workflow.add_edge("synthesizer", END)

# Compile the graph
app = workflow.compile()

