"""Chunking and Chroma collection access for Lucy's note embeddings."""
from functools import lru_cache

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import get_settings

COLLECTION_NAME = "notes"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ~0.75 words per token in English, so 300-500 tokens is roughly this many words.
CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


@lru_cache
def get_collection() -> chromadb.Collection:
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding_function)


def add_document(path: str, text: str) -> int:
    """Chunk, embed, and store a document's text in Chroma, keyed by its path. Returns the chunk count."""
    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection = get_collection()
    ids = [f"{path}::{i}" for i in range(len(chunks))]
    metadatas = [{"path": path, "filename": path.split("/")[-1], "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def remove_document(path: str) -> None:
    """Remove all chunks for a document from Chroma, keyed by the same path used to add it.

    Deleting the underlying note/file alone leaves it searchable — Chroma
    has no other way to know it's gone.
    """
    get_collection().delete(where={"path": path})
