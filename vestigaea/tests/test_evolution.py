"""
Tests for genome evolution and mutation.
"""
import pytest
import random
import json
from pathlib import Path
from vestigaea.game.evolution import Evolution

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    return tmp_path

@pytest.fixture
def base_genome():
    """Create a test genome with known values."""
    return {
        "morphology": {"size": 0.9},
        "locomotion": {"type": "wade", "speed": 120},
        "metabolism": {"rate": 1.0, "stamina_max": 100},
        "sense": {"vision": {"range": 180, "fov_deg": 110}},
        "behavior": {"risk_tolerance": 0.3, "memory_span": 2},
        "verbs": ["move", "forage", "hide"]
    }

def test_genome_mutation(test_data_dir, base_genome):
    """Test genome mutation stays within valid ranges."""
    # Set up evolution with deterministic RNG
    random.seed(42)
    evolution = Evolution(test_data_dir)
    
    # Save initial genome
    with open(test_data_dir / "genome.json", "w") as f:
        json.dump(base_genome, f)
    
    # Perform multiple mutations
    current = base_genome
    for _ in range(10):
        mutated = evolution.mutate(current)
        
        # Check value ranges
        assert 80 <= mutated["sense"]["vision"]["range"] <= 280
        assert 60 <= mutated["sense"]["vision"]["fov_deg"] <= 150
        assert 0 <= mutated["behavior"]["risk_tolerance"] <= 1
        assert 70 <= mutated["locomotion"]["speed"] <= 200
        assert 60 <= mutated["metabolism"]["stamina_max"] <= 150
        
        # Values should change but not too dramatically
        vision_delta = abs(mutated["sense"]["vision"]["range"] - 
                         current["sense"]["vision"]["range"])
        assert vision_delta <= current["sense"]["vision"]["range"] * 0.15
        
        speed_delta = abs(mutated["locomotion"]["speed"] - 
                         current["locomotion"]["speed"])
        assert speed_delta <= current["locomotion"]["speed"] * 0.15
        
        current = mutated

def test_evolution_persistence(test_data_dir, base_genome):
    """Test genome history and milestone persistence."""
    evolution = Evolution(test_data_dir)
    
    # Save initial state
    with open(test_data_dir / "genome.json", "w") as f:
        json.dump(base_genome, f)
    
    # Evolve with some fitness scores
    scores = [10.5, 15.2, 8.7]
    for fitness in scores:
        new_genome, deltas = evolution.evolve(fitness)
        
        # Check that deltas are calculated
        assert "vision_range_pct" in deltas
        assert "risk_tolerance" in deltas
        assert "speed_pct" in deltas
        assert "stamina_pct" in deltas
    
    # Check history file
    history_path = test_data_dir / "genome.jsonl"
    assert history_path.exists()
    
    with open(history_path) as f:
        lines = f.readlines()
        assert len(lines) == len(scores)
        
        for line in lines:
            entry = json.loads(line)
            assert "genome" in entry
            assert "fitness" in entry

def test_milestone_tracking(test_data_dir):
    """Test milestone flag management."""
    evolution = Evolution(test_data_dir)
    
    # Initially no milestones
    assert not evolution.milestones["first_survival"]
    
    # Set milestone
    evolution.milestones["first_survival"] = True
    evolution.save_milestones()
    
    # Load fresh instance
    new_evolution = Evolution(test_data_dir)
    assert new_evolution.milestones["first_survival"]

def test_mutation_deltas(test_data_dir, base_genome):
    """Test delta calculations between genomes."""
    evolution = Evolution(test_data_dir)
    
    # Create a known mutation
    mutated = base_genome.copy()
    mutated["sense"]["vision"]["range"] = 198  # +10%
    mutated["behavior"]["risk_tolerance"] = 0.4  # +0.1
    mutated["locomotion"]["speed"] = 108  # -10%
    
    deltas = evolution.get_mutation_deltas(base_genome, mutated)
    
    assert deltas["vision_range_pct"] == pytest.approx(0.1)
    assert deltas["risk_tolerance"] == pytest.approx(0.1)
    assert deltas["speed_pct"] == pytest.approx(-0.1)