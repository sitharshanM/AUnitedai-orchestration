# 🛠️ AUnitedAI Multi-Agent System: Tools & Prompts Master Guide

Welcome to the definitive master reference guide for all **32 individual tools**, **245+ worker skills**, and **35+ specialized agent personas** in the **AUnitedAI Multi-Agent Orchestrator**.

This document provides complete documentation for **every single tool in the system**, including parameter schemas, trigger keywords, and **copy-pasteable prompt templates designed to unlock 100% of each tool's potential**.

---

## 📋 Table of Contents
1. [Overview & Dynamic AI Tool Selection](#-overview--dynamic-ai-tool-selection)
2. [Individual Tool Master Reference (All 32 Tools)](#-individual-tool-master-reference)
   - [1. `autoplan_pipeline_tool`](#1-autoplan_pipeline_tool)
   - [2. `canary_benchmark_tool`](#2-canary_benchmark_tool)
   - [3. `create_technical_spec_tool`](#3-create_technical_spec_tool)
   - [4. `cso_security_scanner_tool`](#4-cso_security_scanner_tool)
   - [5. `devex_audit_tool`](#5-devex_audit_tool)
   - [6. `domain_category_tool`](#6-domain_category_tool)
   - [7. `duckduckgo_search_results`](#7-duckduckgo_search_results)
   - [8. `e2e_test_verifier_tool`](#8-e2e_test_verifier_tool)
   - [9. `fetch_github_repo_tool`](#9-fetch_github_repo_tool)
   - [10. `fetch_webpage_tool`](#10-fetch_webpage_tool)
   - [11. `freeze_file_path_tool`](#11-freeze_file_path_tool)
   - [12. `generate_ascii_architecture_tool`](#12-generate_ascii_architecture_tool)
   - [13. `generate_diataxis_docs_tool`](#13-generate_diataxis_docs_tool)
   - [14. `geoip_lookup_tool`](#14-geoip_lookup_tool)
   - [15. `investigate_root_cause_tool`](#15-investigate_root_cause_tool)
   - [16. `list_directory_tool`](#16-list_directory_tool)
   - [17. `neural_threat_score_tool`](#17-neural_threat_score_tool)
   - [18. `query_gstack_memory_tool`](#18-query_gstack_memory_tool)
   - [19. `query_knowledge_base`](#19-query_knowledge_base)
   - [20. `read_file_tool`](#20-read_file_tool)
   - [21. `record_continuous_learning_tool`](#21-record_continuous_learning_tool)
   - [22. `record_decision_tool`](#22-record_decision_tool)
   - [23. `redact_sensitive_content_tool`](#23-redact_sensitive_content_tool)
   - [24. `scan_dependencies_tool`](#24-scan_dependencies_tool)
   - [25. `scrapling_adaptor_parse_tool`](#25-scrapling_adaptor_parse_tool)
   - [26. `scrapling_stealth_fetch_tool`](#26-scrapling_stealth_fetch_tool)
   - [27. `silent_failure_scan_tool`](#27-silent_failure_scan_tool)
   - [28. `threat_intel_lookup_tool`](#28-threat_intel_lookup_tool)
   - [29. `token_budget_advisor_tool`](#29-token_budget_advisor_tool)
   - [30. `unfreeze_file_path_tool`](#30-unfreeze_file_path_tool)
   - [31. `verification_loop_tool`](#31-verification_loop_tool)
   - [32. `write_file_tool`](#32-write_file_tool)
3. [Agent Personas & Skill Prompt Catalogs (245+ Skills)](#-agent-personas--skill-prompt-catalogs)
   - [Agency Agents Engineering Suite (58 Roles)](#agency-agents-engineering-suite-58-roles)
   - [ECC Pipeline & Plugin Skills (15 Roles)](#ecc-pipeline--plugin-skills-15-roles)
   - [gstack & Strix Security Audit Suite (35+ Roles)](#gstack--strix-security-audit-suite-35-roles)
4. [Prompt Engineering Cookbook (Execution Scenarios)](#-prompt-engineering-cookbook)

---

## 🧠 Overview & Dynamic AI Tool Selection

The orchestrator uses an **Automated Dynamic AI Tool Binder**. When a user submits a prompt, the system inspects the prompt's intent and dynamically attaches the required tools to the execution graph.

### Keyword Map for Intent-Based Tool Auto-Binding:
| Prompt Keyword Category | Bound Tools |
| :--- | :--- |
| **Web & Scraping**: `search`, `web`, `url`, `scrape`, `stealth fetch`, `parse html` | `scrapling_stealth_fetch_tool`, `fetch_webpage_tool`, `scrapling_adaptor_parse_tool`, `duckduckgo_search_results` |
| **File Operations**: `file`, `code`, `write`, `read`, `patch`, `create`, `refactor`, `dir` | `read_file_tool`, `write_file_tool`, `list_directory_tool`, `freeze_file_path_tool`, `unfreeze_file_path_tool` |
| **Security & Vulnerabilities**: `sec`, `audit`, `owasp`, `cso`, `scan`, `threat`, `redact`, `cve` | `cso_security_scanner_tool`, `scan_dependencies_tool`, `redact_sensitive_content_tool`, `threat_intel_lookup_tool`, `geoip_lookup_tool`, `neural_threat_score_tool`, `domain_category_tool` |
| **Architecture & Specs**: `arch`, `spec`, `diataxis`, `ascii flow`, `gstack`, `decisions` | `create_technical_spec_tool`, `generate_ascii_architecture_tool`, `generate_diataxis_docs_tool`, `record_decision_tool`, `query_gstack_memory_tool` |
| **Quality & Performance**: `perf`, `benchmark`, `canary`, `token budget`, `silent failure`, `verify`, `e2e` | `silent_failure_scan_tool`, `verification_loop_tool`, `e2e_test_verifier_tool`, `canary_benchmark_tool`, `token_budget_advisor_tool`, `devex_audit_tool`, `autoplan_pipeline_tool` |

---

## 🧰 Individual Tool Master Reference

---

### 1. `autoplan_pipeline_tool`
* **Description**: Executes the automated 3-phase review pipeline (CEO Review -> Senior Designer Review -> Engineering Manager Review) for a feature idea.
* **Parameters**:
  * `feature_idea` (`string`, required): High-level feature concept or architectural proposal.
* **Trigger Keywords**: `autoplan`, `auto plan`, `review pipeline`, `ceo design eng review`
* **Full-Potential Prompt**:
  ```markdown
  Execute autoplan_pipeline_tool for feature_idea="Add multi-tenant real-time notification engine with WebSocket fallbacks". 
  Run the automated CEO -> Senior Designer -> Eng Architecture review chain and output the consolidated feedback report.
  ```

---

### 2. `canary_benchmark_tool`
* **Description**: Executes canary performance benchmarks, monitoring response latencies, memory footprint, and Core Web Vitals.
* **Parameters**:
  * `url_or_endpoint` (`string`, required): HTTP URL, API endpoint, or local path to benchmark.
* **Trigger Keywords**: `canary`, `benchmark`, `latency check`, `perf test`, `core web vitals`
* **Full-Potential Prompt**:
  ```markdown
  Run canary_benchmark_tool on url_or_endpoint="http://localhost:8000/health". 
  Measure latency percentiles (p50, p95, p99), memory consumption, and flag any performance regressions.
  ```

---

### 3. `create_technical_spec_tool`
* **Description**: Generates an executable technical specification document (/spec) complete with architectural requirements, boundary conditions, quality gates, and security constraints.
* **Parameters**:
  * `feature_name` (`string`, required): Name of the feature or system component.
  * `problem_statement` (`string`, required): Problem being solved and business justification.
  * `technical_scope` (`string`, required): Implementation details, data models, and API interfaces.
* **Trigger Keywords**: `spec`, `create spec`, `technical spec`, `author specification`
* **Full-Potential Prompt**:
  ```markdown
  Use create_technical_spec_tool for:
  - feature_name="OAuth2 Refresh Token Rotation Engine"
  - problem_statement="Prevent session hijack by rotating refresh tokens on every use and detecting replay attacks"
  - technical_scope="PostgreSQL storage, Redis token blacklist, JWT validation, 24-hour expiration, and audit logging"
  Generate the complete executable /spec document with quality gates.
  ```

---

### 4. `cso_security_scanner_tool`
* **Description**: Performs Chief Security Officer (CSO) level code security auditing, scanning for OWASP Top 10 vulnerabilities, hardcoded secrets, SQL injection, SSRF, and JWT flaws.
* **Parameters**:
  * `code_or_filepath` (`string`, required): Source code string or local file path to audit.
* **Trigger Keywords**: `cso`, `cso audit`, `security scan`, `owasp audit`, `vulnerability scan`
* **Full-Potential Prompt**:
  ```markdown
  Run cso_security_scanner_tool on code_or_filepath="orchestrator/tools.py". 
  Audit the code for OWASP Top 10 vulnerabilities, hardcoded API keys, unvalidated inputs, and dangerous subprocess calls. Return findings sorted by severity.
  ```

---

### 5. `devex_audit_tool`
* **Description**: Audits Developer Experience (DX) and Time-To-Hello-World (TTHW) friction points in onboarding flows, installation scripts, and developer documentation.
* **Parameters**:
  * `onboarding_flow_description` (`string`, required): Description or code of the developer onboarding process.
* **Trigger Keywords**: `devex`, `dev experience`, `tthw`, `developer onboarding`
* **Full-Potential Prompt**:
  ```markdown
  Use devex_audit_tool to audit onboarding_flow_description="Clone repository, install uv/python dependencies, configure .env, run fastapi server and streamlit UI". 
  Identify friction points, missing setup validations, and recommendations to reduce TTHW under 3 minutes.
  ```

---

### 6. `domain_category_tool`
* **Description**: Classifies a domain name into threat categories (e.g. malware, phishing, legitimate SaaS, search engine) and evaluates risk scores.
* **Parameters**:
  * `domain` (`string`, required): Domain name to categorize (e.g. `example.com`).
* **Trigger Keywords**: `domain category`, `classify domain`, `domain risk`, `domain lookup`
* **Full-Potential Prompt**:
  ```markdown
  Run domain_category_tool for domain="github.com". 
  Determine domain reputation score, threat category, and security risk level.
  ```

---

### 7. `duckduckgo_results_json` / `duckduckgo_search_results`
* **Description**: Executes live DuckDuckGo web searches and returns structured titles, web snippets, and source URLs.
* **Parameters**:
  * `query` (`string`, required): Search terms or query string.
* **Trigger Keywords**: `search`, `web search`, `duckduckgo`, `google search`, `find online`
* **Full-Potential Prompt**:
  ```markdown
  Use duckduckgo_search_results to query="LangGraph multi-agent architecture best practices 2026". 
  Extract top 3 search result titles, snippets, and target URLs.
  ```

---

### 8. `e2e_test_verifier_tool`
* **Description**: Executes end-to-end integration tests, unit test suites, and regression verifications with structured pass/fail reports.
* **Parameters**:
  * `test_filter` (`string`, required): Test pattern, file name, or tag to execute (e.g. `test_median.py` or `all`).
* **Trigger Keywords**: `e2e`, `e2e test`, `verify tests`, `regression test`, `run pytest`
* **Full-Potential Prompt**:
  ```markdown
  Execute e2e_test_verifier_tool with test_filter="all". 
  Run integration test verification, check assertion results, and produce a structured pass/fail matrix.
  ```

---

### 9. `fetch_github_repo_tool`
* **Description**: Fetches repository structure, tree, file content, and commit details from a public GitHub repository.
* **Parameters**:
  * `repo_url` (`string`, required): GitHub repository URL (e.g. `https://github.com/owner/repo`).
* **Trigger Keywords**: `github repo`, `fetch repo`, `clone repo info`, `github url`
* **Full-Potential Prompt**:
  ```markdown
  Use fetch_github_repo_tool on repo_url="https://github.com/msitarzewski/agency-agents". 
  Retrieve the repository directory tree, key markdown files, and architecture structure.
  ```

---

### 10. `fetch_webpage_tool`
* **Description**: Fetches webpage HTML/text using Scrapling (with fallback to `requests` + `BeautifulSoup`) and extracts cleaned text.
* **Parameters**:
  * `url` (`string`, required): Webpage URL to fetch.
* **Trigger Keywords**: `fetch webpage`, `read web page`, `url content`, `scrape page`
* **Full-Potential Prompt**:
  ```markdown
  Run fetch_webpage_tool for url="https://news.ycombinator.com". 
  Fetch page content, strip HTML noise, and return clean text summary.
  ```

---

### 11. `freeze_file_path_tool`
* **Description**: Locks a specified file path in memory to protect it from being modified or overwritten during task execution.
* **Parameters**:
  * `filepath` (`string`, required): Absolute or relative file path to freeze.
* **Trigger Keywords**: `freeze`, `freeze file`, `protect file`, `lock path`
* **Full-Potential Prompt**:
  ```markdown
  Execute freeze_file_path_tool for filepath="orchestrator/states.py". 
  Lock this file path to guarantee no automated agent edits it during refactoring.
  ```

---

### 12. `generate_ascii_architecture_tool`
* **Description**: Generates clean ASCII system architecture diagrams, data flow diagrams, and state machine flowcharts.
* **Parameters**:
  * `component_name` (`string`, required): Name of the system or workflow.
  * `state_flow_description` (`string`, required): Description of nodes, arrows, data inputs, and outputs.
* **Trigger Keywords**: `ascii arch`, `ascii diagram`, `draw architecture`, `flowchart`
* **Full-Potential Prompt**:
  ```markdown
  Use generate_ascii_architecture_tool for:
  - component_name="LangGraph Orchestration Pipeline"
  - state_flow_description="User Prompt -> Orchestrator Planner -> Router -> Worker Nodes (Research, Coding, CSO) -> Critic -> Final Report"
  Render a detailed ASCII diagram.
  ```

---

### 13. `generate_diataxis_docs_tool`
* **Description**: Generates documentation formatted according to the 4 Diataxis pillars: Tutorial, How-To Guide, Technical Reference, or Explanation.
* **Parameters**:
  * `component_name` (`string`, required): Topic or component name.
  * `doc_type` (`string`, required): One of `"tutorial"`, `"how-to"`, `"reference"`, or `"explanation"`.
* **Trigger Keywords**: `diataxis`, `generate docs`, `author tutorial`, `how-to guide`
* **Full-Potential Prompt**:
  ```markdown
  Use generate_diataxis_docs_tool with:
  - component_name="Scrapling Stealth Web Scraping Integration"
  - doc_type="how-to"
  Write a comprehensive step-by-step How-To guide with code examples.
  ```

---

### 14. `geoip_lookup_tool`
* **Description**: Performs IP geolocation lookup, returning country, city, ISP, ASN, and organization data for an IP address.
* **Parameters**:
  * `ip_address` (`string`, required): Target IP address (e.g. `8.8.8.8`).
* **Trigger Keywords**: `geoip`, `ip location`, `lookup ip`, `ip geo`
* **Full-Potential Prompt**:
  ```markdown
  Execute geoip_lookup_tool for ip_address="1.1.1.1". 
  Retrieve country, city, organization, and Autonomous System (ASN) details.
  ```

---

### 15. `investigate_root_cause_tool`
* **Description**: Applies the Iron Law Root-Cause Debugging methodology to trace data flow bugs, exceptions, and unexpected behavior.
* **Parameters**:
  * `symptom_description` (`string`, required): Error traceback or unexpected symptom.
  * `file_context` (`string`, optional): File path or relevant code context.
* **Trigger Keywords**: `investigate`, `root cause`, `debug bug`, `iron law debugging`
* **Full-Potential Prompt**:
  ```markdown
  Run investigate_root_cause_tool with:
  - symptom_description="ModuleNotFoundError: No module named 'curl_cffi' when calling StealthyFetcher"
  - file_context="orchestrator/tools.py"
  Trace root cause across imports, pyproject.toml dependencies, and virtual environment state.
  ```

---

### 16. `list_directory_tool`
* **Description**: Lists all child files and subdirectories at a target directory path.
* **Parameters**:
  * `directory_path` (`string`, optional): Target directory path (defaults to workspace root).
* **Trigger Keywords**: `list dir`, `ls`, `show files`, `directory contents`
* **Full-Potential Prompt**:
  ```markdown
  Use list_directory_tool for directory_path="orchestrator". 
  Return file list, file sizes, and directory tree.
  ```

---

### 17. `neural_threat_score_tool`
* **Description**: Scores network traffic patterns (packet rate, packet size, connection duration, port) using a neural threat assessment model.
* **Parameters**:
  * `packet_rate` (`number`, required): Packets per second.
  * `packet_size_kb` (`number`, required): Average packet size in KB.
  * `connection_duration_hours` (`number`, required): Duration of connection in hours.
  * `port_number` (`integer`, required): Target network port number.
* **Trigger Keywords**: `neural threat`, `threat score`, `traffic analysis`, `packet score`
* **Full-Potential Prompt**:
  ```markdown
  Run neural_threat_score_tool with packet_rate=4500, packet_size_kb=0.5, connection_duration_hours=12, port_number=443. 
  Calculate threat probability score and risk level.
  ```

---

### 18. `query_gstack_memory_tool`
* **Description**: Queries the in-memory decision audit log (gstack decision memory) for architectural decisions and trade-offs.
* **Parameters**:
  * `query` (`string`, required): Topic or keyword to search in decision memory.
* **Trigger Keywords**: `gstack memory`, `query decisions`, `decision log`
* **Full-Potential Prompt**:
  ```markdown
  Run query_gstack_memory_tool for query="Scrapling engine setup and fallback logic". 
  Retrieve all recorded decision entries and rationales.
  ```

---

### 19. `query_knowledge_base`
* **Description**: Performs semantic vector search over the local Chroma vector database for company docs, policies, and codemaps.
* **Parameters**:
  * `query` (`string`, required): Natural language search query.
* **Trigger Keywords**: `knowledge base`, `query kb`, `vector search`, `search docs`
* **Full-Potential Prompt**:
  ```markdown
  Use query_knowledge_base to search for "token budget advisor settings and temperature rules". 
  Return top matching document excerpts.
  ```

---

### 20. `read_file_tool`
* **Description**: Reads content from a local file. Supports text files and line range selection.
* **Parameters**:
  * `file_path` (`string`, required): File path to read.
* **Trigger Keywords**: `read file`, `view file`, `cat`, `show file content`
* **Full-Potential Prompt**:
  ```markdown
  Use read_file_tool to read file_path="orchestrator/agents.py". 
  Retrieve the file content and inspect agent definitions.
  ```

---

### 21. `record_continuous_learning_tool`
* **Description**: Records reusable architectural lessons, prompt patterns, or failure lessons into continuous learning memory.
* **Parameters**:
  * `lesson_or_pattern` (`string`, required): Lesson, pattern, or rule discovered.
  * `component` (`string`, required): Associated system component or module name.
* **Trigger Keywords**: `record learning`, `continuous learning`, `log lesson`
* **Full-Potential Prompt**:
  ```markdown
  Execute record_continuous_learning_tool with:
  - lesson_or_pattern="Always use Selector instead of Adaptor when parsing HTML with Scrapling 0.4.x"
  - component="orchestrator/tools.py"
  ```

---

### 22. `record_decision_tool`
* **Description**: Records an architectural decision, rationale, and scope into gstack decision memory.
* **Parameters**:
  * `decision` (`string`, required): Decision title or description.
  * `rationale` (`string`, required): Reasoning and trade-offs.
  * `scope` (`string`, optional): Affected module or project scope.
* **Trigger Keywords**: `record decision`, `log decision`, `decision memory`
* **Full-Potential Prompt**:
  ```markdown
  Run record_decision_tool with:
  - decision="Adopt Scrapling + Patchright for stealth web scraping"
  - rationale="Bypasses client-side anti-bot challenges and TLS fingerprinting without relying on third-party SaaS"
  - scope="orchestrator/tools.py"
  ```

---

### 23. `redact_sensitive_content_tool`
* **Description**: Detects and redacts sensitive data (API keys, JWT tokens, AWS secrets, passwords, credit cards, emails, IP addresses) from text.
* **Parameters**:
  * `text` (`string`, required): Text containing sensitive data.
* **Trigger Keywords**: `redact`, `redact text`, `mask secrets`, `sanitize output`
* **Full-Potential Prompt**:
  ```markdown
  Run redact_sensitive_content_tool on text="API_KEY=sk-proj-998877665544332211 and JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.secret". 
  Sanitize all sensitive tokens and return redacted output.
  ```

---

### 24. `scan_dependencies_tool`
* **Description**: Scans package dependency manifests (`pyproject.toml`, `package.json`, `requirements.txt`) for outdated or vulnerable dependencies.
* **Parameters**:
  * `file_path` (`string`, required): Path to manifest file.
* **Trigger Keywords**: `scan dependencies`, `audit packages`, `check cve`, `vulnerable dependencies`
* **Full-Potential Prompt**:
  ```markdown
  Execute scan_dependencies_tool for file_path="pyproject.toml". 
  Check all listed libraries against security databases for known CVEs and outdated package versions.
  ```

---

### 25. `scrapling_adaptor_parse_tool`
* **Description**: Parses raw HTML strings adaptively using Scrapling's `Selector` engine with CSS or XPath selectors.
* **Parameters**:
  * `html_content` (`string`, required): Raw HTML string.
  * `selector` (`string`, required): CSS or XPath query.
  * `selector_type` (`string`, optional): `"css"` or `"xpath"` (defaults to `"css"`).
* **Trigger Keywords**: `parse html`, `scrapling parse`, `css selector`, `xpath parse`
* **Full-Potential Prompt**:
  ```markdown
  Run scrapling_adaptor_parse_tool with:
  - html_content="<div class='product'><h1>Laptop Pro</h1><span class='price'>$999</span></div>"
  - selector=".price"
  - selector_type="css"
  Extract matching text elements.
  ```

---

### 26. `scrapling_stealth_fetch_tool`
* **Description**: Uses Scrapling's `StealthyFetcher` (Patchright + Chromium engine with TLS fingerprint spoofing) to render dynamic JavaScript pages and bypass anti-bot challenges.
* **Parameters**:
  * `url` (`string`, required): Target URL to fetch.
  * `css_selector` (`string`, optional): CSS selector to filter page elements.
* **Trigger Keywords**: `stealth fetch`, `scrapling stealth`, `bypass anti bot`, `render js page`
* **Full-Potential Prompt**:
  ```markdown
  Use scrapling_stealth_fetch_tool with:
  - url="https://example.com/sponsors"
  - css_selector="h1, .sponsor-card, footer"
  Render the dynamic JavaScript page, bypass client anti-bot checks, and extract elements matching the selector.
  ```

---

### 27. `silent_failure_scan_tool`
* **Description**: Audits code for swallowed exceptions, bare `except:`, empty catch blocks, bad fallback defaults, and unhandled errors.
* **Parameters**:
  * `target_directory` (`string`, optional): Directory path to scan.
* **Trigger Keywords**: `silent failure`, `swallowed exceptions`, `audit catch blocks`, `bad fallbacks`
* **Full-Potential Prompt**:
  ```markdown
  Run silent_failure_scan_tool for target_directory="orchestrator". 
  Identify all lines with swallowed exceptions, lost stack traces, or silent error suppressions.
  ```

---

### 28. `threat_intel_lookup_tool`
* **Description**: Queries threat intelligence feeds for malicious IP addresses, botnet nodes, or known attack vectors.
* **Parameters**:
  * `ip_address` (`string`, required): Target IP address to check.
* **Trigger Keywords**: `threat intel`, `malicious ip`, `ip threat`, `botnet check`
* **Full-Potential Prompt**:
  ```markdown
  Execute threat_intel_lookup_tool for ip_address="185.220.101.5". 
  Check threat intelligence databases for malicious activity reports and risk scores.
  ```

---

### 29. `token_budget_advisor_tool`
* **Description**: Calculates LLM token overhead, estimates cost per execution, and advises on prompt depth settings.
* **Parameters**:
  * `prompt_text` (`string`, required): Prompt text to evaluate.
  * `desired_depth` (`string`, optional): Depth setting (e.g. `"25% Essential"`, `"50% Moderate"`, `"100% Exhaustive"`).
* **Trigger Keywords**: `token budget`, `calculate tokens`, `token cost`, `response depth`
* **Full-Potential Prompt**:
  ```markdown
  Use token_budget_advisor_tool for prompt_text="Audit whole codebase and refactor database queries" with desired_depth="50% Moderate (Balanced)". 
  Calculate estimated token count and cost breakdown across Gemini, Groq, and OpenAI backends.
  ```

---

### 30. `unfreeze_file_path_tool`
* **Description**: Unlocks a previously frozen file path, allowing agents to edit or overwrite it again.
* **Parameters**:
  * `filepath` (`string`, required): File path to unfreeze.
* **Trigger Keywords**: `unfreeze`, `unfreeze file`, `unlock path`
* **Full-Potential Prompt**:
  ```markdown
  Execute unfreeze_file_path_tool for filepath="orchestrator/states.py". 
  Unlock file path permissions.
  ```

---

### 31. `verification_loop_tool`
* **Description**: Runs project verification checks (syntax validation, import resolution, linting, build sanity).
* **Parameters**:
  * `project_root` (`string`, optional): Root directory path.
* **Trigger Keywords**: `verification loop`, `verify build`, `sanity check`, `lint verify`
* **Full-Potential Prompt**:
  ```markdown
  Run verification_loop_tool for project_root=".". 
  Validate syntax, import resolution, and build sanity across Python and JavaScript files.
  ```

---

### 32. `write_file_tool`
* **Description**: Writes text or code content to a specified local file path.
* **Parameters**:
  * `file_path` (`string`, required): Target file path.
  * `content` (`string`, required): Text/code content to write.
* **Trigger Keywords**: `write file`, `create file`, `save code`, `write code`
* **Full-Potential Prompt**:
  ```markdown
  Use write_file_tool with:
  - file_path="src/helpers.py"
  - content="def calculate_total(prices):
    return sum(prices)
"
  Write content to local file.
  ```

---

## 👥 Agent Personas & Skill Prompt Catalogs

### Agency Agents Engineering Suite (58 Roles)
Each role has a dedicated skill prompt loaded from `orchestrator/agency_skills.py`:

* `backend-architect` — System architecture, schema design, microservices, resilience.
* `ai-engineer` — ML models, MLOps, HuggingFace, PyTorch, production serving.
* `rag-pipeline-engineer` — RAG, vector DBs (Chroma, FAISS), chunking, semantic retrieval.
* `database-optimizer` — SQL tuning, indexing, connection pooling, slow logs.
* `devops-automator` — CI/CD, Kubernetes, Terraform, Docker.
* `rust-specialist` — High-performance Rust refactoring & zero-cost abstractions.
* `solidity-engineer` — Smart contracts, reentrancy defense, gas optimization.
* `api-platform-engineer` — OpenAPI/gRPC design, rate limits, SDK generation.
* `sre-incident-commander` — Incident response, post-mortems, SLO/SLA management.
* `prompt-engineer` — System prompt optimization, few-shot evaluation, JSON outputs.
* `finops-engineer` — Cloud cost optimization & token budget management.
* `codebase-onboarding` — Codemaps, entry point tracing, developer onboarding.
*(+ 46 additional roles visible in UI)*

---

## 🚀 Prompt Engineering Cookbook

### Example 1: Full-Stack Web Scraping & Parsing Pipeline
```markdown
Search the web for top Chennai tech sponsors, use scrapling_stealth_fetch_tool 
to load their sponsor page, use scrapling_adaptor_parse_tool with selector='.sponsor-card' 
to extract company names and phone numbers, and save the result using write_file_tool to output/sponsors.md.
```

### Example 2: Security Audit & Automated Secret Redaction
```markdown
Run cso_security_scanner_tool on orchestrator/api.py. Identify any OWASP vulnerabilities, 
pass the findings through redact_sensitive_content_tool to mask API keys, and log the 
architectural decision using record_decision_tool.
```

### Example 3: Full Feature Architecture & Technical Spec
```markdown
Run /backend-architect and /code-architect to design a real-time event streaming engine. 
Use generate_ascii_architecture_tool to render the data flow diagram, and create_technical_spec_tool 
to generate the executable /spec document.
```
