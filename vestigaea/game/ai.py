"""
Utility-based AI for predator behavior in Vestigaea MVP.
"""
import math
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from vestigaea.core.ecs import System
from vestigaea.core.events import bus
from game.perception import Stimulus

@dataclass
class UtilityScore:
    """Scored action with context."""
    action: str
    score: float
    target_pos: Optional[tuple[float, float]] = None

class UtilityAI(System):
    """
    Utility-based decision making for predators.
    Uses same perception system as player for fairness.
    """
    def __init__(self):
        super().__init__()
        self.wander_timer = 0.0
        self.wander_interval = 3.0  # seconds between direction changes
    
    def score_actions(self, entity_id: int) -> List[UtilityScore]:
        """Score possible actions based on current state and perception."""
        scores = []
        
        # Get entity components
        transform = self.world.get_component(entity_id, "transform")
        vision = self.world.get_component(entity_id, "vision")
        status = self.world.get_component(entity_id, "status")
        
        if not all([transform, vision, status]):
            return scores
        
        # Score hunting if prey detected
        prey_stimulus = None
        for stimulus in vision.get("stimuli", []):
            if stimulus.kind == "player" and stimulus.recency_s < 1.0:
                prey_stimulus = stimulus
                break
        
        if prey_stimulus:
            # Convert stimulus direction to world position
            dx = math.cos(prey_stimulus.dir_rad)
            dy = math.sin(prey_stimulus.dir_rad)
            distance = (1.0 - prey_stimulus.intensity) * vision["range"]
            target_x = transform["x"] + dx * distance
            target_y = transform["y"] + dy * distance
            
            hunt_score = 0.8 + 0.2 * prey_stimulus.intensity
            scores.append(UtilityScore(
                action="hunt",
                score=hunt_score,
                target_pos=(target_x, target_y)
            ))
        
        # Score wandering (fallback behavior)
        wander_score = 0.2  # Low baseline score
        if status.get("wandering"):
            # Prefer to continue current wander
            wander_score += 0.1
        scores.append(UtilityScore(
            action="wander",
            score=wander_score
        ))
        
        return scores
    
    def execute_action(self, entity_id: int, action: UtilityScore, dt: float):
        """Execute the highest scoring action."""
        transform = self.world.get_component(entity_id, "transform")
        status = self.world.get_component(entity_id, "status")
        
        if not transform or not status:
            return
        
        if action.action == "hunt" and action.target_pos:
            # Move toward target
            target_x, target_y = action.target_pos
            dx = target_x - transform["x"]
            dy = target_y - transform["y"]
            
            # Normalize direction
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx /= length
                dy /= length
            
            # Check for attack range
            attack_range = 20  # pixels
            if length < attack_range:
                # Attack prey
                entities = self.world.get_entities_with("player")
                if entities:
                    player_id = next(iter(entities))
                    bus.publish("injury", {
                        "entity_id": player_id,
                        "severity": 0.3,
                        "source": entity_id
                    })
            
            # Move predator
            speed = 140  # Slightly faster than base player speed
            transform["x"] += dx * speed * dt
            transform["y"] += dy * speed * dt
            transform["direction"] = math.atan2(dy, dx)
            
            # Update status
            status["wandering"] = False
            
        elif action.action == "wander":
            # Update wander direction periodically
            if not status.get("wandering"):
                status["wandering"] = True
                status["wander_dx"] = math.cos(transform["direction"])
                status["wander_dy"] = math.sin(transform["direction"])
                self.wander_timer = 0
            
            self.wander_timer += dt
            if self.wander_timer >= self.wander_interval:
                # Change direction randomly
                angle = transform["direction"] + random.uniform(-math.pi/4, math.pi/4)
                status["wander_dx"] = math.cos(angle)
                status["wander_dy"] = math.sin(angle)
                self.wander_timer = 0
            
            # Move in wander direction
            speed = 80  # Slower wandering speed
            transform["x"] += status["wander_dx"] * speed * dt
            transform["y"] += status["wander_dy"] * speed * dt
            transform["direction"] = math.atan2(
                status["wander_dy"], 
                status["wander_dx"]
            )
    
    def update(self, dt: float):
        """Update all predator entities."""
        # Get all predator entities
        predators = self.world.get_entities_with("predator")
        
        for entity_id in predators:
            # Score and select action
            scores = self.score_actions(entity_id)
            if scores:
                best_action = max(scores, key=lambda s: s.score)
                self.execute_action(entity_id, best_action, dt)