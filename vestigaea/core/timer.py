"""
Fixed timestep helpers for Vestigaea MVP.
Decouples simulation rate from render framerate.
"""
from typing import Optional, Callable

class FixedTimestep:
    """
    Manages fixed timestep updates independent of render framerate.
    Uses an accumulator pattern to ensure stable simulation.
    """
    def __init__(self, dt: float = 1/30):
        """
        Initialize with desired fixed timestep (default 30Hz).
        
        Args:
            dt: Fixed timestep duration in seconds
        """
        self.dt = dt
        self.accumulator: float = 0.0
        
    def update(self, frame_time: float, update_fn: Callable[[float], None]) -> int:
        """
        Update simulation with fixed timestep while frame time varies.
        
        Args:
            frame_time: Elapsed time since last frame in seconds
            update_fn: Function to call for each fixed update step
            
        Returns:
            Number of physics steps that occurred
        """
        self.accumulator += frame_time
        steps = 0
        
        # While we have enough accumulated time, run fixed updates
        while self.accumulator >= self.dt:
            update_fn(self.dt)
            self.accumulator -= self.dt
            steps += 1
            
        return steps
    
    def alpha(self) -> float:
        """
        Get interpolation alpha (0-1) for rendering between physics steps.
        """
        return self.accumulator / self.dt