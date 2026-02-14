"""
Document ingestion for vector store.
Chunks documents and creates FAISS embeddings.
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any

import faiss
from sentence_transformers import SentenceTransformer


# Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "."))
CHUNK_SIZE = 500  # tokens approximate
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Approximate size of each chunk in words
        overlap: Number of overlapping words between chunks
    
    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def ingest_documents(
    documents: List[Dict[str, Any]],
    model_name: str = EMBEDDING_MODEL,
    save_path: Path = VECTOR_STORE_PATH
) -> Dict[str, Any]:
    """
    Ingest documents into the vector store.
    
    Args:
        documents: List of documents with 'content', 'title', 'department' fields
        model_name: Name of the sentence transformer model
        save_path: Path to save the index
    
    Returns:
        Stats about the ingestion
    """
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Process documents
    processed_docs = []
    all_chunks = []
    
    for doc in documents:
        content = doc.get("content", "")
        title = doc.get("title", "Untitled")
        department = doc.get("department", "general")
        source = doc.get("source", "unknown")
        
        # Chunk the content
        chunks = chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            processed_docs.append({
                "content": chunk,
                "title": f"{title} (Part {i+1})" if len(chunks) > 1 else title,
                "department": department,
                "source": source,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
            all_chunks.append(chunk)
    
    print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
    
    # Create embeddings
    print("Creating embeddings...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"Created FAISS index with {index.ntotal} vectors")
    
    # Save to disk
    save_path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(save_path / "index.faiss"))
    
    with open(save_path / "docs.pkl", "wb") as f:
        pickle.dump(processed_docs, f)
    
    print(f"Saved index to {save_path}")
    
    return {
        "documents_processed": len(documents),
        "chunks_created": len(all_chunks),
        "embedding_dimension": dimension,
        "index_path": str(save_path / "index.faiss")
    }


def ingest_from_directory(
    directory: str,
    extensions: List[str] = [".txt", ".md"],
    department: str = "general"
) -> Dict[str, Any]:
    """
    Ingest all documents from a directory.
    
    Args:
        directory: Path to directory containing documents
        extensions: File extensions to include
        department: Department to tag documents with
    
    Returns:
        Ingestion stats
    """
    documents = []
    dir_path = Path(directory)
    
    for ext in extensions:
        for file_path in dir_path.glob(f"**/*{ext}"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                documents.append({
                    "content": content,
                    "title": file_path.stem,
                    "department": department,
                    "source": str(file_path)
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    if documents:
        return ingest_documents(documents)
    else:
        return {"error": "No documents found"}


# Example usage and demo data
if __name__ == "__main__":
    # Demo documents for testing
    demo_docs = [
        {
            "title": "Company Vacation Policy",
            "content": """Our company provides competitive vacation benefits to all employees. 
            Full-time employees receive 15 days of paid vacation per year, increasing to 20 days after 5 years of service.
            Vacation requests should be submitted at least 2 weeks in advance through the HR portal.
            Unused vacation days can be carried over to the next year, up to a maximum of 5 days.
            For questions about vacation policy, contact HR at hr@company.com.""",
            "department": "hr",
            "source": "hr_policies.pdf"
        },
        {
            "title": "Remote Work Guidelines",
            "content": """Employees may work remotely up to 3 days per week with manager approval.
            Remote work requires a reliable internet connection and a dedicated workspace.
            All remote employees must be available during core hours (10am-4pm local time).
            VPN connection is required when accessing company resources remotely.
            Equipment needs should be discussed with IT department.""",
            "department": "hr",
            "source": "remote_work_policy.pdf"
        },
        {
            "title": "Code Review Guidelines",
            "content": """All code changes must go through peer review before merging.
            PRs should be small and focused on a single feature or bug fix.
            Reviewers should provide feedback within 24 hours.
            At least one approval is required before merging.
            Use conventional commits for commit messages.
            Run all tests locally before submitting a PR.""",
            "department": "engineering",
            "source": "engineering_handbook.md"
        },
        {
            "title": "Security Best Practices",
            "content": """Never commit secrets or API keys to version control.
            Use environment variables for sensitive configuration.
            Enable 2FA on all company accounts.
            Report security concerns to security@company.com immediately.
            Regular security training is required for all employees.
            Encrypt sensitive data at rest and in transit.""",
            "department": "engineering",
            "source": "security_guidelines.md"
        }
    ]
    
    result = ingest_documents(demo_docs)
    print(f"\nIngestion complete: {result}")
