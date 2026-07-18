"""
gui.py  -  Chat-style Streamlit GUI for the AUnitedAI Multi-Agent Orchestrator.
Terminal / technical aesthetic (mono labels, thin borders, restrained palette).

Run with:  streamlit run gui.py
"""

import time
import streamlit as st
import os
import base64
from orchestrator import config

current_config = config.load_config()

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AUnitedAI Orchestrator",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

bg_css = ".stApp { background:#0a0b0d; }"
if os.path.exists("assets/hero_bg.png"):
    bg_img = get_base64_image("assets/hero_bg.png")
    bg_css = f"""
    .stApp {{
        background: url(data:image/png;base64,{bg_img}) no-repeat center center fixed !important;
        background-size: auto 70% !important; /* adjust height to 70% of screen */
        background-color: #0a0b0d !important;
    }}
    """

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"<style>{bg_css}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family:'Inter',sans-serif; }
h1,h2,h3, .mono { font-family:'JetBrains Mono',monospace; }

/* Eyebrow tag */
.eyebrow{
    display:inline-block; font-family:'JetBrains Mono',monospace;
    font-size:.72rem; letter-spacing:.12em; text-transform:uppercase;
    color:#7a8a7d; border:1px solid #2a2f2b; border-radius:5px;
    padding:.25rem .6rem; margin-bottom:1rem;
}
.eyebrow .dot{ color:#3ecf5b; }

/* Hero banner */
.hero{
    background:#101113; border:1px solid #1e2320; border-radius:10px;
    padding:2.2rem 2.4rem; margin-bottom:1.4rem;
}
.hero h1{
    font-size:2.1rem; font-weight:700; margin:0; line-height:1.2;
    color:#e8ece8; letter-spacing:-.01em;
}
.hero h1 .accent{ color:#e0473e; }
.hero p{ color:#8a938c; margin:.6rem 0 0 0; font-size:.95rem; font-family:'JetBrains Mono',monospace; }

/* Node cards inside chat bubbles */
.plan-card{
    background:#101113; border:1px solid #1e2320; border-left:3px solid #3ecf5b;
    border-radius:8px; padding:.9rem 1.1rem; margin:.5rem 0;
}
.worker-card{
    background:#101113; border:1px solid #1e2320; border-left:3px solid #e0473e;
    border-radius:8px; padding:.9rem 1.1rem; margin:.5rem 0;
}
.report-card{
    background:#101113; border:1px solid #1e2320; border-left:3px solid #ff2e93;
    border-radius:8px; padding:.9rem 1.1rem; margin:.5rem 0;
    white-space:pre-wrap; font-size:.88rem; line-height:1.7; color:#dfe4e0;
}
.badge{
    display:inline-block; border-radius:4px; padding:.1rem .5rem;
    font-size:.68rem; font-weight:600; margin-right:.4rem;
    font-family:'JetBrains Mono',monospace; letter-spacing:.03em;
    background:rgba(62,207,91,.08); color:#3ecf5b;
    border:1px solid rgba(62,207,91,.3);
}
.badge.worker{
    background:rgba(224,71,62,.08); color:#e0473e;
    border:1px solid rgba(224,71,62,.3);
}
.badge.security{
    background:rgba(245,158,11,.08); color:#f59e0b;
    border:1px solid rgba(245,158,11,.3);
}
.security-card{
    background:#101113; border:1px solid #1e2320; border-left:3px solid #f59e0b;
    border-radius:8px; padding:.9rem 1.1rem; margin:.5rem 0;
}
.section-label{
    font-family:'JetBrains Mono',monospace;
    font-size:.72rem; font-weight:700; letter-spacing:.1em;
    text-transform:uppercase; margin-bottom:.5rem;
}
.plan-label  { color:#3ecf5b; }
.work-label  { color:#e0473e; }
.report-label{ color:#ff2e93; }
.security-label{ color:#f59e0b; }

/* Numbered feature rows (Hermes-style) */
.feat-num{
    font-family:'JetBrains Mono',monospace; font-size:.75rem; color:#e0473e;
    letter-spacing:.08em;
}
.feat-title{ font-weight:600; color:#e8ece8; margin:.1rem 0 .2rem 0; }
.feat-desc{ color:#8a938c; font-size:.85rem; }

/* Sidebar */
section[data-testid="stSidebar"]>div{ background:#0d0e10; border-right:1px solid #1e2320; }
section[data-testid="stSidebar"] .stMarkdownContainer { font-family:'JetBrains Mono',monospace; }

hr{ border-color:#1e2320 !important; }

/* Buttons */
.stButton>button{
    background:#101113; border:1px solid #2a2f2b; color:#c7cdc8;
    font-family:'JetBrains Mono',monospace; font-size:.78rem; border-radius:6px;
}
.stButton>button:hover{ border-color:#3ecf5b; color:#3ecf5b; }
</style>
""", unsafe_allow_html=True)


# ── Load graph (cached so it only loads once) ──────────────────────────────────
def load_app():
    from orchestrator.graph import app as langgraph_app
    return langgraph_app


# ── Helper: render stored messages ────────────────────────────────────────────
def display_chat_messages():
    for i, msg in enumerate(st.session_state.messages):
        avatar = "▪️" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"], unsafe_allow_html=True)
            for block in msg.get("blocks", []):
                st.markdown(block, unsafe_allow_html=True)
            for w in msg.get("workers", []):
                with st.expander(f"[{w['tid']}] {w['wtype']}", expanded=False):
                    st.markdown(w["block"], unsafe_allow_html=True)
            if "final_report" in msg and msg["final_report"]:
                st.markdown("---")
                st.markdown(msg["final_report"])
                st.download_button(
                    "Download final report (.md)",
                    data=msg["final_report"],
                    file_name="final_report.md",
                    mime="text/markdown",
                    key=f"dl_{i}"
                )


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### AUnitedAI")
    st.caption("MULTI-AGENT ORCHESTRATOR")
    st.markdown(
        """<div style="margin-top: 0.8rem; line-height: 1.6; font-size: 0.88rem; color: #c7cdc8;">
        A <b style="color:#e8ece8">LangGraph</b> multi-agent system powered by <b style="color:#e8ece8">Gemini</b>, <b style="color:#e8ece8">Groq</b>, and local <b style="color:#e8ece8">Ollama</b> models.
        Give it a complex topic — it breaks the work into sub-tasks, dispatches specialised
        worker agents (research, coding, analysis, review, writing, file-writer, <b style="color:#f59e0b">security-audit</b>),
        runs a self-correction critic loop, and synthesises a final report.</div>""",
        unsafe_allow_html=True
    )
    st.divider()
    st.markdown("**SETTINGS**")

    show_workers = st.toggle("Show individual worker outputs", value=True)
    typing_speed = st.slider("Typing speed (words/sec)", 5, 50, 20)

    st.divider()
    st.markdown("**🛡️ SECURITY AUDIT INPUT**")
    st.caption("Upload files or paste a URL to audit for vulnerabilities.")

    ALLOWED_EXTENSIONS = [
        "py", "js", "ts", "java", "go", "rb", "php", "rs", "c", "cpp", "h",
        "html", "css", "sql", "sh", "bat", "ps1",
        "yml", "yaml", "json", "toml", "xml", "conf", "ini", "cfg",
        "env", "txt", "md", "tf", "dockerfile",
    ]
    uploaded_files = st.file_uploader(
        "Upload source files",
        accept_multiple_files=True,
        type=ALLOWED_EXTENSIONS,
        help="Max 5 files, 10MB each. Supports code, config, and text files.",
        key="security_upload"
    )
    target_url = st.text_input(
        "Or paste a URL (GitHub repo, website)",
        placeholder="https://github.com/user/repo",
        key="security_url"
    )

    # Process uploads and URL into session state
    upload_context_parts = []
    if uploaded_files:
        os.makedirs("./uploads", exist_ok=True)
        for uf in uploaded_files[:5]:  # Max 5 files
            if uf.size > 10 * 1024 * 1024:  # 10MB limit
                st.warning(f"Skipped {uf.name} — exceeds 10MB limit.")
                continue
            content = uf.read().decode("utf-8", errors="replace")
            # Save to uploads dir
            save_path = os.path.join("./uploads", uf.name)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            upload_context_parts.append(f"--- FILE: {uf.name} ---\n{content[:50000]}")
        if upload_context_parts:
            st.success(f"{len(upload_context_parts)} file(s) loaded for analysis.")

    if target_url and target_url.strip():
        upload_context_parts.append(f"--- TARGET URL: {target_url.strip()} ---")
        st.info(f"URL target set: `{target_url.strip()}`")

    st.session_state.uploaded_context = "\n\n".join(upload_context_parts) if upload_context_parts else ""

    st.divider()
    st.markdown("**WORKER MODELS**")
    
    if st.button("⚙️ Configure Workers", use_container_width=True):
        st.session_state.show_dashboard = not st.session_state.get("show_dashboard", False)
        st.rerun()
        
    for w_key, w_val in current_config.items():
        st.markdown(f"`{w_key.upper()}` · {w_val['backend']}  \n`{w_val['model']}`")


    st.divider()
    st.markdown("**KNOWLEDGE BASE**")
    st.info("9 PDF books + 508 `.md` files indexed via `nomic-embed-text`.\nRun `python index_docs.py` to re-index.")
    st.success("Orchestrator ready")


# ── Dashboard View ─────────────────────────────────────────────────────────────
if st.session_state.get("show_dashboard", False):
    st.markdown("## ⚙️ Worker Configuration Dashboard")
    st.markdown("Customize the models, backends, and instructions for each LangGraph agent.")
    
    with st.form("worker_config_form"):
        new_config = {}
        for w_key, w_val in current_config.items():
            st.markdown(f"#### {w_key.upper()}")
            c1, c2, c3 = st.columns([1, 2, 1])
            backend = c1.selectbox("Backend", ["Ollama", "Gemini", "Groq"], index=["Ollama", "Gemini", "Groq"].index(w_val["backend"]), key=f"{w_key}_backend")
            model = c2.text_input("Model Name", value=w_val["model"], key=f"{w_key}_model")
            temp = c3.slider("Temperature", 0.0, 1.0, float(w_val["temperature"]), key=f"{w_key}_temp")
            prompt = st.text_area("Custom System Instructions (Optional)", value=w_val.get("custom_prompt", ""), key=f"{w_key}_prompt", height=68)
            new_config[w_key] = {
                "backend": backend,
                "model": model,
                "temperature": temp,
                "custom_prompt": prompt
            }
            st.markdown("---")
            
        if st.form_submit_button("💾 Save Configuration"):
            config.save_config(new_config)
            st.success("Configuration saved! Close the dashboard to continue orchestrating.")
            time.sleep(1)
            st.session_state.show_dashboard = False
            st.rerun()
            
    st.stop() # Prevents the rest of the chat UI from rendering

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="eyebrow"><span class="dot">●</span> Open Source · Multi-Agent System</div>
<div class="hero">
    <h1>The Orchestrator <span class="accent">That Ships</span> Your Work</h1>
    <p>Give it a topic — it plans, researches, codes, reviews, and writes a full report, end to end.</p>
</div>
""", unsafe_allow_html=True)


# ── How it works expander ──────────────────────────────────────────────────────
with st.expander("How this works"):
    st.markdown("#### Architecture")
    st.markdown(
        """The **Orchestrator** receives your topic and breaks it into a dependency-ordered plan.
        Each sub-task is dispatched to a specialised **Worker** agent with its own model and toolset.
        A **Critic** loop reviews each worker's output and triggers self-correction if quality is insufficient.
        The **Synthesizer** then compiles all outputs into one cohesive final report."""
    )
    st.markdown("#### Worker Types")
    info = [
        ("01", "RESEARCH", "Searches the web (DuckDuckGo), fetches webpages, and queries the local knowledge base via RAG."),
        ("02", "ANALYSIS", "Reads local files and the knowledge base to evaluate and compare information."),
        ("03", "CODING", "Writes, reads, and executes code files using `qwen2.5-coder`."),
        ("04", "REVIEW", "Reviews code or writing for bugs, quality, and improvements."),
        ("05", "FILE WRITER", "Persists content to the local filesystem."),
        ("06", "WRITING", "Generates articles, reports, and documentation using `llama3.1`."),
        ("07", "SECURITY AUDIT", "Scans code for vulnerabilities, audits configs, checks dependencies, maps to OWASP Top 10."),
    ]
    cols = st.columns(3)
    for i, (num, title, desc) in enumerate(info):
        with cols[i % 3]:
            color = "#f59e0b" if title == "SECURITY AUDIT" else "#e0473e"
            st.markdown(f'<div class="feat-num" style="color:{color}">#{num}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="feat-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="feat-desc">{desc}</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("#### Example Topics")
    st.code("Analyze find_median.py, write unit tests, review and save them as test_median.py", language=None)
    st.code("Query the knowledge base from 'Data Engineering for Cybersecurity' and build a secure pipeline", language=None)
    st.code("Research the latest LangGraph features online and write a Markdown summary report", language=None)
    st.code("Audit the uploaded files for security vulnerabilities and generate an OWASP report", language=None)


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greeted = False

# ── Display history ────────────────────────────────────────────────────────────
display_chat_messages()

# ── Greet user on first load ───────────────────────────────────────────────────
if not st.session_state.greeted:
    with st.chat_message("assistant", avatar="▪️"):
        intro = "**SYSTEM ONLINE.** Orchestrator ready. Enter your topic to begin."
        st.markdown(intro)
    st.session_state.messages.append({"role": "assistant", "content": intro, "blocks": []})
    st.session_state.greeted = True


# ── Example prompt buttons (2 rows × 3) ───────────────────────────────────────
example_prompts = [
    "Analyze `find_median.py`, write unit tests, review them, save as `test_median.py`",
    "Query the knowledge base from 'Data Engineering for Cybersecurity' and build a secure pipeline",
    "Search the web for the latest LangGraph features and write a Markdown report",
    "Research QuickSort & MergeSort from the knowledge base, implement and save to `sorting.py`",
    "Audit the uploaded files for security vulnerabilities and generate an OWASP report",
    "Pentest the target URL for common web vulnerabilities and write a security report",
]
example_help = [
    "Uses analysis + coding + review + file_writer workers",
    "Uses research (RAG) + coding + file_writer workers",
    "Uses research (web) + writing workers",
    "Uses research (RAG) + coding + review + file_writer workers",
    "Uses security_audit workers — upload files first in sidebar",
    "Uses security_audit + research workers — paste URL in sidebar first",
]

button_pressed = ""
row1 = st.columns(3)
row2 = st.columns(3)
for i in range(3):
    if row1[i].button(example_prompts[i], help=example_help[i], use_container_width=True):
        button_pressed = example_prompts[i]
for i in range(3):
    if row2[i].button(example_prompts[i+3], help=example_help[i+3], use_container_width=True):
        button_pressed = example_prompts[i+3]

st.divider()


# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := (st.chat_input("What do you want to orchestrate?") or button_pressed):

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt, "blocks": []})

    langgraph_app = load_app()
    blocks_for_history = []
    workers_for_history = []
    final_report_for_history = None

    # Construct chat history for the graph
    chat_history = []
    # Skip the very first "SYSTEM ONLINE" greet message and the latest prompt we just appended
    for msg in st.session_state.messages[1:-1]:
        chat_history.append({"role": msg["role"], "content": msg.get("content", "")})
    
    # Inject uploaded context (files/URL) if available
    uploaded_context = st.session_state.get("uploaded_context", "")
    graph_inputs = {
        "topic": prompt.strip(),
        "messages": chat_history,
        "uploaded_context": uploaded_context
    }

    with st.chat_message("assistant", avatar="▪️"):
        status_placeholder = st.empty()
        status_placeholder.markdown("`[ planning ]` building the task graph…")

        for event in langgraph_app.stream(graph_inputs):
            for node, output in event.items():

                if node == "human_approval":
                    continue

                # ── Orchestrator ──────────────────────────────────────────────
                elif node == "orchestrator":
                    plan = output.get("plan")
                    if plan:
                        status_placeholder.markdown("`[ plan ready ]` dispatching workers…")
                        rows = "".join([
                            f'<div style="padding:.3rem 0;color:#c7cdc8;font-size:.87rem;'
                            f'border-bottom:1px solid #1e2320;font-family:\'JetBrains Mono\',monospace">'
                            f'<span class="badge">{t.worker_type}</span>'
                            f'<b>[{t.task_id}]</b> {t.description}'
                            f'{"  &larr; " + ", ".join(t.dependencies) if t.dependencies else ""}'
                            f'</div>'
                            for t in plan.tasks
                        ])
                        block = (
                            f'<div class="plan-card">'
                            f'<div class="section-label plan-label">PLAN</div>'
                            f'<p style="color:#8a938c;font-size:.85rem;margin:.0 0 .6rem 0;'
                            f'font-family:\'JetBrains Mono\',monospace">'
                            f'{plan.overall_strategy or ""}</p>'
                            f'{rows}</div>'
                        )
                        st.markdown(block, unsafe_allow_html=True)
                        blocks_for_history.append(block)

                # ── Worker ────────────────────────────────────────────────────
                elif node == "worker":
                    for res in output.get("results", []):
                        tid   = res.get("task_id", "")
                        wtype = res.get("worker_type", "")
                        out   = res.get("output", "")
                        status_placeholder.markdown(f"`[ worker {tid} ]` {wtype} — done")
                        if show_workers:
                            with st.expander(f"[{tid}] {wtype}", expanded=False):
                                card_class = "security-card" if wtype == "security_audit" else "worker-card"
                                label_class = "security-label" if wtype == "security_audit" else "work-label"
                                block = (
                                    f'<div class="{card_class}">'
                                    f'<div class="section-label {label_class}">{wtype.upper()} — {tid}</div>'
                                    f'<pre style="white-space:pre-wrap;color:#dfe4e0;font-size:.83rem;margin:0;'
                                    f'font-family:\'JetBrains Mono\',monospace">{out}</pre>'
                                    f'</div>'
                                )
                                st.markdown(block, unsafe_allow_html=True)
                                workers_for_history.append({"tid": tid, "wtype": wtype, "block": block})

                # ── Synthesizer ───────────────────────────────────────────────
                elif node == "synthesizer":
                    final = output.get("final_report", "")
                    status_placeholder.markdown("`[ synthesizing ]` writing final report…")

                    msg_placeholder = st.empty()
                    typed = ""
                    words = final.split()
                    delay = 1.0 / max(typing_speed, 1)
                    for word in words:
                        typed += word + " "
                        msg_placeholder.markdown(typed + "▌")
                        time.sleep(delay)
                    msg_placeholder.markdown(typed)

                    final_report_for_history = final

                    st.download_button(
                        "Download final report (.md)",
                        data=final,
                        file_name="final_report.md",
                        mime="text/markdown",
                        key="dl_live_run"
                    )

        status_placeholder.markdown("`[ done ]` all tasks complete")

    st.session_state.messages.append({
        "role": "assistant",
        "content": "**Orchestration complete.**",
        "blocks": blocks_for_history,
        "workers": workers_for_history,
        "final_report": final_report_for_history
    })
    st.rerun()