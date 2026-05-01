# -*- coding: utf-8 -*-
"""
test_stigmergy.py -- Tests for StigmergyAPI (tools/stigmergy_api.py).

These tests use a real SQLite in-memory/temp DB -- no API mocking needed.
The Stigmergy pattern is purely local (SQLite-based pheromone coordination).
"""
import json
import pytest

from tools.stigmergy_api import (
    StigmergyAPI,
    deposit_pheromone,
    sense_pheromones,
    get_best_pheromone_path,
)


class TestStigmergyDeposit:
    """Tests for depositing pheromones."""

    def test_deposit_basic(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        result = api.deposit("path_alpha", strength=0.8)
        assert result is True

    def test_deposit_clamps_strength(self, stigmergy_db):
        """Strength should be clamped to [0.0, 1.0]."""
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")

        api.deposit("path_high", strength=5.0)
        api.deposit("path_low", strength=-2.0)

        paths = api.sense()
        strengths = {p["path_id"]: p["strength"] for p in paths}
        assert strengths["path_high"] == 1.0
        assert strengths["path_low"] == 0.0

    def test_deposit_with_metadata(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_B")
        api.deposit("path_meta", strength=0.5, metadata={"result": "success", "time_ms": 200})

        paths = api.sense()
        assert len(paths) == 1
        assert paths[0]["metadata"]["result"] == "success"
        assert paths[0]["metadata"]["time_ms"] == 200

    def test_deposit_updates_existing(self, stigmergy_db):
        """Depositing on the same path_id should UPDATE, not create duplicate."""
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")

        api.deposit("path_x", strength=0.3, metadata={"v": 1})
        api.deposit("path_x", strength=0.9, metadata={"v": 2})

        paths = api.sense()
        assert len(paths) == 1
        assert paths[0]["strength"] == 0.9
        assert paths[0]["metadata"]["v"] == 2


class TestStimergySense:
    """Tests for reading pheromones."""

    def test_sense_empty(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db)
        paths = api.sense()
        assert paths == []

    def test_sense_sorted_by_strength(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("weak", strength=0.2)
        api.deposit("strong", strength=0.9)
        api.deposit("medium", strength=0.5)

        paths = api.sense()
        assert len(paths) == 3
        assert paths[0]["path_id"] == "strong"
        assert paths[1]["path_id"] == "medium"
        assert paths[2]["path_id"] == "weak"

    def test_sense_with_prefix_filter(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("approach_refactor", strength=0.8)
        api.deposit("approach_rewrite", strength=0.6)
        api.deposit("module_xyz", strength=0.9)

        approach_paths = api.sense(path_prefix="approach_")
        assert len(approach_paths) == 2

        module_paths = api.sense(path_prefix="module_")
        assert len(module_paths) == 1
        assert module_paths[0]["path_id"] == "module_xyz"

    def test_sense_includes_agent_id(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_C")
        api.deposit("path_test", strength=0.7)

        paths = api.sense()
        assert paths[0]["agent_id"] == "agent_C"


class TestStigmergyEvaporate:
    """Tests for pheromone evaporation."""

    def test_evaporate_removes_weakest(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("strong_path", strength=0.9)
        api.deposit("medium_path", strength=0.5)
        api.deposit("weak_path", strength=0.1)

        # Evaporate bottom 33% (1 of 3)
        deleted = api.evaporate(decay_rate=0.33)
        assert deleted == 1

        remaining = api.sense()
        path_ids = [p["path_id"] for p in remaining]
        assert "weak_path" not in path_ids
        assert "strong_path" in path_ids

    def test_evaporate_empty_db(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db)
        deleted = api.evaporate(decay_rate=0.5)
        assert deleted == 0

    def test_evaporate_clamps_rate(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("path_1", strength=0.5)

        # Rate > 1.0 should be clamped to 1.0 (delete all)
        deleted = api.evaporate(decay_rate=5.0)
        assert deleted == 1

    def test_evaporate_minimum_one(self, stigmergy_db):
        """Even with low decay_rate, at least 1 should be evaporated."""
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("path_1", strength=0.3)
        api.deposit("path_2", strength=0.8)

        deleted = api.evaporate(decay_rate=0.01)  # 1% of 2 = 0.02, rounded up to 1
        assert deleted == 1


class TestStigmergyGetBestPath:
    """Tests for get_best_path()."""

    def test_best_path_returns_strongest(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("low", strength=0.2)
        api.deposit("high", strength=0.95)
        api.deposit("mid", strength=0.5)

        best = api.get_best_path()
        assert best == "high"

    def test_best_path_with_prefix(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("task_easy", strength=0.3)
        api.deposit("task_hard", strength=0.9)
        api.deposit("other_thing", strength=1.0)

        best = api.get_best_path(path_prefix="task_")
        assert best == "task_hard"

    def test_best_path_empty(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db)
        assert api.get_best_path() is None


class TestStigmergyDump:
    """Tests for dump() debug method."""

    def test_dump_format(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db, agent_id="agent_A")
        api.deposit("p1", strength=0.5, metadata={"k": "v"})
        api.deposit("p2", strength=0.8)

        dumped = api.dump()
        assert "p1" in dumped
        assert "p2" in dumped
        assert dumped["p1"]["strength"] == 0.5
        assert dumped["p1"]["metadata"] == {"k": "v"}

    def test_dump_empty(self, stigmergy_db):
        api = StigmergyAPI(stigmergy_db)
        assert api.dump() == {}


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_deposit_pheromone(self, stigmergy_db):
        result = deposit_pheromone(stigmergy_db, "agent_X", "path_conv", 0.7)
        assert result is True

    def test_sense_pheromones(self, stigmergy_db):
        deposit_pheromone(stigmergy_db, "agent_X", "p1", 0.5)
        deposit_pheromone(stigmergy_db, "agent_Y", "p2", 0.8)

        paths = sense_pheromones(stigmergy_db)
        assert len(paths) == 2
        assert paths[0]["path_id"] == "p2"  # stronger first

    def test_get_best_pheromone_path(self, stigmergy_db):
        deposit_pheromone(stigmergy_db, "a", "alpha", 0.3)
        deposit_pheromone(stigmergy_db, "b", "beta", 0.9)

        best = get_best_pheromone_path(stigmergy_db)
        assert best == "beta"

    def test_get_best_pheromone_path_empty(self, stigmergy_db):
        result = get_best_pheromone_path(stigmergy_db)
        assert result is None


class TestMultiAgentScenario:
    """Integration test: Multiple agents interacting via pheromones."""

    def test_ant_colony_simulation(self, stigmergy_db):
        """Simulate 3 agents exploring paths and converging on the best one."""
        agent_a = StigmergyAPI(stigmergy_db, agent_id="ant_A")
        agent_b = StigmergyAPI(stigmergy_db, agent_id="ant_B")
        agent_c = StigmergyAPI(stigmergy_db, agent_id="ant_C")

        # Round 1: Each agent explores a different path
        agent_a.deposit("route_north", strength=0.4, metadata={"food": False})
        agent_b.deposit("route_south", strength=0.8, metadata={"food": True})
        agent_c.deposit("route_east", strength=0.2, metadata={"food": False})

        # Agent A senses and follows strongest path
        best = agent_a.get_best_path()
        assert best == "route_south"

        # Round 2: Agent A reinforces route_south
        agent_a.deposit("route_south", strength=0.9, metadata={"food": True, "confirmed": True})

        # Agent C also follows
        paths = agent_c.sense()
        assert paths[0]["path_id"] == "route_south"
        assert paths[0]["strength"] == 0.9  # Updated by agent_a

        # Evaporate weak paths
        evaporated = agent_a.evaporate(decay_rate=0.5)
        assert evaporated >= 1

        # route_south should survive (strongest)
        remaining = agent_a.sense()
        path_ids = [p["path_id"] for p in remaining]
        assert "route_south" in path_ids
