"""
File Compass - Embedder Module
Handles embedding generation via Ollama's nomic-embed-text model.
Adapted from Tool Compass embedder.
"""

import httpx
import numpy as np
from typing import List, Optional
import asyncio
import logging

from .config import get_config

logger = logging.getLogger(__name__)


class Embedder:
    """
    Async embedder using Ollama's nomic-embed-text model.
    Optimized for file content embedding with batching support.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0  # Longer timeout for batch operations
    ):
        config = get_config()
        self.base_url = base_url or config.ollama_url
        self.model = model or config.embedding_model
        self.dim = config.embedding_dim
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return any(self.model in m for m in models)
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text (document/file content).

        Uses chunk averaging for long texts per 2026 best practices:
        - Ollama limits nomic-embed-text to 2048 tokens (not 8192)
        - Split long texts, embed chunks, weighted-average results

        Args:
            text: Text to embed

        Returns:
            numpy array of shape (dim,)
        """
        # Ollama's actual limit is ~2048 tokens, not 8192
        # Conservative char limit: ~1500 chars ≈ 400-500 tokens (safe margin)
        MAX_CHARS = 1500

        if len(text) <= MAX_CHARS:
            return await self._embed_single(text)

        # Chunk averaging for long texts (OpenAI Cookbook best practice)
        chunks = self._split_into_chunks(text, MAX_CHARS, overlap=100)
        embeddings = []
        weights = []

        for chunk in chunks:
            emb = await self._embed_single(chunk)
            embeddings.append(emb)
            weights.append(len(chunk))  # Weight by chunk size

        # Weighted average
        weights = np.array(weights, dtype=np.float32)
        weights = weights / weights.sum()

        avg_embedding = np.zeros_like(embeddings[0])
        for emb, w in zip(embeddings, weights):
            avg_embedding += w * emb

        # Normalize final result
        norm = np.linalg.norm(avg_embedding)
        if norm > 0:
            avg_embedding = avg_embedding / norm

        return avg_embedding

    def _split_into_chunks(self, text: str, max_chars: int, overlap: int = 100) -> list:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
            if start < 0:
                start = 0
            if end >= len(text):
                break
        return chunks if chunks else [text[:max_chars]]

    async def _embed_single(self, text: str, max_retries: int = 3) -> np.ndarray:
        """Embed a single short text chunk with retry logic."""
        client = await self._get_client()

        # Document prefix for retrieval (nomic-embed-text recommendation)
        prefixed_text = f"search_document: {text}"

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    "/api/embed",
                    json={
                        "model": self.model,
                        "input": prefixed_text
                    }
                )

                if response.status_code == 200:
                    break
                elif response.status_code >= 500:
                    # Server error - retry
                    last_error = RuntimeError(f"Server error {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                        continue
                else:
                    # Client error - don't retry
                    raise RuntimeError(f"Embedding failed: {response.text}")
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Embedding timeout, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise RuntimeError(f"Embedding timeout after {max_retries} retries") from e
            except httpx.ConnectError as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Connection error, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}") from e
        else:
            # All retries exhausted
            raise last_error or RuntimeError("Embedding failed after retries")

        if response.status_code != 200:
            raise RuntimeError(f"Embedding failed: {response.text}")

        data = response.json()
        embedding = np.array(data["embeddings"][0], dtype=np.float32)

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    async def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a search query.
        Uses search_query prefix for better retrieval.

        Args:
            query: Search query

        Returns:
            numpy array of shape (dim,)
        """
        client = await self._get_client()

        # Query prefix for retrieval tasks
        prefixed_query = f"search_query: {query}"

        response = await client.post(
            "/api/embed",
            json={
                "model": self.model,
                "input": prefixed_query
            }
        )

        if response.status_code != 200:
            raise RuntimeError(f"Embedding failed: {response.text}")

        data = response.json()
        embedding = np.array(data["embeddings"][0], dtype=np.float32)

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 1,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts sequentially.
        Processes one at a time for reliability with Ollama.

        Args:
            texts: List of texts to embed
            batch_size: Ignored (always processes one at a time)
            show_progress: Print progress updates

        Returns:
            numpy array of shape (len(texts), dim)
        """
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts):
            # Truncate very long texts to avoid timeout
            if len(text) > 8000:
                text = text[:8000] + "..."

            embedding = await self.embed(text)
            embeddings.append(embedding)

            if show_progress and (i + 1) % 5 == 0:
                print(f"  Embedded {i + 1}/{total} chunks ({(i + 1)*100//total}%)")

        if show_progress:
            print(f"  Embedded {total}/{total} chunks (100%)")

        return np.stack(embeddings)


class SyncEmbedder:
    """Synchronous wrapper around async Embedder."""

    def __init__(self, **kwargs):
        self._async_embedder = Embedder(**kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
            return self._loop

    def _run(self, coro):
        """Run coroutine in event loop."""
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    def health_check(self) -> bool:
        return self._run(self._async_embedder.health_check())

    def embed(self, text: str) -> np.ndarray:
        return self._run(self._async_embedder.embed(text))

    def embed_query(self, query: str) -> np.ndarray:
        return self._run(self._async_embedder.embed_query(query))

    def embed_batch(self, texts: List[str], **kwargs) -> np.ndarray:
        return self._run(self._async_embedder.embed_batch(texts, **kwargs))

    def close(self):
        self._run(self._async_embedder.close())
        if self._loop and not self._loop.is_closed():
            self._loop.close()
