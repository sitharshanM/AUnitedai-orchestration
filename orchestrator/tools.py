from langchain_core.tools import tool

@tool
def write_file_tool(file_path: str, content: str) -> str:
    """Writes the specified content to a file at the given file_path.
    Use this tool to save code, reports, or results to the filesystem.
    """
    import os
    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote file to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def read_file_tool(file_path: str) -> str:
    """Reads the contents of a file at the given file_path.
    Use this tool to view code, reports, or results from the filesystem.
    """
    import os
    try:
        if not os.path.exists(file_path):
            return f"Error: File does not exist at {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def fetch_webpage_tool(url: str) -> str:
    """Fetches the content of a web page at the given URL and returns it as plain text.
    Use this tool to read detailed article content after finding links in search results.
    """
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Return first 3000 characters to avoid context overflow
        if len(text) > 3000:
            return text[:3000] + "\n... [Content truncated to 3000 characters] ..."
        return text
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

@tool
def query_knowledge_base(query: str) -> str:
    """Queries the local knowledge base using semantic vector search.
    Use this tool to find information from local company documents, guides, policies, or project files.
    """
    import os
    from langchain_community.vectorstores import Chroma
    from langchain_ollama import OllamaEmbeddings
    
    CHROMA_DB_DIR = "./chroma_db"
    EMBEDDING_MODEL = "nomic-embed-text"
    
    if not os.path.exists(CHROMA_DB_DIR):
        return "Error: Local knowledge base vector database does not exist. Please index documents first."
        
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        results = db.similarity_search(query, k=3)
        
        if not results:
            return "No matching information found in the local knowledge base."
            
        combined_text = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page")
            source_info = f"{source} (Page {page})" if page else source
            combined_text.append(f"--- Document Chunk {i+1} (Source: {source_info}) ---\n{doc.page_content}")
            
        return "\n\n".join(combined_text)
    except Exception as e:
        return f"Error querying local knowledge base: {str(e)}"
