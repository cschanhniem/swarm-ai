# -*- coding: utf-8 -*-
"""
test_translate_swarm.py -- Tests for translate_swarm.py utility functions.

Only pure/utility functions are tested (no API calls, no DB access needed).
"""
import pytest

from tools.translate_swarm import (
    chunk_texts,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_WORKERS,
    MAX_RETRIES,
    SYSTEM_PROMPT,
    TABLE,
    SOURCE_TAG,
)


class TestChunkTexts:
    """Tests for the chunk_texts utility."""

    def test_exact_division(self):
        items = list(range(10))
        chunks = chunk_texts(items, 5)
        assert len(chunks) == 2
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]

    def test_remainder(self):
        items = list(range(7))
        chunks = chunk_texts(items, 3)
        assert len(chunks) == 3
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[2] == [6]

    def test_single_chunk(self):
        items = [1, 2, 3]
        chunks = chunk_texts(items, 10)
        assert len(chunks) == 1
        assert chunks[0] == [1, 2, 3]

    def test_empty_list(self):
        chunks = chunk_texts([], 5)
        assert chunks == []

    def test_chunk_size_one(self):
        items = ["a", "b", "c"]
        chunks = chunk_texts(items, 1)
        assert len(chunks) == 3
        assert all(len(c) == 1 for c in chunks)

    def test_preserves_dict_items(self):
        """chunk_texts should work with any list items including dicts."""
        items = [
            {"key": "a", "value": "Hallo"},
            {"key": "b", "value": "Welt"},
            {"key": "c", "value": "Test"},
        ]
        chunks = chunk_texts(items, 2)
        assert len(chunks) == 2
        assert chunks[0][0]["key"] == "a"
        assert chunks[1][0]["key"] == "c"


class TestConstants:
    """Verify that module constants are sane."""

    def test_default_chunk_size(self):
        assert DEFAULT_CHUNK_SIZE > 0
        assert DEFAULT_CHUNK_SIZE <= 50  # Reasonable upper bound

    def test_default_workers(self):
        assert DEFAULT_WORKERS > 0
        assert DEFAULT_WORKERS <= 20

    def test_max_retries(self):
        assert MAX_RETRIES >= 1

    def test_system_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 50

    def test_system_prompt_mentions_json(self):
        """The prompt should instruct the model to return JSON."""
        assert "JSON" in SYSTEM_PROMPT

    def test_table_name(self):
        assert TABLE == "languages_translations"

    def test_source_tag(self):
        assert SOURCE_TAG == "llm_auto_swarm"
