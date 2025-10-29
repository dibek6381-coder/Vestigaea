"""Vision-based perception system for Vestigaea MVP."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from vestigaea.core.ecs import System
from vestigaea.core.events import bus

@dataclass
class Stimulus:
    """Perception stimulus tuple."""
    kind: str  # "food", "predator", or "shelter"
    dir_rad: float  # Direction in radians
    intensity: float  # 0-1 scale
    recency_s: float  # Time since last seen

class VisionSystem(System):
    """Handles vision cone perception for all entities with vision."""
    def __init__(self):
        super().__init__()
        self.show_debug = False  # Toggle with Q key
        bus.subscribe("toggle_vision", lambda _: self.toggle_debug())
    
    def toggle_debug(self):
        """Toggle vision cone visualization."""
        self.show_debug = not self.show_debug
    
    def update(self, dt: float):
        """Update perception for all entities with vision."""
        # Get all entities with Transform and Vision components
        entities = self.world.get_entities_with("transform", "vision")
        
        for entity_id in entities:
            transform = self.world.get_component(entity_id, "transform")
            vision = self.world.get_component(entity_id, "vision")
            
            if not transform or not vision:
                continue
            
            # Update vision state
            stimuli = self.get_stimuli(
                entity_id=entity_id,
                x=transform["x"],
                y=transform["y"],
                direction=transform["direction"],
                range_px=vision["range"],
                fov_deg=vision["fov_deg"]
            )
            
            # Store new stimuli and decay old ones
            if "stimuli" not in vision:
                vision["stimuli"] = []
            
            # Decay existing stimuli
            for stim in vision["stimuli"]:
                stim.recency_s += dt
            
            # Filter out old stimuli (older than memory_span)
            genome = self.world.get_component(entity_id, "genome")
            if genome:
                memory_span = genome["behavior"]["memory_span"]
                vision["stimuli"] = [
                    s for s in vision["stimuli"] 
                    if s.recency_s <= memory_span
                ]
            
            # Add new stimuli
            vision["stimuli"].extend(stimuli)
    
    def get_stimuli(
        self,
        entity_id: int,
        x: float,
        y: float,
        direction: float,
        range_px: float,
        fov_deg: float,
    ) -> List[Stimulus]:
        """
        Get all stimuli visible from a position within vision cone.
        
        Args:
            x, y: Observer position
            direction: Forward direction in radians
            range_px: Vision range in pixels
            fov_deg: Field of view in degrees
        """
        stimuli = []
        
        # Convert FOV to radians
        fov_rad = math.radians(fov_deg)
        half_fov = fov_rad / 2
        
        # Get all entities that could be visible
        entities = self.world.get_entities_with("transform")

        for observed_id in entities:
            if observed_id == entity_id:
                continue

            transform = self.world.get_component(observed_id, "transform")
            
            # Calculate angle and distance
            dx = transform["x"] - x
            dy = transform["y"] - y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > range_px:
                continue
                
            # Calculate angle to target
            angle = math.atan2(dy, dx)
            # Get smallest angle difference
            angle_diff = abs((angle - direction + math.pi) % (2*math.pi) - math.pi)
            
            # Check if in FOV
            if angle_diff <= half_fov:
                # Determine stimulus type
                stim_type = "food"  # Default
                # Use explicit 'is not None' since components can be empty dicts
                if self.world.get_component(observed_id, "predator") is not None:
                    stim_type = "predator"
                elif self.world.get_component(observed_id, "shelter") is not None:
                    stim_type = "shelter"
                
                # Calculate intensity based on distance
                intensity = 1.0 - (dist / range_px)
                
                stimuli.append(Stimulus(
                    kind=stim_type,
                    dir_rad=angle,
                    intensity=intensity,
                    recency_s=0.0
                ))
        
        return stimuli
