"""
Shared pytest fixtures for Vestigaea tests.
"""
import pytest
import random
from pathlib import Path

@pytest.fixture
def seed_rng():
    """Set a fixed random seed for deterministic tests."""
    random.seed(42)
    yield
    random.seed()  # Reset to random state after test

@pytest.fixture
def test_world():
    """Create a fresh World instance for each test."""
    from vestigaea.core.ecs import World
    return World()

@pytest.fixture
def base_genome():
    """Standard test genome with known values."""
    return {
        "morphology": {"size": 0.9},
        "locomotion": {"type": "wade", "speed": 120},
        "metabolism": {"rate": 1.0, "stamina_max": 100},
        "sense": {"vision": {"range": 180, "fov_deg": 110}},
        "behavior": {"risk_tolerance": 0.3, "memory_span": 2},
        "verbs": ["move", "forage", "hide"]
    }