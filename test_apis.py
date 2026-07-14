from dotenv import load_dotenv
load_dotenv()
import os

print('=== API KEY CHECK ===')
google_key = os.environ.get('GOOGLE_API_KEY', '')
groq_key   = os.environ.get('GROQ_API_KEY', '')
print('GOOGLE_API_KEY :', 'SET (' + google_key[:8] + '...)' if google_key else 'NOT SET')
print('GROQ_API_KEY   :', 'SET (' + groq_key[:8] + '...)' if groq_key else 'NOT SET')

print()
print('=== GEMINI TEST (Research Worker) ===')
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', temperature=0)
    resp = llm.invoke('Say CONNECTED in one word only.')
    print('Gemini 2.0 Flash: OK ->', resp.content.strip())
except Exception as e:
    print('Gemini FAILED:', e)

print()
print('=== GROQ TEST (Writing Worker) ===')
try:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model='llama-3.3-70b-versatile', temperature=0)
    resp = llm.invoke('Say CONNECTED in one word only.')
    print('Groq llama-3.3-70b: OK ->', resp.content.strip())
except Exception as e:
    print('Groq FAILED:', e)

print()
print('=== OLLAMA TEST (Analysis / Review / Orchestrator) ===')
try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model='llama3.1', temperature=0)
    resp = llm.invoke('Say CONNECTED in one word only.')
    print('Ollama llama3.1: OK ->', resp.content.strip())
except Exception as e:
    print('Ollama llama3.1 FAILED:', e)

print()
print('=== DUCKDUCKGO TEST (Research Tool) ===')
try:
    from langchain_community.tools import DuckDuckGoSearchResults
    tool = DuckDuckGoSearchResults(max_results=1)
    result = tool.invoke('LangGraph')
    print('DuckDuckGo: OK ->', str(result)[:80] + '...')
except Exception as e:
    print('DuckDuckGo FAILED:', e)

print()
print('=== CHROMA RAG TEST (Knowledge Base) ===')
if os.path.exists('./chroma_db'):
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        embeddings = OllamaEmbeddings(model='nomic-embed-text')
        db = Chroma(persist_directory='./chroma_db', embedding_function=embeddings)
        results = db.similarity_search('security pipeline', k=1)
        print('Chroma RAG: OK ->', len(results), 'result(s) returned')
        if results:
            print('  Source:', results[0].metadata.get('source', 'unknown'))
    except Exception as e:
        print('Chroma RAG FAILED:', e)
else:
    print('Chroma RAG: SKIPPED - chroma_db not found, run: python index_docs.py')
