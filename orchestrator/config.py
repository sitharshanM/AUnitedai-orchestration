import json
import os

CONFIG_FILE = "worker_config.json"

DEFAULT_CONFIG = {
    "research": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.1,
        "custom_prompt": ""
    },
    "writing": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.7,
        "custom_prompt": ""
    },
    "analysis": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "coding": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "review": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.3,
        "custom_prompt": ""
    },
    "file_writer": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "security_audit": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "orchestrator": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "critic": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "synthesizer": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "custom_prompt": ""
    },
    "office_hours": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.4,
        "custom_prompt": "Run YC Office Hours product interrogation with 6 forcing questions."
    },
    "ceo_review": {
        "backend": "Gemini",
        "model": "gemini-3.5-flash",
        "temperature": 0.3,
        "custom_prompt": "Run CEO Strategic Review: Challenge premises, mode evaluation (Expansion/Triage)."
    },
    "eng_review": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.1,
        "custom_prompt": "Run Eng Manager Review: Lock architecture, state machines, failure modes, ASCII data flow."
    },
    "design_review": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.3,
        "custom_prompt": "Run Senior Designer Review: Rate UI 0-10, AI Slop detection, polish recommendations."
    },
    "cso_audit": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": "Run CSO Security Audit: OWASP Top 10 + STRIDE threat modeling & secret redaction."
    },
    "investigate": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.0,
        "custom_prompt": "Run Iron Law Root-Cause Debugging: Trace data flows, hypotheses, no blind fixes."
    },
    "qa_lead": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.1,
        "custom_prompt": "Run QA Verification: Test execution, regression checks, bug reporting."
    },
    "ship_release": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.1,
        "custom_prompt": "Run Release Engineer: Pre-flight checks, test verification, PR doc generation."
    },
    "retro": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.2,
        "custom_prompt": "Run Weekly Retrospective: Shipping velocity, test health, growth learnings."
    },
    "spec_author": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.1,
        "custom_prompt": "Author Technical Specification (/spec) with Codex quality gate and scope boundaries."
    },
    "devex_lead": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.2,
        "custom_prompt": "Audit Developer Experience & Time-To-Hello-World (TTHW) friction points."
    },
    "diataxis_writer": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "custom_prompt": "Author Diataxis documentation (Tutorial, How-To, Reference, Explanation)."
    },
    "canary_sre": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": "Run Canary & Performance Benchmark: Core Web Vitals, API latency, console errors."
    },
    "autoplan": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.1,
        "custom_prompt": "Run AutoPlan Pipeline: CEO → Design → Eng Architecture review chain."
    },
    "silent_failure_hunter": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": "Audit codebase for silent failures, swallowed exceptions, empty catch blocks, bad fallbacks, and missing error propagation."
    },
    "build_error_resolver": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.0,
        "custom_prompt": "Diagnose build errors, syntax failures, type mismatches, and dependency issues with specific fixes."
    },
    "performance_optimizer": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.1,
        "custom_prompt": "Optimize code latency, memory usage, unoptimized loops, and token budget consumption."
    },
    "harness_optimizer": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.1,
        "custom_prompt": "Audit agent harness prompts, tool delegation efficiency, and graph state transitions."
    },
    "a11y_architect": {
        "backend": "Ollama",
        "model": "qwen2.5:latest",
        "temperature": 0.2,
        "custom_prompt": "Audit UI accessibility (WCAG 2.1), color contrast, ARIA roles, and screen reader compatibility."
    },
    "e2e_runner": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": "Run end-to-end integration tests, regression checks, and user flow validations."
    },
    "seo_specialist": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.3,
        "custom_prompt": "Optimize pages for SEO, title/meta descriptions, semantic HTML structure, and OpenGraph headers."
    },
    "doc_updater": {
        "backend": "Ollama",
        "model": "llama3.1:latest",
        "temperature": 0.2,
        "custom_prompt": "Keep documentation, READMEs, API specifications, and architecture maps updated."
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            for k, v in config.items():
                if k in merged:
                    merged[k].update(v)
            return merged
    except Exception:
        return DEFAULT_CONFIG

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
