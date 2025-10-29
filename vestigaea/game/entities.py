"""
Entity factories for spawning players and predators.
"""
import random
from typing import Dict, Any

from vestigaea.core.ecs import World

def create_player(world: World, genome: Dict[str, Any], x: float, y: float):
    """Create player entity with all required components."""
    player = world.create_entity()
    
    # Basic components
    world.add_component(player.id, "player", {})
    world.add_component(player.id, "transform", {
        "x": x,
        "y": y,
        "direction": 0.0
    })
    
    # Vision from genome
    world.add_component(player.id, "vision", {
        "range": genome["sense"]["vision"]["range"],
        "fov_deg": genome["sense"]["vision"]["fov_deg"],
        "stimuli": []
    })
    
    # Metabolism/stats
    world.add_component(player.id, "metabolism", {
        "stamina": genome["metabolism"]["stamina_max"],
        "stamina_max": genome["metabolism"]["stamina_max"],
        "calories": 50.0,  # Start with some energy
        "rate": genome["metabolism"]["rate"]
    })
    
    # Status flags
    world.add_component(player.id, "status", {
        "hiding": False,
        "injured": False,
        "injury_severity": 0.0
    })
    
    # Store genome for offspring
    world.add_component(player.id, "genome", genome)
    
    return player

def create_predator(world: World, x: float, y: float):
    """Create predator entity with AI behavior."""
    predator = world.create_entity()
    
    # Basic components
    world.add_component(predator.id, "predator", {})
    world.add_component(predator.id, "transform", {
        "x": x,
        "y": y,
        "direction": random.uniform(0, 6.28)  # Random initial direction
    })
    
    # Vision (better range than default player)
    world.add_component(predator.id, "vision", {
        "range": 240,  # Longer visual range
        "fov_deg": 120,  # Wider FOV
        "stimuli": []
    })
    
    # Status flags
    world.add_component(predator.id, "status", {
        "wandering": False,
        "wander_dx": 0.0,
        "wander_dy": 0.0,
        "hunt_cooldown": 0.0
    })
    
    return predator
