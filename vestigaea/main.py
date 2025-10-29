"""
Vestigaea MVP - Main Entry Point
"""
import sys
import pygame
import json
import random
from enum import Enum, auto
from pathlib import Path

from vestigaea.core.timer import FixedTimestep
from vestigaea.core.ecs import World
from vestigaea.core.events import bus
from game.entities import create_player, create_predator

# Constants
SCREEN_WIDTH = 1024  # 64 tiles * 16 pixels
SCREEN_HEIGHT = 1024
TILE_SIZE = 16
WORLD_SIZE = 64
TARGET_FPS = 60
SIM_RATE = 30  # Hz

class GameState(Enum):
    PLAYING = auto()
    POSTRUN = auto()
    RESTART = auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Vestigaea MVP")
        self.clock = pygame.time.Clock()
        
        # Fixed timestep for simulation
        self.timer = FixedTimestep(1.0 / SIM_RATE)
        
        # ECS world
        self.world = World()
        
        # Game state
        self.state = GameState.PLAYING
        self.running = True
        self.run_time = 0
        self.max_run_time = 120  # 120 seconds max per run
        self.cause_of_death = None
        
        # Import systems
        from game.world import WorldSystem
        from game.perception import VisionSystem
        from game.verbs import VerbSystem
        from game.ai import UtilityAI
        from game.telemetry import TelemetrySystem
        from game.evolution import Evolution
        from ui.hud import HUD
        from ui.postrun import PostRunScreen
        
        # Initialize systems
        self.world_system = WorldSystem(WORLD_SIZE, WORLD_SIZE)
        self.vision_system = VisionSystem()
        self.verb_system = VerbSystem()
        self.ai_system = UtilityAI()
        self.telemetry_system = TelemetrySystem()
        
        self.world.register_system(self.world_system)
        self.world.register_system(self.vision_system)
        self.world.register_system(self.verb_system)
        self.world.register_system(self.ai_system)
        
        # Load initial genome and create entities
        self.genome = self.load_genome()
        self.evolution = Evolution(Path(__file__).parent / "data")
        
        # UI components
        self.hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.post_run = PostRunScreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Create initial entities
        self.spawn_entities()
        
        self.world_system = WorldSystem(WORLD_SIZE, WORLD_SIZE)
        self.vision_system = VisionSystem()
        self.verb_system = VerbSystem()
        self.ai_system = UtilityAI()
        self.telemetry_system = TelemetrySystem()
        
        self.world.register_system(self.world_system)
        self.world.register_system(self.vision_system)
        self.world.register_system(self.verb_system)
        self.world.register_system(self.ai_system)
        
        # Load initial genome and create entities
        self.genome = self.load_genome()
        self.evolution = Evolution(Path(__file__).parent / "data")
        
        # UI
        self.hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.post_run = PostRunScreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Create initial entities
        self.spawn_entities()
        
        # Subscribe to events
        bus.subscribe("injury", self.handle_injury)
    
    def load_genome(self):
        """Load genome from JSON file."""
        genome_path = Path(__file__).parent / "data" / "genome.json"
        with open(genome_path) as f:
            return json.load(f)
            
    def spawn_entities(self):
        """Create player and predator entities."""
        # Spawn player in center
        self.player = create_player(
            self.world,
            self.genome,
            SCREEN_WIDTH/2,
            SCREEN_HEIGHT/2
        )
        
        # Spawn predator at random edge
        edge = random.randint(0, 3)
        if edge == 0:  # Top
            x = random.uniform(0, SCREEN_WIDTH)
            y = 32
        elif edge == 1:  # Right
            x = SCREEN_WIDTH - 32
            y = random.uniform(0, SCREEN_HEIGHT)
        elif edge == 2:  # Bottom
            x = random.uniform(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT - 32
        else:  # Left
            x = 32
            y = random.uniform(0, SCREEN_HEIGHT)
            
        self.predator = create_predator(self.world, x, y)
    
    def handle_injury(self, data):
        """Handle injury events."""
        if data["entity_id"] == self.player.id:
            # Update player status
            status = self.world.get_component(self.player.id, "status")
            if status:
                status["injured"] = True
                status["injury_severity"] += data["severity"]
                
                # Check for death
                if status["injury_severity"] >= 1.0:
                    self.cause_of_death = "Fatal injury from predator"
                    self.end_run()
    
    def handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Toggle vision overlay with Q
                elif event.key == pygame.K_q:
                    bus.publish("toggle_vision")
                # Forage with E
                elif event.key == pygame.K_e:
                    bus.publish("forage")
    
    def update(self, dt):
        """Update game state."""
        # Get movement input
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]
        if dx != 0 or dy != 0:
            bus.publish("move", {"dx": dx, "dy": dy})
        
        # Update ECS world
        self.world.update(dt)
    
    def render(self):
        """Render current game state."""
        self.screen.fill((0, 40, 0))  # Dark green background
        
        if self.state == GameState.PLAYING:
            # Render world and entities
            self.world_system.render(self.screen)
            
            # Get player data for HUD
            metabolism = self.world.get_component(self.player.id, "metabolism")
            player_data = {
                "stamina": metabolism["stamina"],
                "stamina_max": metabolism["stamina_max"],
                "calories": metabolism["calories"]
            }
            
            # Render HUD
            self.hud.render(
                screen=self.screen,
                player_data=player_data,
                time_remaining=self.max_run_time - self.run_time,
                vision_enabled=self.vision_system.show_debug
            )
            
        elif self.state == GameState.POSTRUN:
            # Calculate fitness and evolve
            fitness = self.telemetry_system.calculate_fitness()
            new_genome, deltas = self.evolution.evolve(fitness)
            
            # Render post-run screen
            self.post_run.render(
                screen=self.screen,
                fitness=fitness,
                deltas=deltas,
                time_alive=self.run_time,
                cause_of_death=self.cause_of_death
            )
        
        pygame.display.flip()
    
    def end_run(self):
        """End current run and transition to post-run screen."""
        self.state = GameState.POSTRUN
        
        # Record time alive event
        self.telemetry_system.events.append({
            "name": "time_alive",
            "data": {"seconds": self.run_time}
        })
        
        # Check for first survival milestone
        if self.run_time >= self.max_run_time:
            self.evolution.milestones["first_survival"] = True
            self.evolution.save_milestones()
    
    def restart_run(self):
        """Start a new run with evolved genome."""
        self.state = GameState.PLAYING
        self.run_time = 0
        self.cause_of_death = None
        
        # Clear old entities
        self.world = World()
        
        # Re-register systems
        self.world.register_system(self.world_system)
        self.world.register_system(self.vision_system)
        self.world.register_system(self.verb_system)
        self.world.register_system(self.ai_system)
        
        # Reset telemetry
        self.telemetry_system.clear()
        
        # Spawn new entities
        self.spawn_entities()
    
    def run(self):
        """Main game loop."""
        prev_time = pygame.time.get_ticks() / 1000.0
        
        while self.running:
            # Calculate frame time
            curr_time = pygame.time.get_ticks() / 1000.0
            frame_time = curr_time - prev_time
            prev_time = curr_time
            
            # Handle input
            self.handle_events()
            
            if self.state == GameState.PLAYING:
                # Update run time
                self.run_time += frame_time
                
                # Check for timeout
                if self.run_time >= self.max_run_time:
                    self.cause_of_death = "Reached maximum lifespan"
                    self.end_run()
                
                # Check for starvation
                metabolism = self.world.get_component(self.player.id, "metabolism")
                if metabolism and metabolism["calories"] <= 0:
                    self.cause_of_death = "Starvation"
                    self.end_run()
                
                # Fixed timestep updates
                self.timer.update(frame_time, self.update)
                
            elif self.state == GameState.POSTRUN:
                # Wait for space to restart
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    self.restart_run()
            
            # Render at display refresh rate
            self.render()
            
            # Cap frame rate
            self.clock.tick(TARGET_FPS)

def main():
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()