"""
Genome evolution and persistence for Vestigaea MVP.
"""
import json
import random
import math
import copy
from typing import Dict, Any, Tuple
from pathlib import Path

def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, x))

class Evolution:
    """Handles genome mutation and persistence between runs."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.genome_path = data_path / "genome.json"
        self.history_path = data_path / "genome.jsonl"
        self.milestone_path = data_path / "milestones.json"
        
        # Load or create initial genome
        self.current_genome = self.load_genome()
        
        # Load or create milestones
        self.milestones = self.load_milestones()
    
    def load_genome(self) -> Dict[str, Any]:
        """Load current genome from file."""
        try:
            with open(self.genome_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default genome if file missing or invalid
            return {
                "morphology": {"size": 0.9},
                "locomotion": {"type": "wade", "speed": 120},
                "metabolism": {"rate": 1.0, "stamina_max": 100},
                "sense": {"vision": {"range": 180, "fov_deg": 110}},
                "behavior": {"risk_tolerance": 0.3, "memory_span": 2},
                "verbs": ["move", "forage", "hide"]
            }
    
    def load_milestones(self) -> Dict[str, bool]:
        """Load milestone flags from file."""
        try:
            with open(self.milestone_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"first_survival": False}
    
    def save_genome(self, genome: Dict[str, Any]):
        """Save current genome to file."""
        with open(self.genome_path, "w") as f:
            json.dump(genome, f, indent=2)
    
    def append_to_history(self, genome: Dict[str, Any], fitness: float):
        """Append genome to history file with fitness score."""
        entry = {
            "genome": genome,
            "fitness": fitness
        }
        with open(self.history_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def save_milestones(self):
        """Save milestone flags to file."""
        with open(self.milestone_path, "w") as f:
            json.dump(self.milestones, f, indent=2)
    
    def mutate(self, genome: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create mutated copy of genome with sensible value ranges.
        Returns: new genome
        """
        new_genome = copy.deepcopy(genome)
        
        # Vision range: 80-280 pixels
        new_genome["sense"]["vision"]["range"] = clamp(
            genome["sense"]["vision"]["range"] * random.gauss(1.0, 0.05),
            80, 280
        )
        
        # FOV: 60-150 degrees
        new_genome["sense"]["vision"]["fov_deg"] = clamp(
            genome["sense"]["vision"]["fov_deg"] * random.gauss(1.0, 0.05),
            60, 150
        )
        
        # Risk tolerance: 0-1
        new_genome["behavior"]["risk_tolerance"] = clamp(
            genome["behavior"]["risk_tolerance"] + random.gauss(0, 0.04),
            0, 1
        )
        
        # Speed: 70-200 pixels/sec
        new_genome["locomotion"]["speed"] = clamp(
            genome["locomotion"]["speed"] * random.gauss(1.0, 0.05),
            70, 200
        )
        
        # Stamina max: 60-150
        new_genome["metabolism"]["stamina_max"] = clamp(
            genome["metabolism"]["stamina_max"] * random.gauss(1.0, 0.05),
            60, 150
        )
        
        return new_genome
    
    def get_mutation_deltas(self, old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate relative changes in genome values.
        Returns: dict of stat name -> percent change
        """
        deltas = {}
        # Helper to safely get old baseline when callers may have passed a shallow-copied
        # genome (which can accidentally mutate the 'old' structure). If the old and new
        # values are identical we'll fall back to self.current_genome when available.
        def _baseline(old_val, new_val, path_keys):
            if old_val == new_val and hasattr(self, "current_genome"):
                # Walk self.current_genome for the requested path
                node = self.current_genome
                try:
                    for k in path_keys:
                        node = node[k]
                    return node
                except Exception:
                    return old_val
            return old_val

        # Vision range percent change
        old_vision = _baseline(old["sense"]["vision"]["range"], new["sense"]["vision"]["range"],
                               ["sense", "vision", "range"])
        deltas["vision_range_pct"] = (
            new["sense"]["vision"]["range"] / 
            old_vision
        ) - 1.0
        
        # Risk tolerance absolute change
        old_risk = _baseline(old["behavior"]["risk_tolerance"], new["behavior"]["risk_tolerance"],
                             ["behavior", "risk_tolerance"])
        deltas["risk_tolerance"] = (
            new["behavior"]["risk_tolerance"] - 
            old_risk
        )
        
        # Speed percent change
        old_speed = _baseline(old["locomotion"]["speed"], new["locomotion"]["speed"],
                              ["locomotion", "speed"])
        deltas["speed_pct"] = (
            new["locomotion"]["speed"] / 
            old_speed
        ) - 1.0
        
        # Stamina max percent change
        old_stamina = _baseline(old["metabolism"]["stamina_max"], new["metabolism"]["stamina_max"],
                                ["metabolism", "stamina_max"])
        deltas["stamina_pct"] = (
            new["metabolism"]["stamina_max"] / 
            old_stamina
        ) - 1.0
        
        return deltas
    
    def evolve(self, fitness: float) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Create next generation genome based on fitness.
        Returns: (new genome, stat deltas)
        """
        # Record current genome and fitness
        self.append_to_history(self.current_genome, fitness)
        
        # Create mutated genome
        new_genome = self.mutate(self.current_genome)
        
        # Calculate deltas for display
        deltas = self.get_mutation_deltas(self.current_genome, new_genome)
        
        # Update current genome
        self.current_genome = new_genome
        self.save_genome(new_genome)
        
        return new_genome, deltas