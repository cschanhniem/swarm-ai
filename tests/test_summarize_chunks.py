# -*- coding: utf-8 -*-
"""
test_summarize_chunks.py -- Tests for summarize_chunks.py.

Tests the ChunkSummarizer class logic without real API calls.
"""
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from tools.summarize_chunks import (
    ChunkSummarizer,
    MODELS,
    COST_PER_1M,
    SYSTEM_PROMPT,
    MAX_RETRIES,
)


class TestChunkSummarizerInit:
    """Tests for ChunkSummarizer construction."""

    def test_default_model(self):
        summarizer = ChunkSummarizer(model="haiku")
        assert summarizer.model == "haiku"
        assert summarizer.model_id == MODELS["haiku"]
        assert summarizer.client is None
        assert summarizer.run_id is None

    def test_sonnet_model(self):
        summarizer = ChunkSummarizer(model="sonnet")
        assert summarizer.model_id == MODELS["sonnet"]

    def test_unknown_model_defaults_to_haiku(self):
        summarizer = ChunkSummarizer(model="unknown")
        assert summarizer.model_id == MODELS["haiku"]

    def test_initial_stats(self):
        summarizer = ChunkSummarizer()
        assert summarizer.stats["chunks_processed"] == 0
        assert summarizer.stats["chunks_summarized"] == 0
        assert summarizer.stats["errors"] == 0
        assert summarizer.stats["total_input_tokens"] == 0
        assert summarizer.stats["total_output_tokens"] == 0
        assert summarizer.stats["total_cost_usd"] == 0.0


class TestTokenTracking:
    """Tests for token and cost tracking."""

    def test_track_tokens_haiku(self):
        summarizer = ChunkSummarizer(model="haiku")
        summarizer._track_tokens(1000, 500)

        assert summarizer.stats["total_input_tokens"] == 1000
        assert summarizer.stats["total_output_tokens"] == 500

        # Cost: (1000 * 1.00 + 500 * 5.00) / 1_000_000 = 0.0035
        expected_cost = (1000 * 1.00 + 500 * 5.00) / 1_000_000
        assert abs(summarizer.stats["total_cost_usd"] - expected_cost) < 1e-10

    def test_track_tokens_sonnet(self):
        summarizer = ChunkSummarizer(model="sonnet")
        summarizer._track_tokens(1000, 500)

        expected_cost = (1000 * 3.00 + 500 * 15.00) / 1_000_000
        assert abs(summarizer.stats["total_cost_usd"] - expected_cost) < 1e-10

    def test_track_tokens_accumulates(self):
        summarizer = ChunkSummarizer(model="haiku")
        summarizer._track_tokens(100, 50)
        summarizer._track_tokens(200, 100)

        assert summarizer.stats["total_input_tokens"] == 300
        assert summarizer.stats["total_output_tokens"] == 150


class TestSummarizeChunk:
    """Tests for the summarize_chunk method with mocked API."""

    def test_successful_summary(self, mock_anthropic_client):
        summarizer = ChunkSummarizer(model="haiku")
        summarizer.client = mock_anthropic_client

        mock_anthropic_client.messages.create.return_value = (
            mock_anthropic_client._make_response(
                "Dies ist eine Zusammenfassung des Textes.", 100, 30
            )
        )

        result = summarizer.summarize_chunk("Ein langer Text zum Zusammenfassen...")
        assert result == "Dies ist eine Zusammenfassung des Textes."
        assert summarizer.stats["total_input_tokens"] == 100
        assert summarizer.stats["total_output_tokens"] == 30

    def test_api_error_returns_none(self, mock_anthropic_client):
        summarizer = ChunkSummarizer(model="haiku")
        summarizer.client = mock_anthropic_client

        mock_anthropic_client.messages.create.side_effect = Exception("API error")

        result = summarizer.summarize_chunk("Text")
        assert result is None


class TestModelsAndCosts:
    """Tests for model and cost configuration."""

    def test_haiku_model_id(self):
        assert "haiku" in MODELS["haiku"]

    def test_sonnet_model_id(self):
        assert "sonnet" in MODELS["sonnet"]

    def test_haiku_costs(self):
        assert COST_PER_1M["haiku"]["input"] == 1.00
        assert COST_PER_1M["haiku"]["output"] == 5.00

    def test_sonnet_costs(self):
        assert COST_PER_1M["sonnet"]["input"] == 3.00
        assert COST_PER_1M["sonnet"]["output"] == 15.00

    def test_sonnet_more_expensive_than_haiku(self):
        assert COST_PER_1M["sonnet"]["input"] > COST_PER_1M["haiku"]["input"]
        assert COST_PER_1M["sonnet"]["output"] > COST_PER_1M["haiku"]["output"]


class TestSystemPrompt:
    """Tests for the system prompt configuration."""

    def test_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 50

    def test_prompt_mentions_summary(self):
        assert "zusammen" in SYSTEM_PROMPT.lower() or "Zusammenfassung" in SYSTEM_PROMPT

    def test_max_retries(self):
        assert MAX_RETRIES >= 1
        assert MAX_RETRIES <= 10


class TestGetUnsummarizedChunks:
    """Test chunk loading from DB."""

    def test_with_empty_db(self, tmp_path):
        """Should return empty list when no chunks exist."""
        db_path = tmp_path / "test_chunks.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE document_chunks (
                id INTEGER PRIMARY KEY,
                search_index_id INTEGER,
                chunk_number INTEGER,
                chunk_text TEXT,
                chunk_tokens INTEGER,
                summary TEXT
            )
        """)
        conn.commit()
        conn.close()

        summarizer = ChunkSummarizer(model="haiku", db_path=db_path)
        chunks = summarizer.get_unsummarized_chunks()
        assert chunks == []

    def test_returns_only_unsummarized(self, tmp_path):
        """Should only return chunks where summary IS NULL."""
        db_path = tmp_path / "test_chunks.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE document_chunks (
                id INTEGER PRIMARY KEY,
                search_index_id INTEGER,
                chunk_number INTEGER,
                chunk_text TEXT,
                chunk_tokens INTEGER,
                summary TEXT
            )
        """)
        conn.execute(
            "INSERT INTO document_chunks VALUES (1, 1, 1, 'Text A', 50, NULL)"
        )
        conn.execute(
            "INSERT INTO document_chunks VALUES (2, 1, 2, 'Text B', 60, 'Already summarized')"
        )
        conn.execute(
            "INSERT INTO document_chunks VALUES (3, 2, 1, 'Text C', 40, NULL)"
        )
        conn.commit()
        conn.close()

        summarizer = ChunkSummarizer(model="haiku", db_path=db_path)
        chunks = summarizer.get_unsummarized_chunks()
        assert len(chunks) == 2
        assert chunks[0]["chunk_text"] == "Text A"
        assert chunks[1]["chunk_text"] == "Text C"

    def test_respects_limit(self, tmp_path):
        db_path = tmp_path / "test_chunks.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE document_chunks (
                id INTEGER PRIMARY KEY,
                search_index_id INTEGER,
                chunk_number INTEGER,
                chunk_text TEXT,
                chunk_tokens INTEGER,
                summary TEXT
            )
        """)
        for i in range(10):
            conn.execute(
                f"INSERT INTO document_chunks VALUES ({i+1}, 1, {i+1}, 'Text {i}', 50, NULL)"
            )
        conn.commit()
        conn.close()

        summarizer = ChunkSummarizer(model="haiku", db_path=db_path)
        chunks = summarizer.get_unsummarized_chunks(limit=3)
        assert len(chunks) == 3
