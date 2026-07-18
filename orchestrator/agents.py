import builtins
_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _print(*args, **kwargs)

from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from . import config
from .states import State, WorkerState, OrchestratorPlan
from .tools import (write_file_tool, read_file_tool, fetch_webpage_tool, query_knowledge_base,
                     list_directory_tool, scan_dependencies_tool, fetch_github_repo_tool,
                     geoip_lookup_tool, threat_intel_lookup_tool, neural_threat_score_tool, domain_category_tool)

worker_config = config.load_config()

def get_node_llm(node_type: str):
    """Creates the appropriate LLM for a given node type from the configuration."""
    conf = config.load_config().get(node_type, config.DEFAULT_CONFIG.get(node_type))
    if not conf:
        conf = config.DEFAULT_CONFIG["orchestrator"]
    backend = conf["backend"]
    model = conf["model"]
    temperature = float(conf["temperature"])
    
    if backend == "Gemini":
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, safety_settings=safety_settings)
    elif backend == "Groq":
        return ChatGroq(model=model, temperature=temperature)
    else:
        return ChatOllama(model=model, temperature=temperature)

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
        - "file_writer": write content/code to local files on disk
        - "security_audit": perform security vulnerability analysis, code auditing, config review, dependency scanning, OWASP Top 10 checks"""),
        MessagesPlaceholder(variable_name="messages", optional=True),
        ("user", "Topic: {topic}\n\nHuman feedback for previous plan adjustments (if any): {feedback}")
    ])

    llm = get_node_llm("orchestrator")
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

def worker_step(state: WorkerState) -> dict:
    """Executes the assigned task using the appropriate LLM and tools."""
    task = state["task"]
    topic = state["topic"]
    prev_results = state.get("previous_results", [])
    feedback = state.get("critic_feedback")

    context = "\n\n".join([
        f"--- Output of {r.get('task_id')} ({r.get('worker_type')}) ---\n{r.get('output')}"
        for r in prev_results
    ])

    w_conf = worker_config.get(task.worker_type, config.DEFAULT_CONFIG.get(task.worker_type, config.DEFAULT_CONFIG["review"]))
    model = w_conf["model"]
    backend = w_conf["backend"]
    temperature = float(w_conf["temperature"])
    custom_prompt = w_conf.get("custom_prompt", "")


    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent
    
    @tool
    def delegate_to_agent(agent_type: Literal["research", "writing", "analysis", "coding", "review", "security_audit"], query: str) -> str:
        """Delegates a specific sub-task or question to another specialized agent.
        Use this if you need information or capabilities outside your domain.
        Returns the final answer from the agent.
        """
        print(f"  [Delegating] Sending query to {agent_type} agent...")
        w_conf = worker_config.get(agent_type, config.DEFAULT_CONFIG.get(agent_type, config.DEFAULT_CONFIG["review"]))
        del_model = w_conf["model"]
        del_backend = w_conf["backend"]
        del_temp = float(w_conf["temperature"])
        
        agent_tools = []
        if agent_type == "research":
            agent_tools = [DuckDuckGoSearchResults(max_results=3), fetch_webpage_tool, query_knowledge_base]
        elif agent_type == "analysis":
            agent_tools = [read_file_tool, query_knowledge_base]
        elif agent_type in ["coding", "file_writer"]:
            agent_tools = [read_file_tool, write_file_tool]
        elif agent_type == "review":
            agent_tools = [read_file_tool]
        elif agent_type == "security_audit":
            agent_tools = [read_file_tool, list_directory_tool, scan_dependencies_tool, query_knowledge_base,
                           fetch_webpage_tool, fetch_github_repo_tool, geoip_lookup_tool,
                           threat_intel_lookup_tool, neural_threat_score_tool, domain_category_tool]
            
        if del_backend == "Gemini":
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            agent_llm = ChatGoogleGenerativeAI(model=del_model, temperature=del_temp, safety_settings=safety_settings)
        elif del_backend == "Groq":
            agent_llm = ChatGroq(model=del_model, temperature=del_temp)
        else:
            agent_llm = ChatOllama(model=del_model, temperature=del_temp)
            
        try:
            agent_executor = create_react_agent(agent_llm, agent_tools)
            sys_msg = f"You are a {agent_type} agent.\nAnswer the delegated query."
            result = agent_executor.invoke({"messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": query}]})
            return result["messages"][-1].content
        except Exception as e:
            return f"Delegation failed: {str(e)}"
            
    tools = [delegate_to_agent]
    if task.worker_type == "research":
        tools = [DuckDuckGoSearchResults(max_results=3), fetch_webpage_tool, query_knowledge_base]
    elif task.worker_type == "analysis":
        tools = [read_file_tool, query_knowledge_base]
    elif task.worker_type == "coding" or task.worker_type == "file_writer":
        tools = [read_file_tool, write_file_tool]
    elif task.worker_type == "review":
        tools = [read_file_tool]
    elif task.worker_type == "security_audit":
        tools = [read_file_tool, list_directory_tool, scan_dependencies_tool, query_knowledge_base,
                 fetch_webpage_tool, fetch_github_repo_tool, geoip_lookup_tool,
                 threat_intel_lookup_tool, neural_threat_score_tool, domain_category_tool]

    is_devstral = (model == "devstral:latest")

    if backend == "Gemini":
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        llm = ChatGoogleGenerativeAI(model=model, temperature=temperature, safety_settings=safety_settings)
    elif backend == "Groq":
        llm = ChatGroq(model=model, temperature=temperature)
    else:
        llm = ChatOllama(model=model, temperature=temperature)

    if tools and not is_devstral:
        llm = llm.bind_tools(tools)

    if task.worker_type == "security_audit":
        system_instruction = """You are an expert security auditor and penetration tester (white-hat).
Analyze the provided code, configuration files, or URL content for security vulnerabilities.

For each finding, report in this structured format:
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW / INFO
- **OWASP Category**: (e.g., A01:2021 Broken Access Control, A03:2021 Injection, etc.)
- **CWE ID**: (e.g., CWE-79, CWE-89, etc.)
- **Vulnerable Code/Config**: The exact code snippet or config line
- **Description**: What the vulnerability is and how it can be exploited
- **Remediation**: Specific fix with code examples

Check for: SQL Injection, XSS, SSRF, Path Traversal, Hardcoded Secrets/API Keys,
Insecure Deserialization, Broken Authentication, Security Misconfiguration,
Vulnerable Dependencies, Insufficient Logging, Command Injection,
Insecure File Operations, CSRF, Open Redirects, Insecure Direct Object References,
Missing Security Headers, Weak Cryptography, Information Disclosure.

Use your tools to:
- read_file_tool / list_directory_tool: Read and discover source code and config files
- scan_dependencies_tool: Check package manifests for vulnerable dependencies
- geoip_lookup_tool: Look up geographic origin of IP addresses
- threat_intel_lookup_tool: Check IPs against threat intelligence patterns
- neural_threat_score_tool: Score network traffic patterns with the neural network model
- domain_category_tool: Classify and assess risk of domains
- query_knowledge_base: Search local security documentation
- fetch_webpage_tool / fetch_github_repo_tool: Fetch external content for analysis

Be thorough and methodical. At the end, provide a summary table of all findings sorted by severity."""
    else:
        system_instruction = f"You are a specialized {task.worker_type} agent.\nExecute the assigned task thoroughly and professionally.\nUse provided context from previous tasks when relevant."

    # Inject uploaded context if available
    uploaded_ctx = state.get("uploaded_context", "")
    if uploaded_ctx:
        system_instruction += f"\n\n[UPLOADED CONTENT FOR ANALYSIS]\n{uploaded_ctx}"
    
    if feedback:
        system_instruction += f"\n\nYour previous attempt was REJECTED by the critic.\nCRITIC FEEDBACK: {feedback}\nPlease revise your work to address all comments thoroughly."
        
    if custom_prompt.strip():
        system_instruction += f"\n\n[CUSTOM INSTRUCTIONS]\n{custom_prompt.strip()}"
    if is_devstral and tools:
        tool_descriptions = "\n".join([f"- `{t.name}`: {t.description}" for t in tools])
        system_instruction += "\n\nYou can call the following tools by outputting a JSON block:\n" + tool_descriptions + "\n\nTo call a tool, you MUST output a JSON block formatted exactly like this:\n```json\n{{\n  \"tool\": \"tool_name\",\n  \"args\": {{\n    \"arg_name\": \"arg_value\"\n  }}\n}}\n```\nDo not output anything else after the JSON block. Once the tool results are provided, they will be given as a user response, and you can output your final result."

    if task.worker_type == "file_writer":
        system_instruction += "\nIMPORTANT: You must write the file to the filesystem by calling the 'write_file_tool' tool. Do not just output the file contents as text; you must call the tool."

    worker_prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("user", """Main Topic: {topic}\n\nTask: {description}\nExpected Output: {expected_output}\n\nPrevious Context:\n{context}""")
    ])

    def execute_tools_if_called(resp_msg, p_template, p_vars) -> AnyMessage:
        parsed_tool_calls = []
        if hasattr(resp_msg, "tool_calls") and resp_msg.tool_calls and tools:
            for tc in resp_msg.tool_calls:
                parsed_tool_calls.append({"id": tc.get("id"), "name": tc["name"], "args": tc["args"], "source": "native"})
        elif is_devstral and tools:
            import re, json
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, resp_msg.content, re.DOTALL)
            if match:
                try:
                    tc_data = json.loads(match.group(1))
                    if "tool" in tc_data and "args" in tc_data:
                        parsed_tool_calls.append({"id": "devstral_call", "name": tc_data["tool"], "args": tc_data["args"], "source": "parsed"})
                except Exception:
                    pass

        if not parsed_tool_calls:
            return resp_msg

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
                    msgs.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"], name=tool_name))
                else:
                    from langchain_core.messages import HumanMessage
                    msgs.append(HumanMessage(content=f"Tool output of `{tool_name}`: {str(tool_result)}"))
            else:
                err_msg = f"Error: Tool {tool_name} not found."
                if tool_call["source"] == "native":
                    from langchain_core.messages import ToolMessage
                    msgs.append(ToolMessage(content=err_msg, tool_call_id=tool_call["id"], name=tool_name))
                else:
                    from langchain_core.messages import HumanMessage
                    msgs.append(HumanMessage(content=err_msg))
        
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
    return {"output": output_content}


def critic_step(state: WorkerState) -> dict:
    """Evaluates the worker's output and determines if it meets requirements."""
    task = state["task"]
    output_content = state.get("output", "")
    
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
    
    critic_llm = get_node_llm("critic")
    critic_chain = critic_prompt | critic_llm.with_structured_output(CriticEvaluation)
    
    print(f"[{task.task_id}] Submitting output to critic for review...")
    try:
        evaluation = critic_chain.invoke({
            "description": task.description,
            "expected_output": task.expected_output or "High-quality result",
            "output": output_content
        })
        status = evaluation.status
        feedback = evaluation.feedback
    except Exception as e:
        print(f"[{task.task_id}] Critic review error: {str(e)}. Auto-approving.")
        status = "APPROVED"
        feedback = ""
        
    print(f"[{task.task_id}] Critic Status: {status}")
    if status == "REJECTED":
        print(f"[{task.task_id}] Critic Feedback: {feedback}")

    return {
        "critic_feedback": feedback,
        "critic_status": status,
        "retries": state.get("retries", 0) + 1
    }


def finalize_worker(state: WorkerState) -> dict:
    """Packages the worker's output to return to the parent graph."""
    task = state["task"]
    return {
        "completed_tasks": [task],
        "results": [{
            "task_id": task.task_id,
            "worker_type": task.worker_type,
            "output": state.get("output", "")
        }]
    }

def route_worker(state: WorkerState) -> str:
    """Routes after worker_step."""
    task = state["task"]
    if task.worker_type == "file_writer":
        return "finalize_worker"
    return "critic_step"

def route_critic(state: WorkerState) -> str:
    """Routes after critic_step."""
    if state.get("critic_status") == "APPROVED":
        return "finalize_worker"
    if state.get("retries", 0) >= 2:
        print(f"[{state['task'].task_id}] Max retries reached. Forcing approval.")
        return "finalize_worker"
    return "worker_step"

# Build the Worker SubGraph
worker_workflow = StateGraph(WorkerState)
worker_workflow.add_node("worker_step", worker_step)
worker_workflow.add_node("critic_step", critic_step)
worker_workflow.add_node("finalize_worker", finalize_worker)

worker_workflow.set_entry_point("worker_step")
worker_workflow.add_conditional_edges("worker_step", route_worker, ["critic_step", "finalize_worker"])
worker_workflow.add_conditional_edges("critic_step", route_critic, ["worker_step", "finalize_worker"])
worker_workflow.add_edge("finalize_worker", END)
worker_app = worker_workflow.compile()


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
        ("user", """Topic: {topic}\nFinal Goal: {final_goal}\n\nWorker Outputs:\n{compiled_results}""")
    ])

    llm = get_node_llm("synthesizer")
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
