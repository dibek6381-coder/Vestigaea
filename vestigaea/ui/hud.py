"""
In-game HUD elements for Vestigaea MVP.
"""
import pygame
from typing import Dict, Any, Optional, Tuple

class HUD:
    """
    Displays stamina, hunger, and time remaining during gameplay.
    """
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        
        # UI colors
        self.colors = {
            "bar_bg": (40, 40, 40),
            "stamina": (100, 200, 100),
            "hunger": (200, 180, 60),
            "text": (220, 220, 220)
        }
        
        # Bar dimensions
        self.bar_width = 200
        self.bar_height = 20
        self.bar_padding = 10
        
        # Initialize font
        pygame.font.init()
        try:
            self.font = pygame.font.Font(None, 24)
        except pygame.error:
            self.font = pygame.font.SysFont(None, 24)
    
    def render_bar(self, screen: pygame.Surface, x: int, y: int,
                  value: float, maximum: float, color: Tuple[int, int, int],
                  label: str):
        """
        Render a status bar with label.
        
        Args:
            screen: Surface to render to
            x, y: Top-left position
            value: Current value
            maximum: Maximum value
            color: Bar fill color (RGB)
            label: Bar label
        """
        # Background
        pygame.draw.rect(screen, self.colors["bar_bg"],
                        (x, y, self.bar_width, self.bar_height))
        
        # Fill bar
        fill_width = int((value / maximum) * self.bar_width)
        if fill_width > 0:
            pygame.draw.rect(screen, color,
                           (x, y, fill_width, self.bar_height))
        
        # Label
        label_surf = self.font.render(
            f"{label}: {int(value)}/{int(maximum)}", 
            True, self.colors["text"]
        )
        screen.blit(label_surf, (
            x + self.bar_width//2 - label_surf.get_width()//2,
            y + self.bar_height//2 - label_surf.get_height()//2
        ))
    
    def render(self, screen: pygame.Surface, 
               player_data: Dict[str, Any],
               time_remaining: float,
               vision_enabled: bool):
        """
        Render the HUD.
        
        Args:
            screen: Surface to render to
            player_data: Dict with stamina and hunger values
            time_remaining: Seconds left in run
            vision_enabled: Whether vision cone is visible
        """
        # Stamina bar
        self.render_bar(
            screen=screen,
            x=10,
            y=10,
            value=player_data["stamina"],
            maximum=player_data["stamina_max"],
            color=self.colors["stamina"],
            label="Stamina"
        )
        
        # Hunger bar
        self.render_bar(
            screen=screen,
            x=10,
            y=40,
            value=player_data["calories"],
            maximum=100,  # Max calories
            color=self.colors["hunger"],
            label="Energy"
        )
        
        # Time remaining
        time_text = self.font.render(
            f"Time: {int(time_remaining)}s",
            True, self.colors["text"]
        )
        screen.blit(time_text, (10, 70))
        
        # Vision cone status
        vision_text = self.font.render(
            "Vision Cone: [Q] " + ("ON" if vision_enabled else "OFF"),
            True, self.colors["text"]
        )
        screen.blit(vision_text, (10, 100))
