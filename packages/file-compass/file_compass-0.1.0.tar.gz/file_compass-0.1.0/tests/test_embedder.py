"""
Tests for file_compass.embedder module.
Uses mocks to avoid requiring Ollama to be running.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from file_compass.embedder import Embedder, SyncEmbedder


class TestEmbedder:
    """Tests for async Embedder class."""

    def test_init_defaults(self):
        """Test default initialization."""
        embedder = Embedder()
        assert embedder.base_url is not None
        assert embedder.model is not None
        assert embedder.dim == 768
        assert embedder.timeout == 120.0
        assert embedder._client is None

    def test_init_custom_values(self):
        """Test custom initialization."""
        embedder = Embedder(
            base_url="http://custom:1234",
            model="custom-model",
            timeout=60.0
        )
        assert embedder.base_url == "http://custom:1234"
        assert embedder.model == "custom-model"
        assert embedder.timeout == 60.0

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self):
        """Test that _get_client creates a client."""
        embedder = Embedder()
        try:
            client = await embedder._get_client()
            assert client is not None
            assert embedder._client is client
        finally:
            await embedder.close()

    @pytest.mark.asyncio
    async def test_get_client_reuses_client(self):
        """Test that _get_client reuses existing client."""
        embedder = Embedder()
        try:
            client1 = await embedder._get_client()
            client2 = await embedder._get_client()
            assert client1 is client2
        finally:
            await embedder.close()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test client cleanup."""
        embedder = Embedder()
        await embedder._get_client()
        assert embedder._client is not None

        await embedder.close()
        assert embedder._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test close when no client exists."""
        embedder = Embedder()
        # Should not raise
        await embedder.close()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "nomic-embed-text:latest"}]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        """Test health check when model not loaded."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama2:latest"}]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        """Test health check on connection error."""
        embedder = Embedder()

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_get_client.return_value = mock_client

            result = await embedder.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_bad_status(self):
        """Test health check with bad status code."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_embed_single_short_text(self):
        """Test embedding short text (no chunking)."""
        embedder = Embedder()

        # Mock embedding response
        mock_embedding = np.random.randn(768).astype(np.float32)
        mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.embed("short text")

            assert result.shape == (768,)
            assert np.isclose(np.linalg.norm(result), 1.0)  # Normalized

            # Check that search_document prefix was added
            call_args = mock_client.post.call_args
            assert "search_document:" in call_args[1]["json"]["input"]

    @pytest.mark.asyncio
    async def test_embed_long_text_chunking(self):
        """Test embedding long text (triggers chunking)."""
        embedder = Embedder()

        # Create text longer than MAX_CHARS (1500)
        long_text = "word " * 400  # ~2000 chars

        # Mock embedding response
        mock_embedding = np.random.randn(768).astype(np.float32)
        mock_embedding = mock_embedding / np.linalg.norm(mock_embedding)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.embed(long_text)

            assert result.shape == (768,)
            # Should have been called multiple times for chunks
            assert mock_client.post.call_count > 1

    @pytest.mark.asyncio
    async def test_embed_error(self):
        """Test embedding error handling with server error."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            # With retry logic, server errors raise RuntimeError with server error message
            with pytest.raises(RuntimeError, match="Server error 500"):
                await embedder.embed("test")

    @pytest.mark.asyncio
    async def test_embed_client_error(self):
        """Test embedding with client error (4xx - no retry)."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(RuntimeError, match="Embedding failed"):
                await embedder.embed("test")

    @pytest.mark.asyncio
    async def test_embed_query(self):
        """Test query embedding."""
        embedder = Embedder()

        mock_embedding = np.random.randn(768).astype(np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.embed_query("search query")

            assert result.shape == (768,)

            # Check that search_query prefix was added
            call_args = mock_client.post.call_args
            assert "search_query:" in call_args[1]["json"]["input"]

    @pytest.mark.asyncio
    async def test_embed_query_error(self):
        """Test query embedding error."""
        embedder = Embedder()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(RuntimeError, match="Embedding failed"):
                await embedder.embed_query("test")

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test batch embedding."""
        embedder = Embedder()

        texts = ["text1", "text2", "text3"]

        mock_embedding = np.random.randn(768).astype(np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.embed_batch(texts)

            assert result.shape == (3, 768)
            # Should have been called 3 times (once per text)
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_embed_batch_truncates_long_texts(self):
        """Test that batch embedding truncates very long texts."""
        embedder = Embedder()

        # Text longer than 8000 chars
        very_long_text = "x" * 10000
        texts = [very_long_text]

        mock_embedding = np.random.randn(768).astype(np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(embedder, 'embed', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = mock_embedding

                await embedder.embed_batch(texts)

                # Check that text was truncated before calling embed
                call_args = mock_embed.call_args
                called_text = call_args[0][0]
                assert len(called_text) <= 8003  # 8000 + "..."

    @pytest.mark.asyncio
    async def test_embed_batch_with_progress(self, capsys):
        """Test batch embedding with progress output."""
        embedder = Embedder()

        texts = ["text"] * 10

        mock_embedding = np.random.randn(768).astype(np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [mock_embedding.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await embedder.embed_batch(texts, show_progress=True)

            captured = capsys.readouterr()
            assert "Embedded" in captured.out
            assert "100%" in captured.out


class TestSplitIntoChunks:
    """Tests for chunk splitting logic."""

    def test_split_short_text(self):
        """Test that short text returns single chunk."""
        embedder = Embedder()
        chunks = embedder._split_into_chunks("short", max_chars=100)
        assert len(chunks) == 1
        assert chunks[0] == "short"

    def test_split_long_text(self):
        """Test splitting long text."""
        embedder = Embedder()
        text = "a" * 300
        chunks = embedder._split_into_chunks(text, max_chars=100, overlap=20)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Each chunk should be <= max_chars
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_split_with_overlap(self):
        """Test that chunks overlap."""
        embedder = Embedder()
        text = "0123456789" * 30  # 300 chars
        chunks = embedder._split_into_chunks(text, max_chars=100, overlap=20)

        # Check overlap exists
        for i in range(len(chunks) - 1):
            end_of_current = chunks[i][-20:]
            start_of_next = chunks[i + 1][:20]
            # Overlapping portion should match
            assert end_of_current == start_of_next

    def test_split_empty_text(self):
        """Test splitting empty text."""
        embedder = Embedder()
        chunks = embedder._split_into_chunks("", max_chars=100)
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_split_whitespace_only(self):
        """Test that whitespace-only chunks are skipped."""
        embedder = Embedder()
        # Text with whitespace between content
        text = "content" + " " * 200 + "more"
        chunks = embedder._split_into_chunks(text, max_chars=100, overlap=10)

        # All chunks should have non-whitespace content
        for chunk in chunks:
            assert chunk.strip() or len(chunks) == 1


class TestSyncEmbedder:
    """Tests for synchronous embedder wrapper."""

    def test_init(self):
        """Test SyncEmbedder initialization."""
        sync_embedder = SyncEmbedder()
        assert sync_embedder._async_embedder is not None

    def test_init_custom_values(self):
        """Test SyncEmbedder with custom values."""
        sync_embedder = SyncEmbedder(
            base_url="http://custom:1234",
            model="custom-model"
        )
        assert sync_embedder._async_embedder.base_url == "http://custom:1234"
        assert sync_embedder._async_embedder.model == "custom-model"

    def test_health_check(self):
        """Test sync health check."""
        sync_embedder = SyncEmbedder()

        with patch.object(sync_embedder._async_embedder, 'health_check',
                          new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            result = sync_embedder.health_check()
            assert result is True

    def test_embed(self):
        """Test sync embed."""
        sync_embedder = SyncEmbedder()

        mock_embedding = np.random.randn(768).astype(np.float32)

        with patch.object(sync_embedder._async_embedder, 'embed',
                          new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embedding
            result = sync_embedder.embed("test text")
            assert result.shape == (768,)

    def test_embed_query(self):
        """Test sync embed_query."""
        sync_embedder = SyncEmbedder()

        mock_embedding = np.random.randn(768).astype(np.float32)

        with patch.object(sync_embedder._async_embedder, 'embed_query',
                          new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embedding
            result = sync_embedder.embed_query("search query")
            assert result.shape == (768,)

    def test_embed_batch(self):
        """Test sync embed_batch."""
        sync_embedder = SyncEmbedder()

        mock_embeddings = np.random.randn(3, 768).astype(np.float32)

        with patch.object(sync_embedder._async_embedder, 'embed_batch',
                          new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embeddings
            result = sync_embedder.embed_batch(["text1", "text2", "text3"])
            assert result.shape == (3, 768)

    def test_close(self):
        """Test sync close."""
        sync_embedder = SyncEmbedder()

        with patch.object(sync_embedder._async_embedder, 'close',
                          new_callable=AsyncMock) as mock_close:
            sync_embedder.close()
            mock_close.assert_called_once()


class TestNormalization:
    """Tests for embedding normalization."""

    @pytest.mark.asyncio
    async def test_embed_normalizes_output(self):
        """Test that embeddings are normalized."""
        embedder = Embedder()

        # Create unnormalized embedding
        unnormalized = np.array([1.0, 2.0, 3.0] * 256, dtype=np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [unnormalized.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await embedder.embed("test")

            # Should be normalized (L2 norm = 1)
            assert np.isclose(np.linalg.norm(result), 1.0, atol=1e-5)

    @pytest.mark.asyncio
    async def test_embed_handles_zero_norm(self):
        """Test handling of zero-norm embedding."""
        embedder = Embedder()

        # Zero embedding
        zero_emb = np.zeros(768, dtype=np.float32)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [zero_emb.tolist()]
        }

        with patch.object(embedder, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            # Should not raise division by zero
            result = await embedder.embed("test")
            assert result.shape == (768,)
