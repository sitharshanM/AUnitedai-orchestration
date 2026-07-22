"""
gui.py  -  Chat-style Streamlit GUI for the AUnitedAI Multi-Agent Orchestrator.
Terminal / technical aesthetic (mono labels, thin borders, restrained palette).

Run with:  streamlit run gui.py
"""

import time
import streamlit as st
import os
import base64
import dotenv
from dotenv import load_dotenv
from orchestrator import config

load_dotenv()

# Copy all Streamlit secrets to environment variables so LangChain can access them
try:
    if hasattr(st, "secrets"):
        try:
            for key, val in st.secrets.items():
                os.environ[key] = str(val)
        except Exception:
            pass
except Exception:
    pass

current_config = config.load_config()

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def check_password():
    """Returns True if the user had the correct password."""
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        try:
            app_password = st.secrets.get("APP_PASSWORD")
        except Exception:
            pass
    if not app_password:
        return True

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password_input"] == app_password:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # remove from session state
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show password input
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 35vh; flex-direction: column;">
            <div style="background: #101113; border: 1px solid #1e2320; border-top: 3px solid #ff2e93; padding: 2.5rem; border-radius: 8px; width: 400px; text-align: center;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #7a8a7d; margin-bottom: 0.5rem;">AUNITEDAI SECURE ACCESS</div>
                <h3 style="font-family: 'JetBrains Mono', monospace; color: #e8ece8; margin-top: 0; font-size: 1.5rem;">Password Required</h3>
                <p style="color: #8a938c; font-size: 0.85rem; margin-bottom: 0;">This orchestrator is password-protected to prevent unauthorized code execution and filesystem actions.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the input using streamlit columns
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.text_input(
                "Enter Password:",
                type="password",
                on_change=password_entered,
                key="password_input",
                label_visibility="collapsed"
            )
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 35vh; flex-direction: column;">
            <div style="background: #101113; border: 1px solid #1e2320; border-top: 3px solid #e0473e; padding: 2.5rem; border-radius: 8px; width: 400px; text-align: center;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #e0473e; margin-bottom: 0.5rem;">ACCESS DENIED</div>
                <h3 style="font-family: 'JetBrains Mono', monospace; color: #e8ece8; margin-top: 0; font-size: 1.5rem;">Password Incorrect</h3>
                <p style="color: #8a938c; font-size: 0.85rem; margin-bottom: 0;">Please check your APP_PASSWORD configuration and try again.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.text_input(
                "Enter Password:",
                type="password",
                on_change=password_entered,
                key="password_input",
                label_visibility="collapsed"
            )
        return False
    else:
        return True

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AUnitedAI Orchestrator",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not check_password():
    st.stop()

bg_css = ".stApp { background:#0a0a0c; color:#f4f4f5; }"
if os.path.exists("assets/hero_bg.png"):
    bg_img = get_base64_image("assets/hero_bg.png")
    bg_css = f"""
    .stApp {{
        background: url(data:image/png;base64,{bg_img}) no-repeat center center fixed !important;
        background-size: auto 70% !important;
        background-color: #0a0a0c !important;
    }}
    """

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"<style>{bg_css}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family:'Inter',sans-serif; color:#f4f4f5; }
h1,h2,h3, .mono { font-family:'Cinzel','Times New Roman',serif; text-transform:uppercase; color:#ffffff; }

/* Eyebrow tag */
.eyebrow{
    display:inline-block; font-family:'JetBrains Mono',monospace;
    font-size:.72rem; letter-spacing:.18em; text-transform:uppercase;
    color:#ff3344; border:1px solid rgba(255,255,255,0.25); border-radius:2px;
    padding:.25rem .6rem; margin-bottom:1rem; font-weight:700;
}
.eyebrow .dot{ color:#ff3344; }

/* Hero banner */
.hero{
    background:#ffffff; border:1px solid #ffffff; border-radius:2px;
    padding:2rem 2.2rem; margin-bottom:1.4rem; color:#0a0a0c;
}
.hero h1{
    font-family:'Cinzel',serif; font-size:2.8rem; font-weight:900; margin:0; line-height:1.0;
    color:#0a0a0c; letter-spacing:.12em; text-transform:uppercase;
}
.hero h1 .accent{ color:#ff3344; }
.hero p{ color:#3f3f46; margin:.6rem 0 0 0; font-size:.85rem; font-family:'JetBrains Mono',monospace; font-weight:600; }

/* Node cards inside chat bubbles */
.plan-card{
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.2); border-left:5px solid #00ff66;
    border-radius:2px; padding:.9rem 1.1rem; margin:.5rem 0; color:#ffffff;
}
.worker-card{
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.2); border-left:5px solid #00f0ff;
    border-radius:2px; padding:.9rem 1.1rem; margin:.5rem 0; color:#ffffff;
}
.report-card{
    background:#ffffff; border:1px solid #ffffff; border-left:5px solid #0a0a0c;
    border-radius:2px; padding:1.2rem; margin:.5rem 0;
    white-space:pre-wrap; font-size:.9rem; line-height:1.7; color:#0a0a0c;
}
.badge{
    display:inline-block; border-radius:2px; padding:.15rem .55rem;
    font-size:.68rem; font-weight:700; margin-right:.4rem;
    font-family:'JetBrains Mono',monospace; letter-spacing:.05em;
    background:rgba(0,255,102,0.2); color:#00ff66;
    border:1px solid #00ff66; text-transform:uppercase;
}
.badge.worker{
    background:rgba(0,240,255,0.2); color:#00f0ff;
    border:1px solid #00f0ff;
}
.badge.security{
    background:rgba(251,191,36,0.2); color:#fbbf24;
    border:1px solid #fbbf24;
}
.security-card{
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.2); border-left:5px solid #fbbf24;
    border-radius:2px; padding:.9rem 1.1rem; margin:.5rem 0; color:#ffffff;
}
.section-label{
    font-family:'JetBrains Mono',monospace;
    font-size:.75rem; font-weight:700; letter-spacing:.14em;
    text-transform:uppercase; margin-bottom:.5rem;
}
.plan-label  { color:#00ff66; }
.work-label  { color:#00f0ff; }
.report-label{ color:#0a0a0c; font-weight:900; }
.security-label{ color:#fbbf24; }

/* Numbered feature rows */
.feat-num{
    font-family:'JetBrains Mono',monospace; font-size:.75rem; color:#ff3344;
    letter-spacing:.08em; font-weight:700;
}
.feat-title{ font-weight:700; color:#ffffff; margin:.1rem 0 .2rem 0; font-family:'Cinzel',serif; text-transform:uppercase; }
.feat-desc{ color:#a1a1aa; font-size:.85rem; }

/* Sidebar */
section[data-testid="stSidebar"]>div{ background:#121216; border-right:1px solid rgba(255,255,255,0.2); color:#ffffff; }
section[data-testid="stSidebar"] .stMarkdownContainer { font-family:'JetBrains Mono',monospace; color:#ffffff; }

hr{ border-color:rgba(255,255,255,0.2) !important; }

/* Buttons */
.stButton>button{
    background:#ff3344; border:1px solid #ff3344; color:#ffffff;
    font-family:'JetBrains Mono',monospace; font-size:.78rem; font-weight:700;
    border-radius:2px; text-transform:uppercase; letter-spacing:.08em;
}
.stButton>button:hover{ background:#ff5566; border-color:#ff5566; color:#ffffff; }
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

    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        try:
            app_password = st.secrets.get("APP_PASSWORD")
        except Exception:
            pass
    if not app_password:
        st.warning("⚠️ **Security Warning**: `APP_PASSWORD` is not set. Exposing this app publicly allows unauthorized file operations on your machine.")

    st.divider()
    st.markdown("**SECURITY AUDIT INPUT**")
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
    st.markdown("**⚡ ECC TOKEN BUDGET & DEPTH**")
    token_depth = st.selectbox(
        "Response Depth (ECC TBA):",
        ["Auto (50% Moderate)", "25% Essential (Brief)", "50% Moderate (Balanced)", "75% Detailed (Full)", "100% Exhaustive (Deep Dive)"],
        index=0,
        help="Controls output depth and token consumption budget."
    )
    st.session_state.token_depth = token_depth

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
    st.markdown("## 🔑 API Keys Management")
    st.markdown("Enter your API keys here. They will be saved securely to `.env`.")
    
    with st.form("api_keys_form"):
        c1, c2 = st.columns(2)
        google_key = c1.text_input("Google API Key", value=os.environ.get("GOOGLE_API_KEY", ""), type="password")
        groq_key = c2.text_input("Groq API Key", value=os.environ.get("GROQ_API_KEY", ""), type="password")
        
        c3, c4 = st.columns(2)
        openai_key = c3.text_input("OpenAI API Key", value=os.environ.get("OPENAI_API_KEY", ""), type="password")
        anthropic_key = c4.text_input("Anthropic API Key", value=os.environ.get("ANTHROPIC_API_KEY", ""), type="password")
        
        c5, c6 = st.columns(2)
        deepseek_key = c5.text_input("DeepSeek API Key", value=os.environ.get("DEEPSEEK_API_KEY", ""), type="password")
        together_key = c6.text_input("TogetherAI API Key", value=os.environ.get("TOGETHER_API_KEY", ""), type="password")
        
        c7, c8 = st.columns(2)
        custom_key = c7.text_input("Custom API Key (OpenAI-compatible)", value=os.environ.get("CUSTOM_API_KEY", ""), type="password")
        custom_url = c8.text_input("Custom API Base URL", value=os.environ.get("CUSTOM_BASE_URL", ""), placeholder="e.g. https://api.openai.com/v1")
        
        if st.form_submit_button("💾 Save API Keys"):
            env_file = dotenv.find_dotenv()
            if not env_file:
                env_file = ".env"
                open(env_file, 'a').close()
            
            dotenv.set_key(env_file, "GOOGLE_API_KEY", google_key)
            dotenv.set_key(env_file, "GROQ_API_KEY", groq_key)
            dotenv.set_key(env_file, "OPENAI_API_KEY", openai_key)
            dotenv.set_key(env_file, "ANTHROPIC_API_KEY", anthropic_key)
            dotenv.set_key(env_file, "DEEPSEEK_API_KEY", deepseek_key)
            dotenv.set_key(env_file, "TOGETHER_API_KEY", together_key)
            dotenv.set_key(env_file, "CUSTOM_API_KEY", custom_key)
            dotenv.set_key(env_file, "CUSTOM_BASE_URL", custom_url)
            
            os.environ["GOOGLE_API_KEY"] = google_key
            os.environ["GROQ_API_KEY"] = groq_key
            os.environ["OPENAI_API_KEY"] = openai_key
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key
            os.environ["TOGETHER_API_KEY"] = together_key
            os.environ["CUSTOM_API_KEY"] = custom_key
            os.environ["CUSTOM_BASE_URL"] = custom_url
            
            st.success("API Keys saved to .env and loaded into environment.")
            time.sleep(1)
            st.rerun()

    st.markdown("---")
    st.markdown("## ⚙️ Worker Configuration Dashboard")
    st.markdown("Customize the models, backends, and instructions for each LangGraph agent.")
    
    with st.form("worker_config_form"):
        new_config = {}
        for w_key, w_val in current_config.items():
            st.markdown(f"#### {w_key.upper()}")
            c1, c2, c3 = st.columns([1, 2, 1])
            backends_list = ["Ollama", "Gemini", "Groq", "OpenAI", "Anthropic", "DeepSeek", "TogetherAI", "Custom API"]
            current_backend = w_val["backend"] if w_val["backend"] in backends_list else "Ollama"
            backend = c1.selectbox("Backend", backends_list, index=backends_list.index(current_backend), key=f"{w_key}_backend")
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