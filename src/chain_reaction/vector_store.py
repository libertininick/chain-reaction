"""Utilities for vector storage using ChromaDB."""

from collections.abc import Callable, Mapping
from os import PathLike
from pathlib import Path
from types import MappingProxyType
from typing import Final

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

# Immutable map of embedding model name → embedding function factory
EMBEDDING_MODEL_REGISTRY: Final[Mapping[str, Callable[[str | None], Embeddings]]] = MappingProxyType({
    "huggingface": lambda _: HuggingFaceEmbeddings(model_name="multi-qa-mpnet-base-dot-v1"),
    "openai-small": lambda api_key: OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key),  # type: ignore[unknown-argument]
    "openai-large": lambda api_key: OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key),  # type: ignore[unknown-argument]
})


def init_vector_store(
    *,
    collection_name: str,
    persist_directory: str | PathLike | None,
    embedding_model_name: str,
    api_key: str | None = None,
) -> Chroma:
    """Initialize a Chroma vectorstore.

    Args:
        collection_name (str): Name of the Chroma collection.
        persist_directory (str | PathLike | None): Path to the persisted Chroma database directory.
            If `None` will be in memory.
        embedding_model_name (str): Name of embedding model to use.
        api_key (str | None, optional): API key for embedding model. Defaults to None.

    Returns:
        Chroma: Initialized LangChain Chroma vectorstore.

    Raises:
        ValueError: If a valid embedding model is not provided.
    """
    if embedding_model_name not in EMBEDDING_MODEL_REGISTRY:
        raise ValueError(
            f"Unknown embedding model '{embedding_model_name}'. Known models: {list(EMBEDDING_MODEL_REGISTRY.keys())}"
        )

    return Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_directory) if persist_directory is not None else None,
        embedding_function=EMBEDDING_MODEL_REGISTRY[embedding_model_name](api_key),
        collection_metadata={"embedding_model": embedding_model_name},
    )


def load_vector_store(
    *,
    collection_name: str,
    persist_directory: str | Path,
    api_key: str | None = None,
) -> Chroma:
    """Load a Chroma vectorstore, inferring the embedding function from collection metadata.

    Args:
        collection_name (str): Name of the Chroma collection.
        persist_directory (str | Path): Path to the persisted Chroma database.
        api_key (str | None, optional): API key for embedding model. Defaults to None.

    Returns:
        Chroma: Initialized LangChain Chroma vectorstore.

    Raises:
        FileNotFoundError: If `persist_directory` doesn't exist.
        ValueError: If a valid embedding model is not associated with the collection.
    """
    if not Path(persist_directory).exists():
        raise FileNotFoundError(f"{persist_directory} doesn't exist")

    # Peek at metadata before initializing LangChain wrapper
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_collection(collection_name)

    # Get embedding model name from collection metadata
    if (embedding_model_name := collection.metadata.get("embedding_model")) is None:
        raise ValueError(f"Collection '{collection_name}' has no 'embedding_model' metadata.")

    return init_vector_store(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_model_name=embedding_model_name,
        api_key=api_key,
    )
