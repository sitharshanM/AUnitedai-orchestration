# 🛠️ AUnitedAI Multi-Agent System: Tools & Prompts Master Guide

Welcome to the comprehensive master guide for all tools, worker agents, and skill prompts in the **AUnitedAI Multi-Agent Orchestrator**. 

This document serves as an exhaustive reference manual designed to help users, prompt engineers, and developers unlock **100% potential** of every tool, agent, and workflow in the repository.

---

## 📋 Table of Contents
1. [Overview & Dynamic AI Tool Selection](#-overview--dynamic-ai-tool-selection)
2. [Complete Tools Catalog (30+ Tools)](#-complete-tools-catalog)
   - [Web Fetching & Stealth Scraping Tools](#1-web-fetching--stealth-scraping-tools)
   - [File & Code Management Tools](#2-file--code-management-tools)
   - [Security, Audit & Redaction Tools](#3-security-audit--redaction-tools)
   - [Architecture & Documentation Tools](#4-architecture--documentation-tools)
   - [Quality, Performance & Testing Tools](#5-quality-performance--testing-tools)
3. [Agent & Skill Roles Catalog (245+ Skills)](#-agent--skill-roles-catalog)
   - [Agency Agents Engineering Suite (58 Roles)](#1-agency-agents-engineering-suite-58-roles)
   - [ECC Pipeline & Plugin Skills (15 Roles)](#2-ecc-pipeline--plugin-skills-15-roles)
   - [gstack Review Workflows & Strix Pentest Suite (35+ Roles)](#3-gstack-review-workflows--strix-pentest-suite)
4. [Prompt Engineering Cookbook (Unlocking Full Potential)](#-prompt-engineering-cookbook)

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

## 🧰 Complete Tools Catalog

### 1. Web Fetching & Stealth Scraping Tools

#### `fetch_webpage_tool`
* **Description**: Fetches clean text content from a web page using Scrapling (with fallback to `requests` + `BeautifulSoup`).
* **Parameters**: `url` (string)
* **Prompt Trigger**: *"Fetch the content of https://example.com and summarize it."*

#### `scrapling_stealth_fetch_tool`
* **Description**: Uses Scrapling's `StealthyFetcher` (Patchright + Chromium engine with TLS fingerprint spoofing) to render dynamic JavaScript pages and bypass client-side anti-bot checks.
* **Parameters**: `url` (string), `css_selector` (optional string)
* **Prompt Trigger**: *"Use stealth scraper to render https://example.com/sponsors and extract elements matching CSS selector '.sponsor-card'."*

#### `scrapling_adaptor_parse_tool`
* **Description**: Parses raw HTML content adaptively using Scrapling's `Selector` engine with CSS or XPath expressions.
* **Parameters**: `html_content` (string), `selector` (string), `selector_type` ("css" or "xpath")
* **Prompt Trigger**: *"Parse the HTML content using XPath '//h1/text()' to extract headings."*

#### `duckduckgo_search_results`
* **Description**: Performs live DuckDuckGo web searches and returns structured titles, snippets, and target URLs.
* **Parameters**: `query` (string)
* **Prompt Trigger**: *"Search the web for recent LLM benchmarking research papers."*

---

### 2. File & Code Management Tools

#### `read_file_tool`
* **Description**: Safely reads the text content of any local file within the workspace.
* **Parameters**: `file_path` (string)
* **Prompt Trigger**: *"Read file orchestrator/agents.py and explain lines 100-150."*

#### `write_file_tool`
* **Description**: Writes or overwrites code/text to a specified local file path.
* **Parameters**: `file_path` (string), `content` (string)
* **Prompt Trigger**: *"Write a new Python file src/utils.py with helper functions."*

#### `list_directory_tool`
* **Description**: Lists files and subdirectories at a given directory path.
* **Parameters**: `dir_path` (optional string)
* **Prompt Trigger**: *"List all files in the orchestrator directory."*

#### `freeze_file_path_tool` & `unfreeze_file_path_tool`
* **Description**: Freezes critical file paths in memory to prevent accidental overwrites or unfreezes them.
* **Parameters**: `file_path` (string)
* **Prompt Trigger**: *"Freeze file orchestrator/states.py to protect it during refactoring."*

---

### 3. Security, Audit & Redaction Tools

#### `cso_security_scanner_tool`
* **Description**: Scans code for OWASP Top 10 vulnerabilities, hardcoded API keys, JWT flaws, SQLi, and SSRF.
* **Parameters**: `code_snippet` (string), `file_name` (optional string)
* **Prompt Trigger**: *"Run CSO security scanner on authentication middleware."*

#### `scan_dependencies_tool`
* **Description**: Audits project dependencies (e.g. `pyproject.toml`, `package.json`, `requirements.txt`) for known CVE vulnerabilities.
* **Parameters**: `manifest_content` (string)
* **Prompt Trigger**: *"Scan pyproject.toml dependencies for security vulnerabilities."*

#### `redact_sensitive_content_tool`
* **Description**: Automatically detects and redacts secrets (API keys, JWT tokens, private keys, AWS secrets, passwords, SSNs, emails, IP addresses).
* **Parameters**: `text` (string)
* **Prompt Trigger**: *"Redact all sensitive secrets and API keys from this log output."*

#### `threat_intel_lookup_tool` & `geoip_lookup_tool` & `neural_threat_score_tool` & `domain_category_tool`
* **Description**: Network security suite for IP geographic lookup, malicious IP threat intelligence matching, neural network threat scoring, and domain classification.
* **Prompt Trigger**: *"Lookup threat intelligence for IP 192.168.1.1 and calculate neural threat score."*

---

### 4. Architecture & Documentation Tools

#### `create_technical_spec_tool`
* **Description**: Generates an executable technical specification document (/spec) with quality gates, boundary conditions, and acceptance criteria.
* **Parameters**: `feature_name` (string), `requirements` (string)

#### `generate_ascii_architecture_tool`
* **Description**: Generates ASCII data flow diagrams, system architecture block diagrams, and state machine charts.
* **Parameters**: `system_name` (string), `components` (list of strings)

#### `generate_diataxis_docs_tool`
* **Description**: Authors documentation following the 4 Diataxis pillars: Tutorial, How-To Guide, Technical Reference, Explanation.
* **Parameters**: `doc_type` ("tutorial" | "how-to" | "reference" | "explanation"), `topic` (string)

#### `query_knowledge_base`
* **Description**: Performs semantic vector search over the local Chroma vector database for project documentation, policies, and codemaps.
* **Parameters**: `query` (string)

---

### 5. Quality, Performance & Testing Tools

#### `silent_failure_scan_tool`
* **Description**: Audits codebase for swallowed exceptions, bare `except:`, empty catch blocks, bad fallbacks, and lost stack traces.

#### `verification_loop_tool` & `e2e_test_verifier_tool`
* **Description**: Runs verification checks, test execution loops, and end-to-end regression verifications.

#### `canary_benchmark_tool` & `token_budget_advisor_tool`
* **Description**: Runs performance benchmarking, Core Web Vitals checks, and calculates LLM token budget consumption.

#### `record_decision_tool` & `query_gstack_memory_tool`
* **Description**: Logs architectural decisions to gstack decision memory and retrieves decision logs.

---

## 👥 Agent & Skill Roles Catalog

### 1. Agency Agents Engineering Suite (58 Roles)
*Extracted from `msitarzewski/agency-agents/engineering`*

| Role Name | Prompt Skill Trigger | Focus Area |
| :--- | :--- | :--- |
| `backend-architect` | `/backend-architect` | Scalable system design, database schemas, microservices, API contracts |
| `ai-engineer` | `/ai-engineer` | Machine learning models, MLOps, production model serving, TensorFlow/PyTorch |
| `rag-pipeline-engineer` | `/rag-pipeline-engineer` | Vector databases (Chroma, FAISS, Pinecone), embeddings, chunking, semantic search |
| `database-optimizer` | `/database-optimizer` | SQL query tuning, index optimization, connection pooling, slow log analysis |
| `devops-automator` | `/devops-automator` | CI/CD pipelines, Kubernetes, Terraform, Docker containerization |
| `rust-specialist` | `/rust-specialist` | High-performance Rust refactoring, memory safety, zero-cost abstractions |
| `solidity-engineer` | `/solidity-engineer` | Smart contract development, reentrancy guards, gas optimization |
| `api-platform-engineer` | `/api-platform-engineer` | Contract-first OpenAPI/gRPC design, rate limiting, developer portal DX |
| `sre-incident-commander` | `/sre-incident-commander` | Incident response, root cause analysis, SLO/SLA management, post-mortems |
| `prompt-engineer` | `/prompt-engineer` | LLM system prompt optimization, few-shot evaluation, JSON output parsing |
| `finops-engineer` | `/finops-engineer` | Cloud cost optimization, LLM token budget management, resource rightsizing |
| `codebase-onboarding` | `/codebase-onboarding` | Architectural codemaps, entry point flowcharts, developer onboarding |
| *(+ 46 additional roles)* | *(See list in UI)* | CMS, Mobile, Firmware, Security, UI, Data Engineering, etc. |

---

### 2. ECC Pipeline & Plugin Skills (15 Roles)
*Extracted from Anthropic Claude-Code Plugins & ECC Pipeline*

* `/silent-failure-scan` — Swallowed exceptions & silent error audit.
* `/build-resolve` — Compilation, type error, and syntax error resolver.
* `/perf-optimize` — Execution latency, memory leak, and token budget optimizer.
* `/harness-optimize` — Multi-agent harness, prompt template, and tool binding auditor.
* `/a11y-audit` — Accessibility (WCAG 2.1), ARIA roles, and screen-reader audit.
* `/e2e-run` — Integration test suite and regression verifier.
* `/seo-audit` — Web app SEO, OpenGraph, and semantic HTML audit.
* `/doc-sync` — Documentation, codemap, and README sync.
* `/code-explorer` — Deep codebase tracing from entry points to database.
* `/code-architect` — Architectural blueprint and technical spec design.
* `/code-reviewer` — Confidence-scored code review (flags >= 75 confidence).
* `/feature-dev` — 7-phase feature development pipeline.
* `/git-workflow` — Conventional Commits, push, and PR checklist.
* `/security-guidance` — 3-layer security audit and secret redaction.
* `/frontend-design` — Non-templated UI design & visual polish.

---

### 3. gstack Review Workflows & Strix Pentest Suite
*Extracted from YC gstack & Strix Security Framework*

* `/office-hours` — YC Product interrogation with 6 forcing questions.
* `/plan-ceo-review` — CEO strategic scope review & 10-star product vision.
* `/plan-eng-review` — Eng Manager review: architecture lock & failure modes.
* `/plan-design-review` — Senior Designer review: rate UI 0-10 & AI slop check.
* `/autoplan` — Automated review pipeline chaining CEO -> Design -> Eng Review.
* `/cso` — Chief Security Officer audit with OWASP Top 10 & STRIDE threat modeling.
* `/strix_pentest` — 3-phase autonomous penetration testing (Recon -> Exploit -> PoC).

---

## 🚀 Prompt Engineering Cookbook

### 1. Web Scraping & Data Extraction
```markdown
Search the web for top Chennai tech sponsors, use scrapling_stealth_fetch_tool 
to load their sponsor directory, and parse out sponsor company names, websites, 
and contact phone numbers into a formatted table.
```

### 2. Architecture & System Specification
```markdown
Run /backend-architect and /code-architect to design a high-throughput 
microservice architecture for a real-time analytics engine. Include an ASCII 
data flow diagram and database schema.
```

### 3. Security & Vulnerability Remediation
```markdown
Run /cso and /silent-failure-scan to audit the authentication module. 
Identify SQL injection, JWT flaws, swallowed exceptions, and return safe 
code replacements.
```

### 4. Code Refactoring & Optimization
```markdown
Run /perf-optimize and /rust-specialist to refactor the data parsing loop. 
Calculate token budget savings and optimize execution latency.
```
