import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState(null);
  const [topic, setTopic] = useState("");
  const [log, setLog] = useState([]);
  const [loading, setLoading] = useState(false);

  // Auth State
  const [password, setPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [authError, setAuthError] = useState("");

  // Configuration management state
  const [configData, setConfigData] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [apiKeys, setApiKeys] = useState({
    GOOGLE_API_KEY: "",
    GROQ_API_KEY: "",
    OPENAI_API_KEY: "",
    ANTHROPIC_API_KEY: "",
    DEEPSEEK_API_KEY: "",
    TOGETHER_API_KEY: "",
    CUSTOM_API_KEY: "",
    CUSTOM_BASE_URL: ""
  });
  const [workersConfig, setWorkersConfig] = useState({});

  // ECC Token Budget Advisor Depth State
  const [tokenDepth, setTokenDepth] = useState("Auto (50% Moderate)");
  const [workflowCategory, setWorkflowCategory] = useState("ecc"); // "ecc" or "gstack"

  // Security Audit State
  const [activeTab, setActiveTab] = useState("url");
  const [targetUrl, setTargetUrl] = useState("");
  const [sourceCode, setSourceCode] = useState("");
  const [fileName, setFileName] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  // gstack Memory & Redaction State
  const [showMemory, setShowMemory] = useState(false);
  const [gstackDecisions, setGstackDecisions] = useState([]);
  const [testRedactInput, setTestRedactInput] = useState("");
  const [testRedactResult, setTestRedactResult] = useState(null);

  // Tools Catalog State
  const [toolsCatalog, setToolsCatalog] = useState([]);
  const [selectedToolCategory, setSelectedToolCategory] = useState("ALL");
  const [selectedTool, setSelectedTool] = useState(null);
  const [showToolsCatalog, setShowToolsCatalog] = useState(true);

  const fetchToolsCatalog = () => {
    axios.get("http://localhost:8000/api/tools")
      .then(r => {
        const fetchedTools = r.data.tools || [];
        setToolsCatalog(fetchedTools);
        if (fetchedTools.length > 0 && !selectedTool) {
          setSelectedTool(fetchedTools[0]);
        }
      })
      .catch(err => console.error("Failed to fetch tools catalog", err));
  };

  const fetchGstackMemory = () => {
    setShowMemory(!showMemory);
    axios.get("http://localhost:8000/api/decisions")
      .then(r => setGstackDecisions(r.data.decisions || []))
      .catch(err => console.error("Failed to fetch decisions", err));
  };

  const handleTestRedact = () => {
    if (!testRedactInput.trim()) return;
    axios.post("http://localhost:8000/api/redact", { text: testRedactInput })
      .then(r => setTestRedactResult(r.data))
      .catch(err => alert("Redaction test failed: " + err.message));
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert("File exceeds 10MB limit.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setSourceCode(event.target.result);
      setFileName(file.name);
      setUploadSuccess(`Loaded ${file.name} successfully.`);
    };
    reader.onerror = () => {
      alert("Error reading file.");
    };
    reader.readAsText(file);
  };


  // Check backend health and load configs on mount
  useEffect(() => {
    fetchStatusAndConfig();
    fetchToolsCatalog();
  }, []);

  const fetchStatusAndConfig = () => {
    axios.get("http://localhost:8000/health")
      .then(r => {
        setStatus(r.data);
        if (!r.data.password_required) {
          setIsAuthenticated(true);
        }
      })
      .catch(() => setStatus({ error: "Unable to reach backend" }));

    axios.get("http://localhost:8000/config")
      .then(r => {
        setConfigData(r.data);
        setWorkersConfig(r.data.workers || {});
      })
      .catch(err => console.error("Failed to load configs", err));
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    axios.post("http://localhost:8000/verify_password", { password })
      .then(() => {
        setIsAuthenticated(true);
        setAuthError("");
      })
      .catch(err => {
        setAuthError(err.response?.data?.detail || "Invalid password");
      });
  };

  const handleRunStream = () => {
    const effectiveTopic = topic.trim() || (targetUrl.trim() ? `Audit target website URL: ${targetUrl.trim()}` : sourceCode.trim() ? `Audit source code ${fileName ? `(${fileName})` : ''}` : "");
    if (!effectiveTopic) return;
    setLog([]);
    setLoading(true);

    // Build context payload matching the Streamlit audit logic
    let auditContext = "";
    if (sourceCode) {
      auditContext += `--- SOURCE CODE${fileName ? ` (${fileName})` : ""} ---\n${sourceCode}\n\n`;
    }
    if (targetUrl) {
      auditContext += `--- TARGET URL: ${targetUrl} ---\n\n`;
    }
    if (tokenDepth && tokenDepth !== "Auto (50% Moderate)") {
      auditContext += `[ECC TOKEN BUDGET ADVISOR DEPTH]: ${tokenDepth}\n\n`;
    }

    const url = `http://localhost:8000/run_stream?topic=${encodeURIComponent(effectiveTopic)}&context=${encodeURIComponent(auditContext)}&password=${encodeURIComponent(password)}`;
    const es = new EventSource(url);


    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setLog((prev) => [...prev, data]);
        if (data.event === "finished" || data.event === "error") {
          es.close();
          setLoading(false);
        }
      } catch (err) {
        setLog((prev) => [...prev, { event: "error", detail: "Failed to parse stream event" }]);
        es.close();
        setLoading(false);
      }
    };

    es.onerror = (e) => {
      console.error("SSE stream error", e);
      setLog((prev) => [...prev, { event: "error", detail: "Lost connection to the streaming server" }]);
      es.close();
      setLoading(false);
    };
  };

  const saveApiKeys = (e) => {
    e.preventDefault();
    axios.post("http://localhost:8000/config/keys", { ...apiKeys, password })
      .then(() => {
        alert("API keys saved to .env!");
        fetchStatusAndConfig();
      })
      .catch(err => alert("Error saving API keys: " + err.message));
  };

  const saveWorkerConfig = (e) => {
    e.preventDefault();
    axios.post(`http://localhost:8000/config/workers?password=${encodeURIComponent(password)}`, workersConfig)
      .then(() => {
        alert("Worker configuration updated!");
        fetchStatusAndConfig();
        setShowConfig(false);
      })
      .catch(err => alert("Error saving worker config: " + err.message));
  };

  const handleKeyChange = (field, val) => {
    setApiKeys(prev => ({ ...prev, [field]: val }));
  };

  const handleWorkerChange = (agent, field, val) => {
    setWorkersConfig(prev => ({
      ...prev,
      [agent]: {
        ...prev[agent],
        [field]: field === "temperature" ? parseFloat(val) : val
      }
    }));
  };


  const isOnline = status && !status.error;
  const nodesList = status?.nodes || [];

  if (!isAuthenticated) {
    return (
      <div className="app-container" style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <form onSubmit={handleLoginSubmit} className="panel-card" style={{ width: "300px" }}>
          <h2>Authentication</h2>
          <input
            type="password"
            className="styled-input"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {authError && <p style={{ color: "var(--accent-red)", fontSize: "0.8rem" }}>{authError}</p>}
          <button className="styled-button" style={{ marginTop: "1rem", width: "100%" }} type="submit">LOGIN</button>
        </form>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Top Header Grid (Exact match to Adam Shams website header grid) */}
      <div className="header-grid-navbar">
        <div className="nav-box-black">
          <h1>AUnitedAI Orchestrator</h1>
          <span style={{ fontSize: "0.8rem", color: "#48bb78" }}>●</span>
        </div>
        <div className="nav-box-center">
          ECC & gstack Workflows
        </div>
        <div className="nav-box-stacked">
          <div className="nav-box-stacked-top">
            <span style={{ cursor: "pointer" }} onClick={() => setShowConfig(!showConfig)}>
              {isOnline ? "Service Online (12 Nodes)" : "Service Offline"}
            </span>
          </div>
          <div className="nav-box-stacked-bottom" onClick={() => fetchGstackMemory()}>
            Decision Memory & Redactor
          </div>
        </div>
      </div>

      {/* Adam Shams Hero Graphic Section */}
      <div className="adam-hero-section">
        <div className="adam-hand-title">AUNITED AI</div>
        <div className="adam-subtext">
          Hi, I'm <u>AUnitedAI</u>!, I'm an <u>Agentic Task Force</u>! Welcome to my <u>World</u>!
        </div>
      </div>

      {/* Configuration View Overlay */}
      {showConfig && (
        <div className="panel-card" style={{ display: "flex", flexDirection: "column", gap: "2rem", borderTop: "3px solid #000000" }}>
          <div>
            <h2 style={{ fontSize: "1.5rem", marginBottom: "0.5rem", fontFamily: "'Space Grotesk', sans-serif" }}>API Keys Management</h2>
            <p style={{ color: "#555555", fontSize: "0.8rem", fontFamily: "monospace" }}>
              SAVED DIRECTLY TO LOCAL .ENV. LEAVE EMPTY TO KEEP UNCHANGED.
            </p>
            <form onSubmit={saveApiKeys} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
              {Object.keys(apiKeys).map((k) => (
                <div key={k} style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                  <label style={{ fontSize: "0.75rem", fontFamily: "monospace" }}>
                    {k} {configData?.keys?.[k] ? "(Active)" : ""}
                  </label>
                  <input
                    type={k.includes("KEY") ? "password" : "text"}
                    className="styled-input"
                    placeholder={configData?.keys?.[k] ? "••••••••••••" : "Enter key..."}
                    value={apiKeys[k]}
                    onChange={e => handleKeyChange(k, e.target.value)}
                  />
                </div>
              ))}
              <button className="styled-button" style={{ position: "static", gridColumn: "span 2", marginTop: "0.5rem" }} type="submit">
                SAVE API KEYS
              </button>
            </form>
          </div>

          <hr />

          <div>
            <h2 style={{ fontSize: "1.5rem", marginBottom: "0.5rem", fontFamily: "'Space Grotesk', sans-serif" }}>Worker Configuration</h2>
            <p style={{ color: "#555555", fontSize: "0.8rem", fontFamily: "monospace" }}>
              CUSTOMIZE BACKENDS, MODELS, AND INSTRUCTIONS FOR AGENTS.
            </p>
            <form onSubmit={saveWorkerConfig} style={{ display: "flex", flexDirection: "column", gap: "1.5rem", marginTop: "1rem" }}>
              {Object.keys(workersConfig).map((agent) => {
                const item = workersConfig[agent];
                return (
                  <div key={agent} style={{ borderBottom: "1px solid #000000", paddingBottom: "1rem" }}>
                    <h4 style={{ fontFamily: "monospace", color: "#000000", marginBottom: "0.75rem" }}>{agent.toUpperCase()}</h4>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", gap: "1rem" }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                        <label style={{ fontSize: "0.7rem", fontFamily: "monospace" }}>BACKEND</label>
                        <select
                          className="styled-input"
                          style={{ height: "100%", padding: "0.5rem" }}
                          value={item.backend}
                          onChange={e => handleWorkerChange(agent, "backend", e.target.value)}
                        >
                          {["Ollama", "Gemini", "Groq", "OpenAI", "Anthropic", "DeepSeek", "TogetherAI", "Custom API"].map(b => (
                            <option key={b} value={b}>{b}</option>
                          ))}
                        </select>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                        <label style={{ fontSize: "0.7rem", fontFamily: "monospace" }}>MODEL NAME</label>
                        <input
                          className="styled-input"
                          value={item.model}
                          onChange={e => handleWorkerChange(agent, "model", e.target.value)}
                        />
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                        <label style={{ fontSize: "0.7rem", fontFamily: "monospace" }}>TEMPERATURE ({item.temperature})</label>
                        <input
                          type="range"
                          min="0.0"
                          max="1.0"
                          step="0.1"
                          style={{ marginTop: "0.75rem" }}
                          value={item.temperature}
                          onChange={e => handleWorkerChange(agent, "temperature", e.target.value)}
                        />
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", marginTop: "0.75rem" }}>
                      <label style={{ fontSize: "0.7rem", fontFamily: "monospace" }}>SYSTEM INSTRUCTIONS</label>
                      <textarea
                        className="styled-input"
                        rows={2}
                        value={item.custom_prompt || ""}
                        onChange={e => handleWorkerChange(agent, "custom_prompt", e.target.value)}
                      />
                    </div>
                  </div>
                );
              })}
              <button className="styled-button" style={{ position: "static", marginTop: "1rem" }} type="submit">
                SAVE CONFIGURATION
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Main Grid Layout */}
      <div className="main-layout">
        
        {/* Left Control Column */}
        <div className="panel-left">

          {/* Node Visualizer Card */}
          <div className="panel-card">
            <h3>Active Graph Nodes</h3>
            {isOnline ? (
              <div className="nodes-grid">
                {nodesList.map((node) => (
                  <span key={node} className={`node-pill ${node === "orchestrator" ? "active-node" : ""}`}>
                    {node}
                  </span>
                ))}
              </div>
            ) : (
              <span style={{ color: "#555555", fontSize: "0.8rem", fontFamily: "monospace" }}>
                CONNECT BACKEND TO VIEW STRUCTURE
              </span>
            )}
          </div>

          {/* Security Audit Sidebar Card */}
          <div className="panel-card">
            <h3>Context & Security Audit Input</h3>
            
            <div className="terminal-tabs">
              <button className={`terminal-tab ${activeTab === 'url' ? 'active' : ''}`} onClick={() => setActiveTab('url')}>Target URL</button>
              <button className={`terminal-tab ${activeTab === 'code' ? 'active' : ''}`} onClick={() => setActiveTab('code')}>Source Code</button>
              <button className={`terminal-tab ${activeTab === 'file' ? 'active' : ''}`} onClick={() => setActiveTab('file')}>Upload File</button>
            </div>

            {activeTab === 'url' && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                <label style={{ fontSize: "0.7rem", fontFamily: "monospace", letterSpacing: "0.08em" }}>TARGET WEBSITE / REPO URL</label>
                <input
                  className="styled-input"
                  placeholder="https://github.com/user/repo"
                  value={targetUrl}
                  onChange={e => setTargetUrl(e.target.value)}
                />
              </div>
            )}

            {activeTab === 'code' && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                <label style={{ fontSize: "0.7rem", fontFamily: "monospace", letterSpacing: "0.08em" }}>PASTE SOURCE CODE</label>
                <textarea
                  className="styled-input"
                  placeholder="Paste contents here..."
                  rows={4}
                  value={sourceCode}
                  onChange={e => setSourceCode(e.target.value)}
                />
              </div>
            )}

            {activeTab === 'file' && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <label style={{ fontSize: "0.7rem", fontFamily: "monospace", letterSpacing: "0.08em" }}>UPLOAD AUDIT FILE</label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="styled-input"
                  style={{ padding: "0.5rem" }}
                  accept=".py,.js,.ts,.java,.go,.rb,.php,.rs,.c,.cpp,.h,.html,.css,.sql,.sh,.bat,.ps1,.yml,.yaml,.json,.toml,.xml,.conf,.ini,.cfg,.env,.txt,.md"
                />
                {uploadSuccess && <span style={{ fontSize: "0.75rem", color: "#000000", fontFamily: "monospace", fontWeight: "bold" }}>{uploadSuccess}</span>}
              </div>
            )}

            {(targetUrl || sourceCode || fileName) && (
              <div className="context-pill">
                <span>Context Attached: {targetUrl ? `URL (${targetUrl.slice(0, 30)}...)` : fileName || 'Pasted Code'}</span>
                <button className="clear-btn" onClick={() => { setTargetUrl(""); setSourceCode(""); setFileName(""); setUploadSuccess(""); }}>
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Autonomous Agent Orchestrator Launchpad */}
          <div className="panel-card" style={{ borderTop: "3px solid #000000", flex: 1, display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <h3 style={{ fontSize: "1.1rem", marginBottom: "0.2rem" }}>Autonomous Agent Launchpad</h3>
              <p style={{ fontSize: "0.75rem", color: "#555555", fontFamily: "monospace" }}>
                AI AUTOMATICALLY PLANS TASKS, ASSIGNS WORKER AGENTS, AND BINDS TOOLS BASED ON YOUR PROMPT.
              </p>
            </div>

            {/* Token Budget Advisor Control */}
            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <label style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#000000", fontWeight: "bold" }}>
                RESPONSE DEPTH & TOKEN BUDGET
              </label>
              <select
                className="styled-input"
                style={{ padding: "0.5rem", fontSize: "0.78rem" }}
                value={tokenDepth}
                onChange={(e) => setTokenDepth(e.target.value)}
              >
                <option value="Auto (50% Moderate)">Auto (50% Moderate)</option>
                <option value="25% Essential (Brief)">25% Essential (Brief, 2-4 sentences)</option>
                <option value="50% Moderate (Balanced)">50% Moderate (Balanced answer)</option>
                <option value="75% Detailed (Full)">75% Detailed (Full breakdown + code)</option>
                <option value="100% Exhaustive (Deep Dive)">100% Exhaustive (Deep dive + edge cases)</option>
              </select>
            </div>

            {/* 2 Main Workflow Category Selectors */}
            <div>
              <label style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#000000", fontWeight: "bold", display: "block", marginBottom: "0.4rem" }}>
                WORKFLOW SHORTCUT PALETTE
              </label>
              <div className="category-tab-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
                <button
                  className={`cat-tab-btn ${workflowCategory === 'ecc' ? 'active' : ''}`}
                  onClick={() => setWorkflowCategory('ecc')}
                >
                  ECC Harness Skills (8)
                </button>

                <button
                  className={`cat-tab-btn ${workflowCategory === 'gstack' ? 'active' : ''}`}
                  onClick={() => setWorkflowCategory('gstack')}
                >
                  gstack Workflows (15)
                </button>
              </div>

              {/* Interactive Preset Chips Palette */}
              <div className="preset-chips-grid">
                {workflowCategory === 'ecc' && [
                  { label: "/silent-failure-scan", topic: "Run silent failure audit: Scan codebase for swallowed exceptions, bare excepts, empty catch blocks, bad fallbacks." },
                  { label: "/build-resolve", topic: "Run build error resolver: Diagnose compilation failures, type errors, syntax errors, and broken dependencies." },
                  { label: "/perf-optimize", topic: "Run performance optimizer: Analyze latency bottlenecks, unoptimized loops, memory leaks, and token budget." },
                  { label: "/harness-optimize", topic: "Run harness optimizer: Audit multi-agent prompts, tool delegation efficiency, and graph state transitions." },
                  { label: "/a11y-audit", topic: "Run a11y architect: Audit UI accessibility (WCAG 2.1), color contrast, screen reader semantics, and ARIA roles." },
                  { label: "/e2e-run", topic: "Run e2e runner: Execute integration test suite, regression checks, and user flow validations." },
                  { label: "/seo-audit", topic: "Run seo specialist: Audit web application for SEO, title/meta tags, OpenGraph headers, and semantic HTML." },
                  { label: "/doc-sync", topic: "Run doc updater: Update project documentation, codemaps, API specs, and README files." }
                ].map((p, idx) => (
                  <button
                    key={idx}
                    className={`preset-chip ${topic === p.topic ? "active-chip" : ""}`}
                    onClick={() => setTopic(p.topic)}
                  >
                    {p.label}
                  </button>
                ))}

                {workflowCategory === 'gstack' && [
                  { label: "/office-hours", topic: "Run /office-hours: Product interrogation with 6 forcing questions on the target project." },
                  { label: "/plan-ceo-review", topic: "Run /plan-ceo-review: CEO strategic scope review, mode evaluation, 10-star product vision." },
                  { label: "/plan-eng-review", topic: "Run /plan-eng-review: Eng Manager review to lock architecture, failure modes, and state machines." },
                  { label: "/plan-design-review", topic: "Run /plan-design-review: Senior Designer review, rate UI 0-10, AI slop detection." },
                  { label: "/autoplan", topic: "Run /autoplan: Automated review pipeline chaining CEO -> Design -> Eng Review." },
                  { label: "/spec", topic: "Run /spec: Author executable technical spec with quality gates and secret redaction." },
                  { label: "/plan-devex-review", topic: "Run /plan-devex-review: Audit Developer Experience & Time-To-Hello-World (TTHW) friction points." },
                  { label: "/cso", topic: "Run /cso: Chief Security Officer audit with OWASP Top 10, STRIDE threat modeling, and secret redaction." },
                  { label: "/investigate", topic: "Run /investigate: Iron Law root-cause debugging methodology and data flow tracing." },
                  { label: "/document-generate", topic: "Run /document-generate: Author Diataxis documentation (Tutorial, How-To, Reference, Explanation)." },
                  { label: "/canary", topic: "Run /canary: Run canary monitoring loop & Core Web Vitals performance benchmark." },
                  { label: "/freeze", topic: "Run /freeze: Freeze critical project paths to protect them against edits." },
                  { label: "/qa", topic: "Run /qa: QA Lead test execution, regression checks, and bug report generation." },
                  { label: "/ship", topic: "Run /ship: Release Engineer pre-flight checks, test validation, and release PR generation." },
                  { label: "/retro", topic: "Run /retro: Weekly retrospective on shipping velocity, test health, and project learnings." }
                ].map((p, idx) => (
                  <button
                    key={idx}
                    className={`preset-chip ${topic === p.topic ? "active-chip" : ""}`}
                    onClick={() => setTopic(p.topic)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Spacious Main Prompt Text Area & Execute Button */}
            <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <label style={{ fontSize: "0.75rem", color: "#000000", fontWeight: "bold", fontFamily: "monospace", letterSpacing: "0.08em" }}>
                ENTER TASK TOPIC / PROMPT INSTRUCTIONS:
              </label>
              <textarea
                className="styled-input"
                style={{ fontSize: "0.88rem", padding: "0.75rem", minHeight: "90px", lineHeight: "1.4", fontFamily: "'JetBrains Mono', monospace" }}
                placeholder="Type any task or goal here... (e.g. Audit auth.py for security vulnerabilities, fix bugs, and refactor code)"
                rows={3}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={loading || !isOnline}
              />
              <button 
                className="styled-button" 
                style={{ position: "static", padding: "0.85rem", fontSize: "0.95rem", fontWeight: "900", letterSpacing: "0.05em", marginTop: "0.2rem" }}
                onClick={handleRunStream} 
                disabled={loading || !isOnline || (!topic.trim() && !targetUrl.trim() && !sourceCode.trim())}
              >
                {loading ? "EXECUTION STREAM RUNNING..." : "EXECUTE AUTONOMOUS AGENT TASK"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Output logs Column */}
        <div className="panel-right">
          {/* Stream Output Header Bar */}
          <div className="stream-header-bar">
            <span className="stream-header-title">
              {loading ? "EXECUTION STREAM ACTIVE" : "AGENT OUTPUT STREAM"}
            </span>
            <div className="stream-actions">
              {log.length > 0 && (
                <button 
                  className="preset-chip" 
                  onClick={() => setLog([])}
                  style={{ color: "var(--accent-red)", borderColor: "var(--accent-red)" }}
                >
                  CLEAR LOGS
                </button>
              )}
            </div>
          </div>

          <div className="stream-container">
            {log.length === 0 ? (
              <div className="stream-empty">
                <p>SYSTEM READY. SELECT A PRESET OR ENTER TOPIC AND EXECUTE TO STREAM LOGS.</p>
              </div>
            ) : (
              log.map((msg, i) => {
                if (msg.event === "started") {
                  return (
                    <div key={i} className="plan-card">
                      <div className="section-label plan-label">PLAN DEFINED</div>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", fontFamily: "monospace", marginBottom: "0.5rem" }}>
                        Orchestration initiated for: "{msg.topic}"
                      </p>
                    </div>
                  );
                }

                if (msg.event === "error") {
                  return (
                    <div key={i} className="worker-card">
                      <div className="section-label work-label">EXECUTION ERROR</div>
                      <p style={{ color: "var(--accent-red)", fontFamily: "monospace", fontSize: "0.85rem" }}>
                        {msg.detail}
                      </p>
                    </div>
                  );
                }

                if (msg.event === "finished") {
                  const finalReport = msg.result?.final_report || "";
                  const plan = msg.result?.plan;
                  const completedTasks = msg.result?.completed_tasks || [];

                  return (
                    <React.Fragment key={i}>
                      {plan && (
                        <div className="plan-card" style={{ marginTop: "1rem" }}>
                          <div className="section-label plan-label">FINAL PLAN STRATEGY</div>
                          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontFamily: "monospace", marginBottom: "0.75rem" }}>
                            {plan.overall_strategy}
                          </p>
                          {plan.tasks && plan.tasks.map((task) => {
                            const badgeClass = ["security_audit", "cso_audit"].includes(task.worker_type) ? "badge security" :
                                               ["silent_failure_hunter", "build_error_resolver", "performance_optimizer", "harness_optimizer", "a11y_architect", "e2e_runner", "seo_specialist", "doc_updater"].includes(task.worker_type) ? "badge ecc" : "badge worker";
                            return (
                              <div key={task.task_id} className="plan-row" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.4rem" }}>
                                <span className={badgeClass}>{task.worker_type}</span>
                                <strong>[{task.task_id}]</strong> {task.description}
                                {task.assigned_tools && task.assigned_tools.length > 0 && (
                                  <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#555" }}>
                                    Tools: {task.assigned_tools.join(", ")}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {completedTasks.length > 0 && (
                        <div className="worker-card" style={{ marginTop: "1rem" }}>
                          <div className="section-label work-label">COMPLETED AGENT TASKS</div>
                          {completedTasks.map((t) => {
                            const badgeClass = ["security_audit", "cso_audit"].includes(t.worker_type) ? "badge security" :
                                               ["silent_failure_hunter", "build_error_resolver", "performance_optimizer", "harness_optimizer", "a11y_architect", "e2e_runner", "seo_specialist", "doc_updater"].includes(t.worker_type) ? "badge ecc" : "badge worker";
                            return (
                              <div key={t.task_id} className="plan-row" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.4rem" }}>
                                <span className={badgeClass}>{t.worker_type}</span>
                                <strong>[{t.task_id}]</strong> {t.description}
                                {t.assigned_tools && t.assigned_tools.length > 0 && (
                                  <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#555" }}>
                                    Tools: {t.assigned_tools.join(", ")}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {finalReport && (
                        <div className="report-card" style={{ marginTop: "1rem" }}>
                          <div className="section-label report-label">SYNTHESIZED FINAL REPORT</div>
                          {finalReport}
                        </div>
                      )}

                      {!finalReport && (
                        <div className="report-card" style={{ marginTop: "1rem" }}>
                          <div className="section-label report-label">GRAPH STATE RESULTS</div>
                          <pre className="json-block">
                            {JSON.stringify(msg.result, null, 2)}
                          </pre>
                        </div>
                      )}
                    </React.Fragment>
                  );
                }

                return null;
              })
            )}
          </div>
        </div>

      </div>
    </div>
  );
}




