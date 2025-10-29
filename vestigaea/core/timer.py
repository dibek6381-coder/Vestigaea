"""Fixed timestep helpers for Vestigaea MVP."""

from __future__ import annotations

from typing import Callable


class FixedTimestep:
    """Manage fixed timestep updates independent of the render framerate."""

    def __init__(self, dt: float = 1 / 30) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.dt = dt
        self.accumulator: float = 0.0

    def update(self, frame_time: float, update_fn: Callable[[float], None]) -> int:
        """Advance the accumulator by ``frame_time`` and call ``update_fn``.

        The callback is executed once per whole ``dt`` that fits inside the
        accumulator.  The number of steps performed is returned for convenience
        (useful for tests and debugging overlays).
        """

        if frame_time < 0:
            raise ValueError("frame_time must not be negative")

        self.accumulator += frame_time
        steps = 0

        while self.accumulator >= self.dt:
            update_fn(self.dt)
            self.accumulator -= self.dt
            steps += 1

        return steps

    def alpha(self) -> float:
        """Return the interpolation factor between 0.0 and 1.0."""

        return min(1.0, max(0.0, self.accumulator / self.dt))

    def reset(self) -> None:
        """Clear the accumulator (useful when pausing or restarting)."""

        self.accumulator = 0.0

