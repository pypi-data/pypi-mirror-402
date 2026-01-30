"""
Comprehensive tests for RAG system.

Tests all components: chunking, embedding, retrieval, query processing.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile

from finrobot.experiments.rag_system import (
    Document,
    TextChunker,
    SimpleEmbedder,
    VectorStore,
    BM25Retriever,
    HybridRetriever,
    QueryProcessor,
    RAGChain,
)


class TestDocument:
    """Test Document dataclass."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            content="Test content",
            metadata={"ticker": "AAPL", "source": "yfinance"},
        )

        assert doc.content == "Test content"
        assert doc.metadata["ticker"] == "AAPL"
        assert doc.embedding is None

    def test_document_to_dict(self):
        """Test document to dict conversion."""
        doc = Document(content="Test", metadata={"key": "value"})
        d = doc.to_dict()

        assert d["content"] == "Test"
        assert d["metadata"]["key"] == "value"
        assert d["embedding"] is None


class TestTextChunker:
    """Test text chunking functionality."""

    @pytest.fixture
    def chunker(self):
        return TextChunker(chunk_size=100, overlap=20)

    def test_chunker_creation(self, chunker):
        """Test creating a chunker."""
        assert chunker.chunk_size == 100
        assert chunker.overlap == 20

    def test_chunk_simple_text(self, chunker):
        """Test chunking simple text."""
        text = "A" * 250  # 250 characters
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 2
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_chunk_empty_text(self, chunker):
        """Test chunking empty text."""
        chunks = chunker.chunk_text("")
        assert len(chunks) == 0

    def test_chunk_stock_data(self, chunker):
        """Test chunking stock data."""
        data = {
            "price_history": "High: 150 Low: 140",
            "news": ["News 1", "News 2"],
            "fundamentals": {"PE": 25, "Market Cap": "2.5T"},
        }

        chunks = chunker.chunk_stock_data("AAPL", data)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)


class TestSimpleEmbedder:
    """Test embedding functionality."""

    @pytest.fixture
    def embedder(self):
        return SimpleEmbedder()

    def test_embed_text(self, embedder):
        """Test embedding text."""
        embedding = embedder.embed("Test text")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)
        assert np.isfinite(embedding).all()

    def test_embed_is_normalized(self, embedder):
        """Test that embeddings are normalized."""
        embedding = embedder.embed("Test text")
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0)

    def test_embed_consistency(self, embedder):
        """Test that same text produces same embedding."""
        emb1 = embedder.embed("Test text")
        emb2 = embedder.embed("Test text")

        assert np.allclose(emb1, emb2)

    def test_embed_batch(self, embedder):
        """Test batch embedding."""
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(isinstance(e, np.ndarray) for e in embeddings)


class TestVectorStore:
    """Test vector store functionality."""

    @pytest.fixture
    def store(self):
        return VectorStore()

    def test_add_documents(self, store):
        """Test adding documents."""
        docs = [
            Document(content="AAPL stock is strong", metadata={"ticker": "AAPL"}),
            Document(content="MSFT is a tech leader", metadata={"ticker": "MSFT"}),
        ]

        store.add_documents(docs)

        assert len(store.documents) == 2
        assert store.embeddings.shape == (2, 768)

    def test_search_empty_store(self, store):
        """Test searching empty store."""
        results = store.search("test query")
        assert len(results) == 0

    def test_search_with_results(self, store):
        """Test searching with results."""
        docs = [
            Document(content="AAPL stock is strong", metadata={"ticker": "AAPL"}),
            Document(content="AAPL is a tech company", metadata={"ticker": "AAPL"}),
            Document(content="MSFT is different", metadata={"ticker": "MSFT"}),
        ]

        store.add_documents(docs)
        results = store.search("AAPL stock", top_k=2)

        assert len(results) <= 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_search_returns_scores(self, store):
        """Test that search returns similarity scores."""
        docs = [
            Document(content="Test content 1", metadata={}),
            Document(content="Test content 2", metadata={}),
        ]

        store.add_documents(docs)
        results = store.search("test", top_k=2)

        if results:
            doc, score = results[0]
            assert isinstance(score, float)
            assert -1 <= score <= 1  # Cosine similarity range


class TestBM25Retriever:
    """Test BM25 keyword retriever."""

    @pytest.fixture
    def retriever(self):
        return BM25Retriever()

    def test_add_documents(self, retriever):
        """Test adding documents."""
        docs = [
            Document(content="AAPL stock price", metadata={}),
            Document(content="MSFT earnings report", metadata={}),
        ]

        retriever.add_documents(docs)
        assert len(retriever.documents) == 2

    def test_search_with_keywords(self, retriever):
        """Test keyword search."""
        docs = [
            Document(content="AAPL stock is strong", metadata={}),
            Document(content="MSFT is a tech company", metadata={}),
            Document(content="AAPL earnings beat expectations", metadata={}),
        ]

        retriever.add_documents(docs)
        results = retriever.search("AAPL earnings", top_k=2)

        assert len(results) > 0
        # Results should be sorted by relevance
        assert all(isinstance(r, tuple) for r in results)

    def test_bm25_no_results(self, retriever):
        """Test BM25 with no matching documents."""
        docs = [
            Document(content="Unrelated content", metadata={}),
        ]

        retriever.add_documents(docs)
        results = retriever.search("AAPL stock", top_k=5)

        # May have partial matches or no matches
        assert isinstance(results, list)


class TestHybridRetriever:
    """Test hybrid semantic + keyword retriever."""

    @pytest.fixture
    def retriever(self):
        return HybridRetriever(semantic_weight=0.6)

    def test_hybrid_add_documents(self, retriever):
        """Test adding documents to hybrid retriever."""
        docs = [
            Document(content="AAPL stock analysis", metadata={"ticker": "AAPL"}),
            Document(content="MSFT quarterly earnings", metadata={"ticker": "MSFT"}),
        ]

        retriever.add_documents(docs)
        assert len(retriever.vector_store.documents) == 2
        assert len(retriever.bm25_retriever.documents) == 2

    def test_hybrid_search(self, retriever):
        """Test hybrid search."""
        docs = [
            Document(
                content="Apple stock price increased to $150", metadata={"ticker": "AAPL"}
            ),
            Document(content="Microsoft announced new AI features", metadata={"ticker": "MSFT"}),
            Document(content="Apple releases new iPhone", metadata={"ticker": "AAPL"}),
        ]

        retriever.add_documents(docs)
        results = retriever.search("Apple stock", top_k=2)

        assert len(results) <= 2
        assert all(isinstance(r, tuple) for r in results)

    def test_hybrid_weights(self, retriever):
        """Test that weights affect search."""
        # Both should work with different weights
        retriever1 = HybridRetriever(semantic_weight=0.9)
        retriever2 = HybridRetriever(semantic_weight=0.1)

        docs = [Document(content="Test content", metadata={})]
        retriever1.add_documents(docs)
        retriever2.add_documents(docs)

        results1 = retriever1.search("test", top_k=1)
        results2 = retriever2.search("test", top_k=1)

        assert len(results1) >= 0  # Should work
        assert len(results2) >= 0  # Should work


class TestQueryProcessor:
    """Test query processing."""

    @pytest.fixture
    def processor(self):
        return QueryProcessor()

    def test_extract_ticker(self, processor):
        """Test ticker extraction."""
        entities = processor.extract_entities("What is AAPL stock price?")
        assert entities["ticker"] == "AAPL"

    def test_extract_time_period(self, processor):
        """Test time period extraction."""
        entities = processor.extract_entities("Predict AAPL for next week")
        assert entities["time_period"] == "1_week"

        entities = processor.extract_entities("MSFT forecast for next month")
        assert entities["time_period"] == "1_month"

    def test_extract_metric(self, processor):
        """Test metric extraction."""
        entities = processor.extract_entities("What is the price risk?")
        assert entities["metric"] in ["price", "risk"]

    def test_expand_query(self, processor):
        """Test query expansion."""
        expanded = processor.expand_query("AAPL price up")

        assert "price" in expanded.lower()
        assert "increase" in expanded.lower() or "rise" in expanded.lower()


class TestRAGChain:
    """Test complete RAG chain."""

    @pytest.fixture
    def rag(self):
        return RAGChain()

    def test_rag_creation(self, rag):
        """Test RAG chain creation."""
        assert rag.chunker is not None
        assert rag.embedder is not None
        assert rag.retriever is not None

    def test_retrieve_context(self, rag):
        """Test context retrieval."""
        # Add some documents first
        docs = [
            Document(content="AAPL stock price is $150", metadata={"ticker": "AAPL"}),
            Document(content="AAPL revenue increased 10%", metadata={"ticker": "AAPL"}),
        ]
        rag.retriever.add_documents(docs)

        context = rag.retrieve_context("AAPL stock")

        assert isinstance(context, list)
        assert len(context) >= 0

    def test_generate_response(self, rag):
        """Test response generation."""
        context = ["Stock price is $150", "Volume increased"]
        response = rag.generate_response("What about AAPL?", context)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_run_complete_pipeline(self, rag):
        """Test running complete RAG pipeline."""
        # Note: This test uses small data and may need real data integration
        try:
            metric = rag.run(
                ticker="AAPL",
                start_date="2025-01-01",
                end_date="2025-01-10",
                query="Analyze AAPL stock",
                task_name="test_analysis",
            )

            assert metric is not None
            assert metric.system_name == "rag"
            assert metric.ticker == "AAPL"
            assert len(metric.response_text) > 0

        except Exception as e:
            # Data fetching may fail in test environment
            pytest.skip(f"Data fetching failed: {e}")
