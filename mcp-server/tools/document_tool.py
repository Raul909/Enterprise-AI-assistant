from vector_store.search import semantic_search

def search_documents(query: str, department: str):
    """
    Search documents with semantic similarity
    """
    results = semantic_search(query, department)
    return {
        "results": results
    }
