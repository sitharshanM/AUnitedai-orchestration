# AUnitedAI Orchestrator

A powerful, open-source multi-agent system built with **LangGraph** and **Streamlit**. 

AUnitedAI acts as your personal AI task force. Give it a complex prompt, and it automatically breaks the work into sub-tasks, dispatches specialized worker agents to execute them, runs a self-correction critic loop, and synthesizes a final Markdown report.

![AUnitedAI Interface](hero_bg.png) 
*(Screenshot placeholder - replace with actual UI screenshot)*

## 🌟 Key Features

- **Dynamic Task Planning**: The Orchestrator agent interprets your prompt and dynamically builds a LangGraph execution graph of sub-tasks.
- **Specialized Worker Agents**: Includes dedicated agents for `Research`, `Coding`, `Analysis`, `Writing`, `Review`, and `File Writing`.
- **Multi-Backend LLM Support**: seamlessly integrates with **Gemini**, **Groq**, and local **Ollama** models. 
- **No-Code Configuration Dashboard**: A built-in Streamlit dashboard allows you to hot-swap models, change backends, and inject custom system prompts for every individual worker—without touching a line of code.
- **RAG / Knowledge Base**: Built-in retrieval augmented generation using `nomic-embed-text`, capable of querying local PDFs and Markdown files.
- **Terminal-Style UI**: A sleek, dark-mode Streamlit interface (Hermes-inspired) featuring live streaming output, typing animations, and persistent native Markdown rendering.

## ⚙️ Architecture

AUnitedAI uses a hub-and-spoke multi-agent architecture powered by LangGraph:

1. **Orchestrator**: Plans the execution and assigns dependencies.
2. **Workers**: Execute tasks using specific tools (Web Search, Webpage Fetch, File I/O, RAG).
3. **Critic**: Evaluates worker outputs and demands revisions if they fail expectations.
4. **Synthesizer**: Compiles all approved worker outputs into a final, downloadable Markdown report.

## 🚀 Quickstart

### Prerequisites

1. **Python 3.10+**
2. **Ollama** (for local models)
3. **API Keys** for Gemini and Groq (if using cloud backends)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/AUnitedAI.git
   cd AUnitedAI
   ```

2. **Install dependencies:**
   We recommend using `uv` for fast dependency management, or standard `pip`.
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_key_here
   GROQ_API_KEY=your_groq_key_here
   ```

4. **Pull Local Models (Optional):**
   If you plan to use Ollama for specific workers (configured via the Dashboard):
   ```bash
   ollama pull qwen2.5
   ollama pull llama3.1
   ollama pull devstral:latest
   ollama pull qwen2.5-coder:7b
   ```

### Running the App

Start the Streamlit GUI:

```bash
streamlit run gui.py
```
*(Or `uv run streamlit run gui.py` if using uv)*

## 🎛️ Worker Configuration

You don't need to edit code to change how the agents behave. 
Click the **⚙️ Configure Workers** button in the sidebar of the GUI to open the **Worker Configuration Dashboard**. 

Here you can:
- Switch an agent's backend (e.g., move Research from Gemini to Groq).
- Update the Model Name (e.g., `llama-3.3-70b-versatile`).
- Tweak the temperature.
- Inject Custom System Instructions (e.g., *"Always write Python 3.12 code"*).

Your settings are saved locally to `worker_config.json` and persist across sessions.

## 🛠️ Tools Included

The agents have access to the following LangChain tools:
- `DuckDuckGoSearchResults`: For real-time web research.
- `fetch_webpage`: For scraping specific URLs.
- `query_knowledge_base`: For RAG over your local documents.
- `read_file_tool` & `write_file_tool`: For interacting with your local filesystem.

## 📝 License

MIT License
