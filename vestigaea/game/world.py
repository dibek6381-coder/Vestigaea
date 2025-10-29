"""
World, tiles, and resource management for Vestigaea MVP.
"""
from enum import Enum
from typing import List, Tuple, Optional
import random
import math
import pygame
from dataclasses import dataclass

from vestigaea.core.ecs import System
from vestigaea.core.events import bus

class TileType(Enum):
    WATER = 0  # Shallow water, wadeable but slows
    LAND = 1   # Basic walkable terrain
    MUD = 2    # Slower movement, good for hiding
    REEDS = 3  # Cover from predators

@dataclass
class ResourceNode:
    """Represents a forageable resource in the world."""
    x: int
    y: int
    calories: float
    respawn_time: float = 0.0

class WorldSystem(System):
    """Manages the world grid, collision, and resource spawning."""
    def __init__(self, width: int, height: int, num_resources: int = 40):
        super().__init__()
        self.width = width
        self.height = height
        self.num_resources = num_resources
        
        # Initialize tile grid
        self.tiles: List[List[TileType]] = []
        self.generate_terrain()
        
        # Resource management
        self.resources: List[Optional[ResourceNode]] = []
        self.spawn_resources()
        
        # Subscribe to events
        bus.subscribe("forage", self.handle_forage)
    
    def generate_terrain(self):
        """Generate world tiles with varying terrain types."""
        self.tiles = [[TileType.LAND for _ in range(self.width)] 
                     for _ in range(self.height)]
        
        # Add water around edges
        for y in range(self.height):
            for x in range(self.width):
                if (x < 3 or x > self.width - 4 or 
                    y < 3 or y > self.height - 4):
                    self.tiles[y][x] = TileType.WATER
        
        # Add random mud patches
        for _ in range(self.width * self.height // 10):
            x = random.randint(3, self.width - 4)
            y = random.randint(3, self.height - 4)
            self.tiles[y][x] = TileType.MUD
        
        # Add reed clusters
        for _ in range(self.width * self.height // 15):
            x = random.randint(3, self.width - 4)
            y = random.randint(3, self.height - 4)
            self.tiles[y][x] = TileType.REEDS
    
    def spawn_resources(self):
        """Spawn initial resource nodes."""
        self.resources.clear()
        valid_spots = []
        
        # Find valid spawn locations (land or reeds)
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] in (TileType.LAND, TileType.REEDS):
                    valid_spots.append((x, y))
        
        # Spawn resources
        for _ in range(self.num_resources):
            if valid_spots:
                x, y = random.choice(valid_spots)
                valid_spots.remove((x, y))
                self.resources.append(ResourceNode(
                    x=x, 
                    y=y,
                    calories=random.uniform(10, 30)
                ))
    
    def get_movement_cost(self, x: int, y: int) -> float:
        """Get stamina cost multiplier for moving through tile."""
        tile = self.tiles[y][x]
        costs = {
            TileType.LAND: 1.0,
            TileType.WATER: 2.0,
            TileType.MUD: 1.8,
            TileType.REEDS: 1.2
        }
        return costs[tile]
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile can be moved into."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def find_resources_in_range(self, x: int, y: int, radius: int) -> List[ResourceNode]:
        """Find resource nodes within range of a position."""
        in_range = []
        for resource in self.resources:
            if resource is None:
                continue
            dx = abs(resource.x - x)
            dy = abs(resource.y - y)
            if dx <= radius and dy <= radius:
                in_range.append(resource)
        return in_range
    
    def handle_forage(self, data):
        """Handle forage attempts from entities."""
        # Expected data: {"entity_id": int, "x": int, "y": int}
        if not data:
            return
            
        x, y = data["x"], data["y"]
        resources = self.find_resources_in_range(x, y, 1)
        
        if resources:
            # Take the closest resource
            resource = resources[0]
            # Remove it from the world
            idx = self.resources.index(resource)
            self.resources[idx] = None
            # Start respawn timer
            resource.respawn_time = 30.0  # 30 seconds to respawn
            # Notify success
            bus.publish("forage_success", {
                "entity_id": data["entity_id"],
                "calories": resource.calories
            })
    
    def update(self, dt: float):
        """Update resource respawn timers."""
        for i, resource in enumerate(self.resources):
            if resource is None:
                continue
            if resource.respawn_time > 0:
                resource.respawn_time -= dt
                if resource.respawn_time <= 0:
                    # Respawn at a random valid location
                    valid_spots = []
                    for y in range(self.height):
                        for x in range(self.width):
                            if (self.tiles[y][x] in (TileType.LAND, TileType.REEDS) and
                                all(r is None or (r.x != x and r.y != y) 
                                    for r in self.resources)):
                                valid_spots.append((x, y))
                    
                    if valid_spots:
                        x, y = random.choice(valid_spots)
                        resource.x = x
                        resource.y = y
                        resource.respawn_time = 0
                        resource.calories = random.uniform(10, 30)
    
    def render(self, screen: pygame.Surface):
        """Render world tiles, resources, and entities."""
        TILE_SIZE = 16  # Must match main.py
        
        # Render tiles
        tile_colors = {
            TileType.WATER: (50, 100, 150),
            TileType.LAND: (100, 150, 50),
            TileType.MUD: (120, 100, 60),
            TileType.REEDS: (150, 160, 40)
        }
        
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(
                    screen,
                    tile_colors[self.tiles[y][x]],
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        
        # Render resources
        for resource in self.resources:
            if resource is None or resource.respawn_time > 0:
                continue
            pygame.draw.circle(
                screen,
                (200, 180, 50),  # Yellow for food
                (resource.x * TILE_SIZE + TILE_SIZE//2,
                 resource.y * TILE_SIZE + TILE_SIZE//2),
                4
            )
        
        # Render entities
        entities = self.world.get_entities_with("transform")
        for entity_id in entities:
            transform = self.world.get_component(entity_id, "transform")
            if not transform:
                continue
            
            # Determine entity color and size
            color = (200, 200, 200)  # Default white
            size = 8
            
            if self.world.get_component(entity_id, "player"):
                color = (50, 200, 50)  # Green for player
                size = 6
            elif self.world.get_component(entity_id, "predator"):
                color = (200, 50, 50)  # Red for predator
                size = 8
            
            # Draw entity
            pygame.draw.circle(
                screen,
                color,
                (transform["x"], transform["y"]),
                size
            )
            
            # Draw direction indicator
            end_x = transform["x"] + math.cos(transform["direction"]) * size
            end_y = transform["y"] + math.sin(transform["direction"]) * size
            pygame.draw.line(
                screen,
                color,
                (transform["x"], transform["y"]),
                (end_x, end_y),
                2
            )