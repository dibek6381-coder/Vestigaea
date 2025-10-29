"""
Action system (verbs) for Vestigaea MVP.
"""
from typing import Dict, Any, Callable
import math

from vestigaea.core.ecs import System
from vestigaea.core.events import bus

class VerbSystem(System):
    """Handles execution of verbs (move, forage, hide)."""
    def __init__(self):
        super().__init__()
        self._verbs: Dict[str, Callable] = {
            "move": self._move,
            "forage": self._forage,
            "hide": self._hide
        }
        
        # Subscribe to verb events
        bus.subscribe("move", self.handle_move)
        bus.subscribe("forage", self.handle_forage)
        bus.subscribe("hide", self.handle_hide)
    
    def _move(self, entity_id: int, data: Dict[str, Any]) -> bool:
        """
        Move an entity, consuming stamina based on terrain.
        
        Args:
            entity_id: The entity to move
            data: Must contain dx, dy for direction
        """
        transform = self.world.get_component(entity_id, "transform")
        metabolism = self.world.get_component(entity_id, "metabolism")
        genome = self.world.get_component(entity_id, "genome")
        
        if not all([transform, metabolism, genome]):
            return False
        
        # Get movement vector
        dx = data.get("dx", 0)
        dy = data.get("dy", 0)
        if dx == 0 and dy == 0:
            return False
            
        # Normalize vector
        length = math.sqrt(dx*dx + dy*dy)
        dx /= length
        dy /= length
        
        # Scale by speed from genome
        speed = genome["locomotion"]["speed"]
        dx *= speed * data.get("dt", 1/30)  # Default 30Hz
        dy *= speed * data.get("dt", 1/30)
        
        # Get new position
        new_x = transform["x"] + dx
        new_y = transform["y"] + dy
        
        # Check collision
        world_system = next(
            (sys for sys in self.world._systems 
             if sys.__class__.__name__ == "WorldSystem"), 
            None
        )
        
        if world_system and world_system.is_walkable(
            int(new_x/16), int(new_y/16)):  # 16 = tile size
            
            # Get terrain movement cost
            cost = world_system.get_movement_cost(
                int(new_x/16), int(new_y/16))
            
            # Apply stamina cost
            base_cost = 0.1  # Base stamina cost per move
            stamina_cost = base_cost * cost
            
            if metabolism["stamina"] >= stamina_cost:
                # Move is valid
                transform["x"] = new_x
                transform["y"] = new_y
                transform["direction"] = math.atan2(dy, dx)
                metabolism["stamina"] -= stamina_cost
                return True
            
        return False
    
    def _forage(self, entity_id: int, _: Dict[str, Any]) -> bool:
        """
        Attempt to forage at current position.
        """
        transform = self.world.get_component(entity_id, "transform")
        if not transform:
            return False
            
        # Notify world system of forage attempt
        bus.publish("forage", {
            "entity_id": entity_id,
            "x": int(transform["x"]/16),
            "y": int(transform["y"]/16)
        })
        return True
    
    def _hide(self, entity_id: int, _: Dict[str, Any]) -> bool:
        """
        Enter hiding state, reducing detection but also movement.
        """
        status = self.world.get_component(entity_id, "status")
        if not status:
            return False
            
        status["hiding"] = True
        return True
    
    def handle_move(self, data):
        """Handle move event from input system."""
        # Get player entity
        player = next(iter(self.world.get_entities_with("player")))
        self._move(player, data)
    
    def handle_forage(self, _):
        """Handle forage event from input system."""
        player = next(iter(self.world.get_entities_with("player")))
        self._forage(player, {})
    
    def handle_hide(self, _):
        """Handle hide event from input system."""
        player = next(iter(self.world.get_entities_with("player")))
        self._hide(player, {})
    
    def update(self, dt: float):
        """Update all entities with verbs."""
        # Handle automatic stamina recovery
        entities = self.world.get_entities_with("metabolism")
        for entity_id in entities:
            metabolism = self.world.get_component(entity_id, "metabolism")
            if metabolism["stamina"] < metabolism["stamina_max"]:
                # Recover faster while hiding
                status = self.world.get_component(entity_id, "status")
                recovery_rate = 2.0 if status and status["hiding"] else 1.0
                metabolism["stamina"] = min(
                    metabolism["stamina"] + recovery_rate * dt,
                    metabolism["stamina_max"]
                )
