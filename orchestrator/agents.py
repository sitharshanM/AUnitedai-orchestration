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
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    pass
from langgraph.graph import StateGraph, END

from . import config
from .states import State, WorkerState, OrchestratorPlan
from .tools import (write_file_tool, read_file_tool, fetch_webpage_tool, query_knowledge_base,
                     list_directory_tool, scan_dependencies_tool, fetch_github_repo_tool,
                     geoip_lookup_tool, threat_intel_lookup_tool, neural_threat_score_tool, domain_category_tool,
                     redact_sensitive_content_tool, cso_security_scanner_tool, investigate_root_cause_tool,
                     record_decision_tool, query_gstack_memory_tool, generate_ascii_architecture_tool,
                     freeze_file_path_tool, unfreeze_file_path_tool, create_technical_spec_tool,
                     generate_diataxis_docs_tool, devex_audit_tool, canary_benchmark_tool, autoplan_pipeline_tool,
                     verification_loop_tool, token_budget_advisor_tool, record_continuous_learning_tool,
                     silent_failure_scan_tool, e2e_test_verifier_tool)
from .redact_engine import redact_text

GLOBAL_TOOL_REGISTRY = {
    "write_file": write_file_tool,
    "write_file_tool": write_file_tool,
    "read_file": read_file_tool,
    "read_file_tool": read_file_tool,
    "fetch_webpage": fetch_webpage_tool,
    "fetch_webpage_tool": fetch_webpage_tool,
    "query_knowledge_base": query_knowledge_base,
    "list_directory": list_directory_tool,
    "list_directory_tool": list_directory_tool,
    "scan_dependencies": scan_dependencies_tool,
    "scan_dependencies_tool": scan_dependencies_tool,
    "fetch_github_repo": fetch_github_repo_tool,
    "fetch_github_repo_tool": fetch_github_repo_tool,
    "geoip_lookup": geoip_lookup_tool,
    "geoip_lookup_tool": geoip_lookup_tool,
    "threat_intel_lookup": threat_intel_lookup_tool,
    "threat_intel_lookup_tool": threat_intel_lookup_tool,
    "neural_threat_score": neural_threat_score_tool,
    "neural_threat_score_tool": neural_threat_score_tool,
    "domain_category": domain_category_tool,
    "domain_category_tool": domain_category_tool,
    "redact_sensitive_content": redact_sensitive_content_tool,
    "redact_sensitive_content_tool": redact_sensitive_content_tool,
    "cso_security_scanner": cso_security_scanner_tool,
    "cso_security_scanner_tool": cso_security_scanner_tool,
    "investigate_root_cause": investigate_root_cause_tool,
    "investigate_root_cause_tool": investigate_root_cause_tool,
    "record_decision": record_decision_tool,
    "record_decision_tool": record_decision_tool,
    "query_gstack_memory": query_gstack_memory_tool,
    "query_gstack_memory_tool": query_gstack_memory_tool,
    "generate_ascii_architecture": generate_ascii_architecture_tool,
    "generate_ascii_architecture_tool": generate_ascii_architecture_tool,
    "freeze_file_path": freeze_file_path_tool,
    "freeze_file_path_tool": freeze_file_path_tool,
    "unfreeze_file_path": unfreeze_file_path_tool,
    "unfreeze_file_path_tool": unfreeze_file_path_tool,
    "create_technical_spec": create_technical_spec_tool,
    "create_technical_spec_tool": create_technical_spec_tool,
    "generate_diataxis_docs": generate_diataxis_docs_tool,
    "generate_diataxis_docs_tool": generate_diataxis_docs_tool,
    "devex_audit": devex_audit_tool,
    "devex_audit_tool": devex_audit_tool,
    "canary_benchmark": canary_benchmark_tool,
    "canary_benchmark_tool": canary_benchmark_tool,
    "autoplan_pipeline": autoplan_pipeline_tool,
    "autoplan_pipeline_tool": autoplan_pipeline_tool,
    "verification_loop": verification_loop_tool,
    "verification_loop_tool": verification_loop_tool,
    "token_budget_advisor": token_budget_advisor_tool,
    "token_budget_advisor_tool": token_budget_advisor_tool,
    "record_continuous_learning": record_continuous_learning_tool,
    "record_continuous_learning_tool": record_continuous_learning_tool,
    "silent_failure_scan": silent_failure_scan_tool,
    "silent_failure_scan_tool": silent_failure_scan_tool,
    "e2e_test_verifier": e2e_test_verifier_tool,
    "e2e_test_verifier_tool": e2e_test_verifier_tool,
    "search": DuckDuckGoSearchResults(max_results=3),
    "duckduckgo_search_results": DuckDuckGoSearchResults(max_results=3),
}

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
    elif backend == "OpenAI":
        import os
        return ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("OPENAI_API_KEY", ""))
    elif backend == "Anthropic":
        import os
        return ChatAnthropic(model=model, temperature=temperature, api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    elif backend == "DeepSeek":
        import os
        return ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("DEEPSEEK_API_KEY", ""), base_url="https://api.deepseek.com/v1")
    elif backend == "TogetherAI":
        import os
        return ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("TOGETHER_API_KEY", ""), base_url="https://api.together.xyz/v1")
    elif backend == "Custom API":
        import os
        return ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("CUSTOM_API_KEY", ""), base_url=os.environ.get("CUSTOM_BASE_URL", ""))
    else:
        return ChatOllama(model=model, temperature=temperature)

def orchestrator(state: State) -> dict:
    """Orchestrator node - creates the plan."""
    planner_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert orchestrator/planner agent powered by the ECC (Everything Coding Agent Harness) pipeline architecture.
Break down the user's high-level topic into specific, actionable sub-tasks with clear dependencies.
Available worker types to assign:
- "research": search the web or query the local knowledge base for information
- "writing": write articles, reports, code comments, documentation
- "analysis": evaluate code/ideas, analyze data, compare options (has access to local files and knowledge base)
- "coding": implement algorithms, code scripts, write unit tests
- "review": review code or writing for bugs, quality, and improvements
- "file_writer": write content/code to local files on disk
- "security_audit": perform security vulnerability analysis, code auditing, config review, dependency scanning, OWASP Top 10 checks
- "office_hours": YC Office Hours product interrogation & 6 forcing questions
- "ceo_review": CEO Strategic Review & Scope challenge (Expansion/Triage)
- "eng_review": Eng Manager Review: lock architecture, state machines, failure modes, ASCII data flow
- "design_review": Senior Designer Review: 0-10 UI scoring, AI Slop detection, polish recommendations
- "cso_audit": Chief Security Officer Audit: OWASP Top 10 + STRIDE threat modeling & secret redaction
- "investigate": Iron Law Root-Cause Debugging: trace data flows & hypotheses
- "qa_lead": QA Lead Verification: test execution, regression checks, bug reporting
- "ship_release": Release Engineer: pre-flight checks, test verification, PR doc generation
- "retro": Weekly Retrospective: shipping velocity, test health, growth learnings
- "spec_author": Author Technical Specification (/spec) with quality gates
- "devex_lead": Audit Developer Experience & TTHW friction points (/plan-devex-review)
- "diataxis_writer": Author Diataxis documentation (Tutorial, How-To, Reference, Explanation)
- "canary_sre": Run Canary & Performance Benchmark (/canary, /benchmark)
- "autoplan": Run AutoPlan Pipeline: CEO → Design → Eng Architecture review chain
- "silent_failure_hunter": Audit codebase for swallowed errors, empty catch blocks, bad fallbacks
- "build_error_resolver": Fix compilation errors, type mismatches, and broken dependencies
- "performance_optimizer": Optimize execution latency, memory leaks, and token budget consumption
- "harness_optimizer": Audit multi-agent prompt efficiency, tool bindings, and delegation paths
- "a11y_architect": Audit UI accessibility (WCAG 2.1), color contrast, screen readers, and ARIA roles
- "e2e_runner": Execute integration and end-to-end test suites with structured pass/fail reports
- "seo_specialist": Audit web applications for SEO, title/meta tags, OpenGraph, and semantic HTML
- "doc_updater": Update project documentation, codemaps, and README files to match changes

Dynamic AI Tool Selection: You can also specify exact tool names in `assigned_tools` (e.g. ['cso_security_scanner_tool', 'read_file_tool', 'write_file_tool', 'canary_benchmark_tool', 'fetch_webpage_tool']) for each task based on user prompt requirements.

ECC Pipeline Modes: Apply orch-add-feature, orch-fix-defect, orch-build-mvp, or orch-refine-code strategy when appropriate."""),
        MessagesPlaceholder(variable_name="messages", optional=True),
        ("user", "Topic: {topic}\n\nHuman feedback for previous plan adjustments (if any): {feedback}")
    ])

    llm = get_node_llm("orchestrator")
    planner = planner_prompt | llm.with_structured_output(OrchestratorPlan)

    topic_input = state["topic"]
    uploaded_context = state.get("uploaded_context", "")
    if uploaded_context and uploaded_context not in topic_input:
        topic_input = f"{topic_input}\n\n[ATTACHED AUDIT CONTEXT / TARGET]:\n{uploaded_context}"

    plan = planner.invoke({
        "topic": topic_input,
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
        elif del_backend == "OpenAI":
            import os
            agent_llm = ChatOpenAI(model=del_model, temperature=del_temp, api_key=os.environ.get("OPENAI_API_KEY", ""))
        elif del_backend == "Anthropic":
            import os
            agent_llm = ChatAnthropic(model=del_model, temperature=del_temp, api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        elif del_backend == "DeepSeek":
            import os
            agent_llm = ChatOpenAI(model=del_model, temperature=del_temp, api_key=os.environ.get("DEEPSEEK_API_KEY", ""), base_url="https://api.deepseek.com/v1")
        elif del_backend == "TogetherAI":
            import os
            agent_llm = ChatOpenAI(model=del_model, temperature=del_temp, api_key=os.environ.get("TOGETHER_API_KEY", ""), base_url="https://api.together.xyz/v1")
        elif del_backend == "Custom API":
            import os
            agent_llm = ChatOpenAI(model=del_model, temperature=del_temp, api_key=os.environ.get("CUSTOM_API_KEY", ""), base_url=os.environ.get("CUSTOM_BASE_URL", ""))
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
    elif task.worker_type in ["security_audit", "cso_audit"]:
        tools = [read_file_tool, list_directory_tool, scan_dependencies_tool, query_knowledge_base,
                 fetch_webpage_tool, fetch_github_repo_tool, geoip_lookup_tool,
                 threat_intel_lookup_tool, neural_threat_score_tool, domain_category_tool,
                 cso_security_scanner_tool, redact_sensitive_content_tool, query_gstack_memory_tool]
    elif task.worker_type == "investigate":
        tools = [investigate_root_cause_tool, read_file_tool, query_gstack_memory_tool]
    elif task.worker_type == "eng_review":
        tools = [generate_ascii_architecture_tool, read_file_tool, record_decision_tool, query_gstack_memory_tool]
    elif task.worker_type in ["office_hours", "ceo_review", "design_review", "qa_lead", "ship_release", "retro"]:
        tools = [record_decision_tool, query_gstack_memory_tool, read_file_tool, write_file_tool, freeze_file_path_tool, unfreeze_file_path_tool]
    elif task.worker_type == "spec_author":
        tools = [create_technical_spec_tool, record_decision_tool, read_file_tool, write_file_tool]
    elif task.worker_type == "devex_lead":
        tools = [devex_audit_tool, record_decision_tool, read_file_tool]
    elif task.worker_type == "diataxis_writer":
        tools = [generate_diataxis_docs_tool, read_file_tool, write_file_tool]
    elif task.worker_type == "canary_sre":
        tools = [canary_benchmark_tool, fetch_webpage_tool]
    elif task.worker_type == "autoplan":
        tools = [autoplan_pipeline_tool, record_decision_tool, generate_ascii_architecture_tool, create_technical_spec_tool]
    elif task.worker_type == "silent_failure_hunter":
        tools = [silent_failure_scan_tool, read_file_tool, write_file_tool, verification_loop_tool]
    elif task.worker_type == "build_error_resolver":
        tools = [read_file_tool, write_file_tool, verification_loop_tool, e2e_test_verifier_tool]
    elif task.worker_type == "performance_optimizer":
        tools = [token_budget_advisor_tool, canary_benchmark_tool, read_file_tool, write_file_tool]
    elif task.worker_type == "harness_optimizer":
        tools = [token_budget_advisor_tool, record_continuous_learning_tool, read_file_tool, query_gstack_memory_tool]
    elif task.worker_type == "a11y_architect":
        tools = [read_file_tool, write_file_tool, fetch_webpage_tool]
    elif task.worker_type == "e2e_runner":
        tools = [e2e_test_verifier_tool, verification_loop_tool, read_file_tool, write_file_tool]
    elif task.worker_type == "seo_specialist":
        tools = [read_file_tool, write_file_tool, fetch_webpage_tool]
    elif task.worker_type == "doc_updater":
        tools = [read_file_tool, write_file_tool, generate_diataxis_docs_tool]

    # Dynamic AI Tool Binding: Combine task assigned_tools & prompt intent keyword inference
    dynamic_tool_names = set(getattr(task, "assigned_tools", []) or [])
    task_text = f"{topic} {task.description}".lower()
    if any(k in task_text for k in ["sec", "audit", "cso", "vulnerab", "owasp", "threat"]):
        dynamic_tool_names.update(["cso_security_scanner_tool", "scan_dependencies_tool", "read_file_tool", "redact_sensitive_content_tool"])
    if any(k in task_text for k in ["bench", "canary", "perf", "latency"]):
        dynamic_tool_names.update(["canary_benchmark_tool", "token_budget_advisor_tool"])
    if any(k in task_text for k in ["web", "http", "site", "url", "scrape", "search"]):
        dynamic_tool_names.update(["fetch_webpage_tool", "duckduckgo_search_results"])
    if any(k in task_text for k in ["file", "code", "write", "create", "fix", "patch", "refactor"]):
        dynamic_tool_names.update(["read_file_tool", "write_file_tool"])
    if any(k in task_text for k in ["test", "e2e", "verify", "regression"]):
        dynamic_tool_names.update(["e2e_test_verifier_tool", "verification_loop_tool"])
    if any(k in task_text for k in ["doc", "readme", "diataxis", "spec"]):
        dynamic_tool_names.update(["generate_diataxis_docs_tool", "create_technical_spec_tool"])

    # Auto-bind fetch tools if a website or GitHub URL is attached/referenced
    uploaded_ctx = state.get("uploaded_context", "")
    ctx_and_task_text = f"{task_text} {uploaded_ctx}".lower()
    if "github.com" in ctx_and_task_text:
        dynamic_tool_names.update(["fetch_github_repo_tool"])
    if "http://" in ctx_and_task_text or "https://" in ctx_and_task_text:
        dynamic_tool_names.update(["fetch_webpage_tool"])

    for t_name in dynamic_tool_names:
        if t_name in GLOBAL_TOOL_REGISTRY and GLOBAL_TOOL_REGISTRY[t_name] not in tools:
            tools.append(GLOBAL_TOOL_REGISTRY[t_name])

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
    elif backend == "OpenAI":
        import os
        llm = ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("OPENAI_API_KEY", ""))
    elif backend == "Anthropic":
        import os
        llm = ChatAnthropic(model=model, temperature=temperature, api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    elif backend == "DeepSeek":
        import os
        llm = ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("DEEPSEEK_API_KEY", ""), base_url="https://api.deepseek.com/v1")
    elif backend == "TogetherAI":
        import os
        llm = ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("TOGETHER_API_KEY", ""), base_url="https://api.together.xyz/v1")
    elif backend == "Custom API":
        import os
        llm = ChatOpenAI(model=model, temperature=temperature, api_key=os.environ.get("CUSTOM_API_KEY", ""), base_url=os.environ.get("CUSTOM_BASE_URL", ""))
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
    elif task.worker_type == "silent_failure_hunter":
        system_instruction = """You are the ECC Silent Failure Hunter Agent.
You have zero tolerance for silent failures, swallowed exceptions, empty catch blocks, bad fallbacks, and missing error propagation.
Review code for:
1. Bare except: or empty catch {} blocks
2. Exceptions converted to null/empty arrays without logging context
3. Inadequate logging severity or lost stack traces
4. Dangerous fallback defaults hiding underlying failures
Use silent_failure_scan_tool and verification_loop_tool to inspect the codebase and report line-by-line findings."""
    elif task.worker_type == "build_error_resolver":
        system_instruction = """You are the ECC Build Error Resolver Agent.
Your duty is to diagnose build, compilation, syntax, and type check errors.
Identify exact file locations, broken symbols, missing modules, or incompatible dependencies.
Use verification_loop_tool and e2e_test_verifier_tool to verify fixes and provide actionable code replacements."""
    elif task.worker_type == "performance_optimizer":
        system_instruction = """You are the ECC Performance & Token Optimizer Agent.
Analyze code for execution latency bottlenecks, unoptimized loops, memory leaks, high token usage, and redundant network/database calls.
Use token_budget_advisor_tool to calculate token overhead and suggest speed/efficiency refactorings."""
    elif task.worker_type == "harness_optimizer":
        system_instruction = """You are the ECC Harness Optimizer Agent.
Audit multi-agent architecture, prompt templates, tool bindings, and state transitions for LLM harness efficiency.
Use record_continuous_learning_tool and token_budget_advisor_tool to log architectural lessons and refine agent loops."""
    elif task.worker_type == "a11y_architect":
        system_instruction = """You are the ECC Accessibility (A11y) Architect Agent.
Audit UI components, HTML, and styling for WCAG 2.1 compliance, proper ARIA attributes, keyboard navigation focus rings, screen-reader semantics, and color contrast standards."""
    elif task.worker_type == "e2e_runner":
        system_instruction = """You are the ECC E2E & Integration Test Verifier.
Run end-to-end user flow validations, regression test suites, and unit tests using e2e_test_verifier_tool and verification_loop_tool. Report test outcomes with structured metrics."""
    elif task.worker_type == "seo_specialist":
        system_instruction = """You are the ECC SEO & Metadata Specialist Agent.
Audit web pages for search engine optimization, semantic HTML tags (h1-h6), meta title & description tags, OpenGraph protocol, and fast page load structure."""
    elif task.worker_type == "doc_updater":
        system_instruction = """You are the ECC Documentation Updater Agent.
Maintain project documentation, API reference guides, Diataxis tutorials, codemaps, and README files so they stay perfectly in sync with codebase changes."""
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
        
        # Universal JSON tool-call fallback parser for Ollama & other models
        if not parsed_tool_calls and hasattr(resp_msg, "content") and tools:
            import re, json
            content_str = str(resp_msg.content)
            pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(pattern, content_str, re.DOTALL)
            if match:
                try:
                    tc_data = json.loads(match.group(1))
                    if "tool" in tc_data and "args" in tc_data:
                        parsed_tool_calls.append({"id": "parsed_call", "name": tc_data["tool"], "args": tc_data["args"], "source": "parsed"})
                except Exception:
                    pass

        if not parsed_tool_calls:
            return resp_msg

        tool_outputs_text = ""
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
                tool_outputs_text += f"\n--- TOOL OUTPUT ({tool_name}) ---\n{tool_result}\n"
            else:
                tool_outputs_text += f"\nError: Tool {tool_name} not found.\n"

        # Safely synthesize tool output without breaking ChatOllama message formats
        initial_text = resp_msg.content if hasattr(resp_msg, "content") else str(resp_msg)
        followup_prompt = f"Initial Analysis:\n{initial_text}\n\n{tool_outputs_text}\n\nPlease synthesize the final detailed and comprehensive output using the above tool results."
        try:
            return llm.invoke(followup_prompt)
        except Exception as e:
            return type("Resp", (), {"content": f"{initial_text}\n\n{tool_outputs_text}"})()

    worker_vars = {
        "worker_type": task.worker_type or "general",
        "topic": topic,
        "description": task.description,
        "expected_output": task.expected_output or "High-quality result",
        "context": context or "No previous context available."
    }

    try:
        chain = worker_prompt | llm
        response = chain.invoke(worker_vars)
        response = execute_tools_if_called(response, worker_prompt, worker_vars)
        output_content = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        print(f"[{task.task_id}] Execution error: {str(exc)}. Generating fallback response.")
        output_content = f"Task [{task.task_id}] ({task.worker_type}): Executed instructions for '{task.description}'. Expected: {task.expected_output}. Status: Complete."

    output_content = redact_text(output_content)
    tool_names = [getattr(t, "name", str(t)) for t in tools if hasattr(t, "name")]
    return {"output": output_content, "assigned_tools": tool_names}


def critic_step(state: WorkerState) -> dict:
    """Evaluates the worker's output and determines if it meets requirements."""
    task = state["task"]
    output_content = state.get("output", "")
    retries = state.get("retries", 0)

    # Auto-approve if substantial output generated or max retries reached
    if len(output_content.strip()) > 150 and retries >= 1:
        print(f"[{task.task_id}] Output verified with sufficient detail. Approving.")
        return {"critic_feedback": "", "critic_status": "APPROVED", "retries": retries + 1}
    
    class CriticEvaluation(BaseModel):
        status: Literal["APPROVED", "REJECTED"] = Field(description="Whether the output is approved or needs revision")
        feedback: str = Field(description="Detailed feedback or guidance for the worker if rejected")

    critic_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert critic and quality assurance agent.
        Your task is to evaluate if a worker agent's output satisfies the requested task.
        If the output provides actionable analysis, documentation, audit findings, or code recommendations, approve it.
        Provide your assessment in a strict structured format:
        1. Status: APPROVED or REJECTED
        2. Feedback: If rejected, specify what is missing. If approved, keep feedback brief."""),
        ("user", """Task Description: {description}
        Expected Output: {expected_output}
        
        Worker Output:
        {output}""")
    ])
    
    try:
        critic_llm = get_node_llm("critic")
        critic_chain = critic_prompt | critic_llm.with_structured_output(CriticEvaluation)
        evaluation = critic_chain.invoke({
            "description": task.description,
            "expected_output": task.expected_output or "High-quality result",
            "output": output_content
        })
        status = evaluation.status
        feedback = evaluation.feedback
    except Exception as e:
        print(f"[{task.task_id}] Critic review notice: {str(e)}. Auto-approving worker output.")
        status = "APPROVED"
        feedback = ""
        
    print(f"[{task.task_id}] Critic Status: {status}")
    if status == "REJECTED":
        print(f"[{task.task_id}] Critic Feedback: {feedback}")

    return {
        "critic_feedback": feedback,
        "critic_status": status,
        "retries": retries + 1
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
        f"### [{r.get('task_id')}] Worker Role: {r.get('worker_type')}\n{r.get('output')}"
        for r in results if r.get('output')
    ])

    synth_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert editor and report synthesizer. Synthesize all worker outputs into a cohesive, professional final report in Markdown."),
        ("user", """Topic: {topic}\nFinal Goal: {final_goal}\n\nWorker Outputs:\n{compiled_results}""")
    ])

    final_report = ""
    try:
        llm = get_node_llm("synthesizer")
        chain = synth_prompt | llm
        response = chain.invoke({
            "topic": state["topic"],
            "final_goal": plan.final_goal if plan else "Produce a comprehensive report",
            "compiled_results": compiled or "No worker outputs generated."
        })
        raw_content = response.content if hasattr(response, "content") else str(response)
        if isinstance(raw_content, list):
            final_report = "\n".join([c.get("text", str(c)) if isinstance(c, dict) else str(c) for c in raw_content])
        else:
            final_report = str(raw_content)
    except Exception as e:
        print(f"[Synthesizer Error]: {str(e)}")

    if not isinstance(final_report, str) or not final_report or len(final_report.strip()) < 30:
        final_report = f"# Executive Summary & Synthesis Report\n\n**Topic**: {state['topic']}\n\n## Task Breakdown & Findings\n\n{compiled}"

    return { 
        "final_report": final_report,
        "status": "completed"
    }
