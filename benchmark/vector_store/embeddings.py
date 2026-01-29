"""Embedding model wrapper using HuggingFace transformers."""

from typing import final

import torch
from transformers import AutoModel, AutoTokenizer

from benchmark.vector_store.base import Encoder


@final
class GemmaEmbedder(Encoder):
    """
    Text encoder using google/embeddinggemma-300m model.

    Generates 768-dimensional embeddings optimized for
    semantic similarity and retrieval tasks.

    Example:
        >>> embedder = GemmaEmbedder()
        >>> vector = embedder.encode("Hello world")
        >>> len(vector)
        768
    """

    def __init__(self, name: str = "google/embeddinggemma-300m"):
        """
        Initialize the embedding model.

        Args:
            name: HuggingFace model identifier
        """
        self._name = name
        self._tokenizer = AutoTokenizer.from_pretrained(name)
        self._model = AutoModel.from_pretrained(name)
        self._model.eval()

    def encode(self, text: str) -> list[float]:
        """
        Transform text into 768-dimensional embedding.

        Args:
            text: Input text to encode

        Returns:
            Dense vector representation as list of floats
        """
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
            padding=True,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
        return embedding.tolist()

    def dimension(self) -> int:
        """
        Return embedding dimensionality.

        Returns:
            768 for embeddinggemma-300m
        """
        return self._model.config.hidden_size
