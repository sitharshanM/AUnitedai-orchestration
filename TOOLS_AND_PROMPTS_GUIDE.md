# 🛠️ AUnitedAI Multi-Agent System: Tools & Prompts Master Guide

Welcome to the comprehensive master guide for all tools, worker agents, and skill prompts in the **AUnitedAI Multi-Agent Orchestrator**. 

This document serves as an exhaustive reference manual designed to help users, prompt engineers, and developers unlock **100% potential** of every single tool, agent, and workflow in the system.

---

## 📋 Table of Contents
1. [Overview & Dynamic AI Tool Selection](#-overview--dynamic-ai-tool-selection)
2. [Individual Tool Master Directory (32 Tools with Full-Potential Prompts)](#-individual-tool-master-directory)
   - [Web Fetching & Stealth Scraping Tools (4 Tools)](#1-web-fetching--stealth-scraping-tools)
   - [File & Code Management Tools (5 Tools)](#2-file--code-management-tools)
   - [Security, Audit & Redaction Tools (8 Tools)](#3-security-audit--redaction-tools)
   - [Architecture, Memory & Documentation Tools (7 Tools)](#4-architecture-memory--documentation-tools)
   - [Quality, Performance & Verification Tools (8 Tools)](#5-quality-performance--verification-tools)
3. [Agent & Skill Roles Catalog (245+ Active Registered Skills)](#-agent--skill-roles-catalog)
4. [Master Prompt Engineering Cookbook](#-master-prompt-engineering-cookbook)

---

## 🧠 Overview & Dynamic AI Tool Selection

The orchestrator utilizes **Dynamic AI Tool Selection**. You do not need to manually bind tools; the Orchestrator AI reads your prompt instructions and dynamically attaches the required tools from the `GLOBAL_TOOL_REGISTRY` to the execution state.

### How to Trigger Specific Tools via Prompts:
* **Web & Scraping**: Include terms like `search`, `web`, `url`, `scrape`, `stealth fetch`, `parse html`.
* **File Operations**: Include terms like `file`, `code`, `write`, `read`, `patch`, `create`, `refactor`.
* **Security & Vulnerabilities**: Include terms like `sec`, `audit`, `owasp`, `cso`, `scan`, `threat`, `redact`.
* **Architecture & Specs**: Include terms like `arch`, `spec`, `diataxis`, `ascii flow`, `gstack`.
* **Performance & Canary**: Include terms like `perf`, `benchmark`, `canary`, `token budget`, `silent failure`.

---

## 🧰 Individual Tool Master Directory

Each entry below includes the **Optimal High-Potential Prompt** specifically engineered to trigger and extract 100% maximum capability from that tool.

---

### 1. Web Fetching & Stealth Scraping Tools

#### 1. `scrapling_stealth_fetch_tool`
* **Description**: Uses Scrapling's `StealthyFetcher` (Patchright + Chromium headless browser engine with TLS fingerprint spoofing) to render dynamic JavaScript pages, bypass Cloudflare/anti-bot challenges, and extract targeted CSS elements.
* **Trigger Keywords**: `stealth fetch`, `scrapling stealth`, `render js`, `bypass anti-bot`, `scrape dynamic page`
* **Optimal Prompt Template**:
  ```markdown
  Use scrapling_stealth_fetch_tool to render the dynamic JavaScript webpage at "https://example.com/sponsors". 
  Bypass client-side anti-bot protection and extract elements matching CSS selector ".sponsor-card". 
  Return the sponsor names, websites, and published contact phone numbers.
  ```

#### 2. `fetch_webpage_tool`
* **Description**: Fetches clean text content from static or basic web pages using Scrapling's `Fetcher` engine (with automatic fallback to `requests` + `BeautifulSoup`).
* **Trigger Keywords**: `fetch webpage`, `read site`, `scrape url`, `read web page`
* **Optimal Prompt Template**:
  ```markdown
  Use fetch_webpage_tool to download and clean the text content of "https://docs.python.org/3/whatsnew/3.12.html". 
  Summarize the key deprecations and performance improvements in bullet points.
  ```

#### 3. `scrapling_adaptor_parse_tool`
* **Description**: Parses raw HTML strings adaptively using Scrapling's `Selector` engine using CSS selectors or XPath queries.
* **Trigger Keywords**: `parse html`, `adaptor parse`, `xpath query`, `css parse`
* **Optimal Prompt Template**:
  ```markdown
  Take the raw HTML content from the previous task and use scrapling_adaptor_parse_tool 
  with selector_type="xpath" and selector="//div[@class='pricing-table']//span/text()" 
  to extract all tier pricing values.
  ```

#### 4. `duckduckgo_search_results`
* **Description**: Performs live DuckDuckGo web searches and returns structured titles, snippets, and target URLs.
* **Trigger Keywords**: `search`, `duckduckgo`, `search web`, `find online`, `google search`
* **Optimal Prompt Template**:
  ```markdown
  Use duckduckgo_search_results to search for "Chennai tech conference 2026 sponsors list contact emails". 
  Extract the top 3 target website URLs for further scraping.
  ```

---

### 2. File & Code Management Tools

#### 5. `read_file_tool`
* **Description**: Reads file contents from the workspace with line-by-line inspection and automatic encoding detection.
* **Trigger Keywords**: `read file`, `inspect file`, `view code`, `examine file`
* **Optimal Prompt Template**:
  ```markdown
  Use read_file_tool to inspect "orchestrator/agents.py". Examine lines 250 to 350 
  and explain how tool bindings are constructed for worker agents.
  ```

#### 6. `write_file_tool`
* **Description**: Creates new files or overwrites existing files safely on the filesystem.
* **Trigger Keywords**: `write file`, `create file`, `save code`, `update file`
* **Optimal Prompt Template**:
  ```markdown
  Use write_file_tool to create a new module "src/validators.py" containing 
  input validation functions for email, phone number, and JWT token signatures with full docstrings.
  ```

#### 7. `list_directory_tool`
* **Description**: Lists files, subdirectories, file sizes, and directory trees recursively.
* **Trigger Keywords**: `list directory`, `ls`, `show files`, `explore folder`
* **Optimal Prompt Template**:
  ```markdown
  Use list_directory_tool to explore "orchestrator/". List all Python files, their sizes, 
  and identify any untracked or scratch scripts.
  ```

#### 8. `freeze_file_path_tool`
* **Description**: Locks critical file paths in gstack memory to prevent unauthorized worker edits or accidental overwrites.
* **Trigger Keywords**: `freeze file`, `lock path`, `protect file`
* **Optimal Prompt Template**:
  ```markdown
  Use freeze_file_path_tool to lock "orchestrator/states.py" and "orchestrator/config.py" 
  so worker agents cannot modify graph state schemas during refactoring.
  ```

#### 9. `unfreeze_file_path_tool`
* **Description**: Unlocks previously frozen file paths after refactoring or approval.
* **Trigger Keywords**: `unfreeze file`, `unlock path`
* **Optimal Prompt Template**:
  ```markdown
  Use unfreeze_file_path_tool to release the edit lock on "orchestrator/states.py".
  ```

---

### 3. Security, Audit & Redaction Tools

#### 10. `cso_security_scanner_tool`
* **Description**: Audits source code for OWASP Top 10 vulnerabilities (SQLi, XSS, SSRF, JWT flaws, RCE, IDOR, path traversal, hardcoded secrets).
* **Trigger Keywords**: `cso scan`, `security audit`, `owasp scan`, `check vulnerabilities`
* **Optimal Prompt Template**:
  ```markdown
  Use cso_security_scanner_tool to audit "orchestrator/api.py". Inspect all API endpoints 
  for OWASP Top 10 vulnerabilities, unauthenticated routes, and input validation gaps. 
  Report findings with CWE IDs and exact code remediations.
  ```

#### 11. `scan_dependencies_tool`
* **Description**: Scans package manifests (`pyproject.toml`, `package.json`, `requirements.txt`) for known CVE security vulnerabilities and yanked packages.
* **Trigger Keywords**: `scan dependencies`, `audit packages`, `cve check`, `dependency vulnerabilities`
* **Optimal Prompt Template**:
  ```markdown
  Use scan_dependencies_tool to audit "pyproject.toml" and "package.json". 
  Check all direct and indirect package dependencies for known CVE security advisories and outdated versions.
  ```

#### 12. `redact_sensitive_content_tool`
* **Description**: Automatically detects and redacts secrets (API keys, JWT tokens, AWS credentials, passwords, credit cards, emails, IP addresses).
* **Trigger Keywords**: `redact`, `redact secrets`, `sanitize output`, `mask sensitive data`
* **Optimal Prompt Template**:
  ```markdown
  Use redact_sensitive_content_tool to sanitize the raw execution logs. 
  Mask all OpenAI keys, JWT tokens, database connection strings, and IP addresses before storing.
  ```

#### 13. `geoip_lookup_tool`
* **Description**: Queries Geographic IP database for country, city, ISP, ASN, and risk region of IP addresses.
* **Trigger Keywords**: `geoip`, `ip lookup`, `ip location`
* **Optimal Prompt Template**:
  ```markdown
  Use geoip_lookup_tool to analyze IP address "185.220.101.5". Report country, city, 
  hosting provider, and proxy status.
  ```

#### 14. `threat_intel_lookup_tool`
* **Description**: Cross-references IP addresses and domain names against malicious threat intelligence databases (botnet, TOR exit node, malware C2, phishing).
* **Trigger Keywords**: `threat intel`, `malicious ip`, `threat lookup`
* **Optimal Prompt Template**:
  ```markdown
  Use threat_intel_lookup_tool to check domain "malicious-phishing-site.com" and IP "45.154.255.8" 
  against threat intelligence feeds.
  ```

#### 15. `neural_threat_score_tool`
* **Description**: Runs neural network inference to calculate threat risk scores (0.0 to 1.0) for network traffic patterns and API payloads.
* **Trigger Keywords**: `neural threat`, `score threat`, `ai risk score`
* **Optimal Prompt Template**:
  ```markdown
  Use neural_threat_score_tool to evaluate a 500 req/sec spike originating from ASN 14061 
  with user-agent "python-requests/2.31.0". Calculate threat probability score.
  ```

#### 16. `domain_category_tool`
* **Description**: Classifies web domains by category (e.g. Finance, E-commerce, Tech, Suspicious/Phishing) and assesses domain risk.
* **Trigger Keywords**: `domain category`, `classify domain`
* **Optimal Prompt Template**:
  ```markdown
  Use domain_category_tool to classify domain "auth-verify-bank-update.net". 
  Determine categorization and risk level.
  ```

#### 17. `fetch_github_repo_tool`
* **Description**: Fetches repository structure, file trees, README, and source code from public GitHub repositories.
* **Trigger Keywords**: `github repo`, `fetch github`, `clone repo info`
* **Optimal Prompt Template**:
  ```markdown
  Use fetch_github_repo_tool to inspect "https://github.com/msitarzewski/agency-agents". 
  Extract the directory layout and main README documentation.
  ```

---

### 4. Architecture, Memory & Documentation Tools

#### 18. `create_technical_spec_tool`
* **Description**: Authors a complete, executable technical specification document (/spec) with architectural scope, API endpoints, state machine transitions, and quality gates.
* **Trigger Keywords**: `create spec`, `technical spec`, `author spec`, `make spec`
* **Optimal Prompt Template**:
  ```markdown
  Use create_technical_spec_tool to author a technical specification for "OAuth2 Single Sign-On System". 
  Define core components, API request/response schemas, failure modes, and acceptance criteria.
  ```

#### 19. `generate_ascii_architecture_tool`
* **Description**: Generates clean ASCII data flow diagrams, system architecture block charts, and state machine transitions.
* **Trigger Keywords**: `ascii flow`, `ascii diagram`, `architecture chart`, `draw ascii`
* **Optimal Prompt Template**:
  ```markdown
  Use generate_ascii_architecture_tool to draw an ASCII system architecture diagram for:
  User Browser -> Vite React Frontend -> FastAPI Gateway -> LangGraph Orchestrator -> Scrapling Engine / SQLite DB.
  ```

#### 20. `generate_diataxis_docs_tool`
* **Description**: Generates documentation following the 4 Diataxis pillars: Tutorial, How-To Guide, Technical Reference, or Explanation.
* **Trigger Keywords**: `diataxis`, `generate docs`, `author tutorial`, `how-to guide`
* **Optimal Prompt Template**:
  ```markdown
  Use generate_diataxis_docs_tool with doc_type="how-to" to write a guide titled 
  "How to Register a New Worker Agent in AUnitedAI Multi-Agent System". Include step-by-step code snippets.
  ```

#### 21. `query_knowledge_base`
* **Description**: Performs semantic vector search over local Chroma vector database for internal documentation, guidelines, and codemaps.
* **Trigger Keywords**: `knowledge base`, `query kb`, `search docs`
* **Optimal Prompt Template**:
  ```markdown
  Use query_knowledge_base to search for "token budget advisor settings and temperature rules". 
  Return relevant document excerpts.
  ```

#### 22. `record_decision_tool`
* **Description**: Records architectural decisions, trade-offs, and rationale into gstack decision memory.
* **Trigger Keywords**: `record decision`, `log decision`, `decision memory`
* **Optimal Prompt Template**:
  ```markdown
  Use record_decision_tool to log decision DEC-042: "Adopt Scrapling with StealthyFetcher + Patchright Chromium engine for web scraping to guarantee anti-bot bypass."
  ```

#### 23. `query_gstack_memory_tool`
* **Description**: Queries recorded architectural decisions and rationale from gstack decision memory.
* **Trigger Keywords**: `query memory`, `gstack memory`, `view decisions`
* **Optimal Prompt Template**:
  ```markdown
  Use query_gstack_memory_tool to search for all past architectural decisions regarding database choices and scrapers.
  ```

#### 24. `investigate_root_cause_tool`
* **Description**: Applies the "Iron Law of Root-Cause Debugging" to trace data flows, form hypotheses, and isolate bug root causes before editing code.
* **Trigger Keywords**: `investigate`, `root cause`, `iron law`, `debug bug`
* **Optimal Prompt Template**:
  ```markdown
  Use investigate_root_cause_tool to analyze why scrapling_stealth_fetch_tool threw "ImportError: No module named patchright". 
  Trace dependency import paths and provide the exact fix hypothesis.
  ```

---

### 5. Quality, Performance & Verification Tools

#### 25. `silent_failure_scan_tool`
* **Description**: Scans codebase for swallowed exceptions, bare `except:`, empty catch blocks, bad fallback defaults, and missing error propagation.
* **Trigger Keywords**: `silent failure`, `swallowed exception`, `catch audit`, `bare except`
* **Optimal Prompt Template**:
  ```markdown
  Use silent_failure_scan_tool to audit "orchestrator/tools.py" and "orchestrator/agents.py". 
  Flag all bare except blocks, silent try-pass statements, and unlogged exceptions.
  ```

#### 26. `build_error_resolver` (via `verification_loop_tool`)
* **Description**: Diagnoses compilation errors, syntax errors, type mismatches, and broken import modules.
* **Trigger Keywords**: `build resolve`, `fix build`, `compilation error`, `syntax error`
* **Optimal Prompt Template**:
  ```markdown
  Use build_error_resolver and verification_loop_tool to diagnose Python syntax errors in "orchestrator/agency_skills.py". 
  Identify the exact line number and apply a drop-in replacement fix.
  ```

#### 27. `canary_benchmark_tool`
* **Description**: Executes performance benchmarking, Core Web Vitals checks, latency profiling, and throughput monitoring.
* **Trigger Keywords**: `canary`, `benchmark`, `perf test`, `latency test`
* **Optimal Prompt Template**:
  ```markdown
  Use canary_benchmark_tool to run latency benchmarks on the FastAPI server endpoints. 
  Report p50, p95, and p99 response times.
  ```

#### 28. `token_budget_advisor_tool`
* **Description**: Calculates LLM token budget consumption, prompt overhead, and suggests compression or depth adjustments (25% Essential, 50% Moderate, 100% Exhaustive).
* **Trigger Keywords**: `token budget`, `token advisor`, `cost estimate`
* **Optimal Prompt Template**:
  ```markdown
  Use token_budget_advisor_tool to calculate the token cost of sending 50,000 scraped HTML rows to LLM. 
  Suggest a semantic compression approach to reduce token usage by 90%.
  ```

#### 29. `devex_audit_tool`
* **Description**: Audits Developer Experience (DX), onboarding friction points, setup script failures, and Time-To-Hello-World (TTHW).
* **Trigger Keywords**: `devex audit`, `dx audit`, `tthw`
* **Optimal Prompt Template**:
  ```markdown
  Use devex_audit_tool to audit the repository onboarding process. Evaluate README instructions, 
  uv environment setup, and script execution friction points.
  ```

#### 30. `autoplan_pipeline_tool`
* **Description**: Executes the automated Review Pipeline chaining CEO Strategic Review -> Senior Designer Review -> Eng Manager Review.
* **Trigger Keywords**: `autoplan`, `review pipeline`, `auto plan`
* **Optimal Prompt Template**:
  ```markdown
  Use autoplan_pipeline_tool to run an automated review pipeline for "AI-Classroom Web Dashboard". 
  Evaluate 10-star product vision, UI design quality score (0-10), and engineering architecture locks.
  ```

#### 31. `verification_loop_tool`
* **Description**: Executes continuous verification loops ensuring code modifications build cleanly, pass lint checks, and maintain contract integrity.
* **Trigger Keywords**: `verify loop`, `verification check`, `test verify`
* **Optimal Prompt Template**:
  ```markdown
  Use verification_loop_tool to verify that all Python files in "orchestrator/" import without syntax or runtime errors.
  ```

#### 32. `e2e_test_verifier_tool`
* **Description**: Runs integration test suites, end-to-end user flow validations, and unit tests with structured pass/fail metrics.
* **Trigger Keywords**: `e2e test`, `e2e runner`, `run integration tests`
* **Optimal Prompt Template**:
  ```markdown
  Use e2e_test_verifier_tool to execute end-to-end user flow tests for the web scraping pipeline. 
  Verify fetch, stealth fetch, and parse outputs with pass/fail reports.
  ```

---

## 👥 Agent & Skill Roles Catalog (245+ Skills)

### 1. Agency Agents Engineering Suite (58 Roles)
*Extracted from `msitarzewski/agency-agents/engineering`*

Each role can be invoked directly in your prompt using `/role_name` or `engineering_role_name`:

* `/backend-architect` — Scalable system design, database schemas, microservices, API contracts.
* `/ai-engineer` — Machine learning models, MLOps, production model serving.
* `/rag-pipeline-engineer` — Vector databases (Chroma, FAISS), chunking, semantic retrieval.
* `/database-optimizer` — SQL query tuning, index optimization, connection pooling.
* `/devops-automator` — CI/CD pipelines, Kubernetes, Terraform, Docker containerization.
* `/rust-specialist` — High-performance Rust refactoring, memory safety, zero-cost abstractions.
* `/solidity-engineer` — Smart contract development, reentrancy guards, gas optimization.
* `/api-platform-engineer` — Contract-first OpenAPI/gRPC design, rate limiting, developer portal DX.
* `/sre-incident-commander` — Incident response, root cause analysis, SLO/SLA management.
* `/prompt-engineer` — LLM system prompt optimization, few-shot evaluation, JSON output parsing.
* `/finops-engineer` — Cloud cost optimization, LLM token budget management.
* `/codebase-onboarding` — Architectural codemaps, entry point flowcharts, developer onboarding.
* *(+ 46 additional roles registered in `orchestrator/agency_skills.py`)*

---

## 🚀 Master Prompt Engineering Cookbook

### Example 1: Autonomous Web Scraping Pipeline
```markdown
Search the web for top Chennai tech sponsors, use scrapling_stealth_fetch_tool 
to load their sponsor directory, use scrapling_adaptor_parse_tool to extract sponsor cards, 
and output a clean CSV table with company names, websites, and phone numbers.
```

### Example 2: Complete Architecture & Spec Generation
```markdown
Run /backend-architect and /code-architect to design a high-throughput 
microservice architecture for a real-time analytics engine. Use generate_ascii_architecture_tool 
to draw the data flow diagram and create_technical_spec_tool to write the /spec document.
```

### Example 3: Full Security Audit & Secret Redaction
```markdown
Run /cso and /silent-failure-scan to audit the authentication module. 
Use cso_security_scanner_tool to find OWASP Top 10 bugs, scan_dependencies_tool to check packages, 
and redact_sensitive_content_tool to mask all secrets in the final report.
```
