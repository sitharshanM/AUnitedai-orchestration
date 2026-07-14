import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# Configuration
KNOWLEDGE_BASE_DIR = "./knowledge_base"
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"

def index_documents():
    print(f"Checking for documents in '{KNOWLEDGE_BASE_DIR}'...")
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
        print(f"Created '{KNOWLEDGE_BASE_DIR}' directory. Please add .txt or .md files there and re-run.")
        return

    # 1. Read files
    documents = []
    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            if file.endswith((".txt", ".md", ".py")):
                file_path = os.path.join(root, file)
                print(f"Loading file: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    documents.append({
                        "content": text,
                        "metadata": {"source": file}
                    })
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
            elif file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"Loading PDF: {file_path}")
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    pages = loader.load()
                    for page in pages:
                        documents.append({
                            "content": page.page_content,
                            "metadata": {"source": file, "page": page.metadata.get("page", 0) + 1}
                        })
                except Exception as e:
                    print(f"Error loading PDF {file_path}: {e}")

    if not documents:
        print("No documents found to index.")
        return

    # 2. Chunk text
    print(f"Splitting {len(documents)} documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    texts = []
    metadatas = []
    for doc in documents:
        chunks = text_splitter.split_text(doc["content"])
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append(doc["metadata"])

    print(f"Created {len(texts)} text chunks.")

    # 3. Create embeddings and store in Chroma
    print(f"Initializing embeddings model '{EMBEDDING_MODEL}'...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    print(f"Generating embeddings and saving database to '{CHROMA_DB_DIR}'...")
    try:
        # Create and persist the database
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            persist_directory=CHROMA_DB_DIR
        )
        print("Indexing completed successfully!")
    except Exception as e:
        print(f"Error creating Chroma database: {e}")

if __name__ == "__main__":
    index_documents()
