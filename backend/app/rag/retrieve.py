"""Query Chroma for the chunks most relevant to a question."""
from app.rag.embed import get_collection

DEFAULT_TOP_K = 4


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[str]:
    """Return the top-k document chunks most relevant to the query."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    return results["documents"][0]
