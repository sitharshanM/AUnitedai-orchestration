from typing import Annotated, List, Literal, Optional, TypedDict

import builtins
_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _print(*args, **kwargs)

from operator import add

from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

import config
worker_config = config.load_config()

# Load GOOGLE_API_KEY (and any other secrets) from .env
from dotenv import load_dotenv
load_dotenv()

# ========================== TOOLS ==========================

@tool
def write_file_tool(file_path: str, content: str) -> str:
    """Writes the specified content to a file at the given file_path.
    Use this tool to save code, reports, or results to the filesystem.
    """
    import os
    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote file to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def read_file_tool(file_path: str) -> str:
    """Reads the contents of a file at the given file_path.
    Use this tool to view code, reports, or results from the filesystem.
    """
    import os
    try:
        if not os.path.exists(file_path):
            return f"Error: File does not exist at {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def fetch_webpage_tool(url: str) -> str:
    """Fetches the content of a web page at the given URL and returns it as plain text.
    Use this tool to read detailed article content after finding links in search results.
    """
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Return first 3000 characters to avoid context overflow
        if len(text) > 3000:
            return text[:3000] + "\n... [Content truncated to 3000 characters] ..."
        return text
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

@tool
def query_knowledge_base(query: str) -> str:
    """Queries the local knowledge base using semantic vector search.
    Use this tool to find information from local company documents, guides, policies, or project files.
    """
    import os
    from langchain_community.vectorstores import Chroma
    from langchain_ollama import OllamaEmbeddings
    
    CHROMA_DB_DIR = "./chroma_db"
    EMBEDDING_MODEL = "nomic-embed-text"
    
    if not os.path.exists(CHROMA_DB_DIR):
        return "Error: Local knowledge base vector database does not exist. Please index documents first."
        
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        results = db.similarity_search(query, k=3)
        
        if not results:
            return "No matching information found in the local knowledge base."
            
        combined_text = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page")
            source_info = f"{source} (Page {page})" if page else source
            combined_text.append(f"--- Document Chunk {i+1} (Source: {source_info}) ---\n{doc.page_content}")
            
        return "\n\n".join(combined_text)
    except Exception as e:
        return f"Error querying local knowledge base: {str(e)}"

# ========================== MODELS ==========================

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


# ========================== STATES ==========================

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


# ========================== NODES ==========================

def orchestrator(state: State) -> dict:
    """Orchestrator node - creates the plan."""
    planner_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert orchestrator/planner agent.
        Break down the user's high-level topic into specific, actionable sub-tasks with clear dependencies.
        Available worker types to assign:
        - "research": search the web or query the local knowledge base for information
        - "writing": write articles, reports, code comments, documentation
        - "analysis": evaluate code/ideas, analyze data, compare options (has access to local files and knowledge base)
        - "coding": implement algorithms, code scripts, write unit tests
        - "review": review code or writing for bugs, quality, and improvements
        - "file_writer": write content/code to local files on disk"""),
        ("user", "Topic: {topic}\n\nHuman feedback for previous plan adjustments (if any): {feedback}")
    ])

    llm = ChatOllama(
        model="llama3.1",
        temperature=0.0
    )

    planner = planner_prompt | llm.with_structured_output(OrchestratorPlan)
    plan = planner.invoke({
        "topic": state["topic"],
        "feedback": state.get("feedback") or "None"
    })

    return {
        "plan": plan,
        "status": "planning",
        "iteration": state.get("iteration", 0) + 1
    }


def human_approval(state: State) -> dict:
    """Human-in-the-Loop approval node to review the plan."""
    plan = state.get("plan")
    if not plan:
        return {"status": "planning"}

    print("\n=================== PROPOSED PLAN ===================")
    if plan.overall_strategy:
        print(f"Strategy: {plan.overall_strategy}")
    for task in plan.tasks:
        deps = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
        print(f" - [{task.task_id}] ({task.worker_type}): {task.description}{deps}")
    print("=====================================================")

    print("Auto-approving plan! Executing tasks...\n")
    return {"status": "routing", "feedback": None}


def worker(state: WorkerState) -> dict:
    """Dynamic worker node."""
    task = state["task"]
    topic = state["topic"]
    prev_results = state.get("previous_results", [])

    # Build context from previous results
    context = "\n\n".join([
        f"--- Output of {r.get('task_id')} ({r.get('worker_type')}) ---\n{r.get('output')}"
        for r in prev_results
    ])

    # Load dynamic configuration from config
    w_conf = worker_config.get(task.worker_type, config.DEFAULT_CONFIG.get(task.worker_type, config.DEFAULT_CONFIG["review"]))
    model = w_conf["model"]
    backend = w_conf["backend"]
    temperature = float(w_conf["temperature"])
    custom_prompt = w_conf.get("custom_prompt", "")

    tools = []
    if task.worker_type == "research":
        tools = [DuckDuckGoSearchResults(max_results=3), fetch_webpage_tool, query_knowledge_base]
    elif task.worker_type == "analysis":
        tools = [read_file_tool, query_knowledge_base]
    elif task.worker_type == "coding" or task.worker_type == "file_writer":
        tools = [read_file_tool, write_file_tool]
    elif task.worker_type == "review":
        tools = [read_file_tool]

    is_devstral = (model == "devstral:latest")

    # Instantiate the correct LLM backend
    if backend == "Gemini":
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature
        )
    elif backend == "Groq":
        llm = ChatGroq(
            model=model,
            temperature=temperature
        )
    else:
        llm = ChatOllama(
            model=model,
            temperature=temperature
        )

    if tools and not is_devstral:
        llm = llm.bind_tools(tools)

    system_instruction = f"You are a specialized {task.worker_type} agent.\nExecute the assigned task thoroughly and professionally.\nUse provided context from previous tasks when relevant."
    if custom_prompt.strip():
        system_instruction += f"\n\n[CUSTOM INSTRUCTIONS]\n{custom_prompt.strip()}"
    if is_devstral and tools:
        tool_descriptions = "\n".join([f"- `{t.name}`: {t.description}" for t in tools])
        system_instruction += "\n\nYou can call the following tools by outputting a JSON block:\n" + tool_descriptions + "\n\nTo call a tool, you MUST output a JSON block formatted exactly like this:\n```json\n{{\n  \"tool\": \"tool_name\",\n  \"args\": {{\n    \"arg_name\": \"arg_value\"\n  }}\n}}\n```\nDo not output anything else after the JSON block. Once the tool results are provided, they will be given as a user response, and you can output your final result."

    if task.worker_type == "file_writer":
        system_instruction += "\nIMPORTANT: You must write the file to the filesystem by calling the 'write_file_tool' tool. Do not just output the file contents as text; you must call the tool."

    worker_prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("user", """Main Topic: {topic}

Task: {description}
Expected Output: {expected_output}

Previous Context:
{context}""")
    ])

    def execute_tools_if_called(resp_msg, p_template, p_vars) -> AnyMessage:
        parsed_tool_calls = []
        
        if hasattr(resp_msg, "tool_calls") and resp_msg.tool_calls and tools:
            for tc in resp_msg.tool_calls:
                parsed_tool_calls.append({
                    "id": tc.get("id"),
                    "name": tc["name"],
                    "args": tc["args"],
                    "source": "native"
                })
        elif is_devstral and tools:
            import re
            import json
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, resp_msg.content, re.DOTALL)
            if match:
                try:
                    tc_data = json.loads(match.group(1))
                    if "tool" in tc_data and "args" in tc_data:
                        parsed_tool_calls.append({
                            "id": "devstral_call",
                            "name": tc_data["tool"],
                            "args": tc_data["args"],
                            "source": "parsed"
                        })
                except Exception:
                    pass

        if not parsed_tool_calls:
            return resp_msg

        # Construct message list to support tool interaction
        msgs = p_template.format_messages(**p_vars)
        msgs.append(resp_msg)
        
        for tool_call in parsed_tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            tool_to_use = next((t for t in tools if t.name == tool_name), None)
            if tool_to_use:
                print(f"[{task.task_id}] Executing tool '{tool_name}' with arguments: {tool_args}")
                try:
                    tool_result = tool_to_use.invoke(tool_args)
                except Exception as e:
                    tool_result = f"Error executing tool '{tool_name}': {str(e)}"
                
                if tool_call["source"] == "native":
                    from langchain_core.messages import ToolMessage
                    msgs.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    ))
                else:
                    from langchain_core.messages import HumanMessage
                    msgs.append(HumanMessage(
                        content=f"Tool output of `{tool_name}`: {str(tool_result)}"
                    ))
            else:
                if tool_call["source"] == "native":
                    from langchain_core.messages import ToolMessage
                    msgs.append(ToolMessage(
                        content=f"Error: Tool {tool_name} not found.",
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    ))
                else:
                    from langchain_core.messages import HumanMessage
                    msgs.append(HumanMessage(
                        content=f"Error: Tool {tool_name} not found."
                    ))
        
        # Invoke LLM again with the tool outputs
        return llm.invoke(msgs)

    worker_vars = {
        "worker_type": task.worker_type or "general",
        "topic": topic,
        "description": task.description,
        "expected_output": task.expected_output or "High-quality result",
        "context": context or "No previous context available."
    }

    chain = worker_prompt | llm
    response = chain.invoke(worker_vars)
    response = execute_tools_if_called(response, worker_prompt, worker_vars)

    output_content = response.content if hasattr(response, "content") else str(response)

    # Self-Correction Critic Loop
    # Only critique primary tasks (research, writing, analysis, coding, review). Skip file_writer.
    if task.worker_type in ["research", "writing", "analysis", "coding", "review"]:
        max_retries = 2
        retry_count = 0
        
        critic_llm = ChatOllama(
            model="llama3.1",
            temperature=0.0
        )
        
        class CriticEvaluation(BaseModel):
            status: Literal["APPROVED", "REJECTED"] = Field(description="Whether the output is approved or needs revision")
            feedback: str = Field(description="Detailed feedback or guidance for the worker if rejected")
            
        critic_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert critic and quality assurance agent.
            Your task is to evaluate if a worker agent's output successfully satisfies the requested task and expected output.
            Provide your assessment in a strict structured format:
            1. Status: APPROVED or REJECTED
            2. Feedback: If rejected, specify exactly what is missing, incorrect, or needs improvement. If approved, keep feedback brief.
            
            IMPORTANT: Ensure that your JSON output is valid. The 'feedback' field must not contain raw unescaped newlines or control characters. Escape any newlines as '\\n'."""),
            ("user", """Task Description: {description}
            Expected Output: {expected_output}
            
            Worker Output:
            {output}""")
        ])
        
        critic_chain = critic_prompt | critic_llm.with_structured_output(CriticEvaluation)
        
        while retry_count < max_retries:
            print(f"[{task.task_id}] Submitting output to critic for review...")
            try:
                evaluation = critic_chain.invoke({
                    "description": task.description,
                    "expected_output": task.expected_output or "High-quality result",
                    "output": output_content
                })
            except Exception as e:
                print(f"[{task.task_id}] Critic review error: {str(e)}. Auto-approving.")
                break
                
            print(f"[{task.task_id}] Critic Status: {evaluation.status}")
            if evaluation.status == "APPROVED":
                print(f"[{task.task_id}] Critic Approved! Proceeding.")
                break
                
            retry_count += 1
            print(f"[{task.task_id}] Critic Rejected (Attempt {retry_count}/{max_retries})!")
            print(f"[{task.task_id}] Critic Feedback: {evaluation.feedback}")
            
            # Feed feedback back to the worker prompt and re-run
            system_instruction_revised = (
                f"You are a specialized {task.worker_type} agent.\n"
                f"Your previous attempt was REJECTED by the critic.\n"
                f"CRITIC FEEDBACK: {evaluation.feedback}\n"
                f"Please revise your work to address all comments thoroughly."
            )
            if is_devstral and tools:
                tool_descriptions = "\n".join([f"- `{t.name}`: {t.description}" for t in tools])
                system_instruction_revised += "\n\nYou can call the following tools by outputting a JSON block:\n" + tool_descriptions + "\n\nTo call a tool, you MUST output a JSON block formatted exactly like this:\n```json\n{{\n  \"tool\": \"tool_name\",\n  \"args\": {{\n    \"arg_name\": \"arg_value\"\n  }}\n}}\n```\nDo not output anything else after the JSON block. Once the tool results are provided, they will be given as a user response, and you can output your final result."
            
            worker_prompt_revised = ChatPromptTemplate.from_messages([
                ("system", system_instruction_revised),
                ("user", """Main Topic: {topic}
    
    Task: {description}
    Expected Output: {expected_output}
    
    Previous Context:
    {context}""")
            ])
            
            # Re-run chain
            chain = worker_prompt_revised | llm
            response = chain.invoke(worker_vars)
            response = execute_tools_if_called(response, worker_prompt_revised, worker_vars)
            output_content = response.content if hasattr(response, "content") else str(response)

    return {
        "completed_tasks": [task],
        "results": [{
            "task_id": task.task_id,
            "worker_type": task.worker_type,
            "output": output_content
        }]
    }


def synthesizer(state: State) -> dict:
    """Final synthesis node."""
    results = state.get("results", [])
    plan = state.get("plan")

    compiled = "\n\n".join([
        f"### {r.get('task_id')} ({r.get('worker_type')}):\n{r.get('output')}"
        for r in results
    ])

    synth_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert editor. Synthesize all inputs into a cohesive final report."),
        ("user", """Topic: {topic}
Final Goal: {final_goal}

Worker Outputs:
{compiled_results}""")
    ])

    llm = ChatOllama(
        model="llama3.1",
        temperature=0.3
    )

    chain = synth_prompt | llm
    response = chain.invoke({
        "topic": state["topic"],
        "final_goal": plan.final_goal if plan else "Produce a comprehensive report",
        "compiled_results": compiled
    })

    return {
        "final_report": response.content,
        "status": "completed"
    }


def route_tasks(state: State):
    """Route ready tasks to workers or go to synthesizer."""
    # Check if we are still planning/feedback loop
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
            "previous_results": state.get("results", [])
        }) for task in ready_tasks
    ]


# ========================== GRAPH DEFINITION ==========================

# Define the StateGraph
workflow = StateGraph(State)

# Add our nodes
workflow.add_node("orchestrator", orchestrator)
workflow.add_node("human_approval", human_approval)
workflow.add_node("worker", worker)
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        try:
            topic = input("Enter the topic/question you want to orchestrate: ").strip()
            if not topic:
                print("Topic cannot be empty. Exiting.")
                exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            exit(0)

    inputs = {"topic": topic}
    
    print(f"\nRunning orchestrator-worker graph for: '{topic}'...")
    # Stream the execution so you can see each node running step-by-step
    for event in app.stream(inputs):
        for node, output in event.items():
            if node == "human_approval":
                continue
            print(f"\n================ Node: {node} ================")
            if node == "orchestrator":
                plan = output.get("plan")
                if plan:
                    print(f"Plan Created: {plan.overall_strategy}")
                    for task in plan.tasks:
                        print(f" - [{task.task_id}] ({task.worker_type}): {task.description} (Deps: {task.dependencies})")
            elif node == "worker":
                for res in output.get("results", []):
                    print(f"Task completed: {res['task_id']}")
                    print(f"\n--- Output of {res['task_id']} ({res['worker_type']}) ---")
                    print(res['output'])
                    print("-" * 50 + "\n")
            elif node == "synthesizer":
                print("\n=== FINAL REPORT ===")
                print(output["final_report"])
