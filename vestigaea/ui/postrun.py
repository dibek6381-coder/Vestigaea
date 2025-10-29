"""
Post-run results screen UI for Vestigaea MVP.
"""
import pygame
from typing import Dict, Tuple, Optional

class PostRunScreen:
    """
    Displays run results, fitness score, and genome mutations.
    """
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        
        # UI colors
        self.colors = {
            "background": (20, 20, 20),
            "text": (220, 220, 220),
            "highlight": (100, 200, 100),
            "positive": (100, 255, 100),
            "negative": (255, 100, 100)
        }
        
        # Fonts
        pygame.font.init()
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.body_font = pygame.font.Font(None, 32)
        except pygame.error:
            # Fallback to default font
            self.title_font = pygame.font.SysFont(None, 48)
            self.body_font = pygame.font.SysFont(None, 32)
    
    def format_delta(self, name: str, value: float) -> Tuple[str, pygame.Color]:
        """Format a genome delta value with color coding."""
        if "pct" in name:
            # Percentage change
            text = f"{name.replace('_pct', '')}: {value*100:+.1f}%"
        else:
            # Absolute change
            text = f"{name}: {value:+.3f}"
        
        # Color based on positive/negative
        color = self.colors["positive"] if value > 0 else self.colors["negative"]
        return text, color
    
    def render(self, screen: pygame.Surface, fitness: float, 
               deltas: Dict[str, float], time_alive: float,
               cause_of_death: Optional[str] = None):
        """
        Render the post-run screen.
        
        Args:
            screen: Pygame surface to render to
            fitness: Final fitness score
            deltas: Genome mutation changes
            time_alive: Seconds survived
            cause_of_death: Optional death reason
        """
        # Clear screen
        screen.fill(self.colors["background"])
        
        # Title
        title = self.title_font.render("Run Complete", True, self.colors["text"])
        screen.blit(title, (
            self.width//2 - title.get_width()//2,
            50
        ))
        
        # Time alive
        time_text = self.body_font.render(
            f"Survived: {time_alive:.1f} seconds", 
            True, self.colors["text"]
        )
        screen.blit(time_text, (
            self.width//2 - time_text.get_width()//2,
            120
        ))
        
        # Cause of death
        if cause_of_death:
            death_text = self.body_font.render(
                f"Cause: {cause_of_death}",
                True, self.colors["text"]
            )
            screen.blit(death_text, (
                self.width//2 - death_text.get_width()//2,
                160
            ))
        
        # Fitness score
        fitness_text = self.title_font.render(
            f"Fitness: {fitness:.1f}",
            True, self.colors["highlight"]
        )
        screen.blit(fitness_text, (
            self.width//2 - fitness_text.get_width()//2,
            220
        ))
        
        # Genome mutations
        mutation_title = self.body_font.render(
            "Mutations for Next Generation:",
            True, self.colors["text"]
        )
        screen.blit(mutation_title, (
            self.width//2 - mutation_title.get_width()//2,
            300
        ))
        
        y = 350
        for name, value in deltas.items():
            text, color = self.format_delta(name, value)
            surf = self.body_font.render(text, True, color)
            screen.blit(surf, (
                self.width//2 - surf.get_width()//2,
                y
            ))
            y += 40
        
        # Continue prompt
        prompt = self.body_font.render(
            "Press SPACE to continue",
            True, self.colors["text"]
        )
        screen.blit(prompt, (
            self.width//2 - prompt.get_width()//2,
            self.height - 100
        ))