"""Telemetry recording and fitness calculation for Vestigaea MVP."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from vestigaea.core.ecs import System
from vestigaea.core.events import bus

@dataclass
class TelemetryEvent:
    """Record of a gameplay event with timestamp."""
    name: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class TelemetrySystem(System):
    """Records and evaluates gameplay events."""
    def __init__(self):
        super().__init__()
        self.events: List[TelemetryEvent] = []
        self.run_start_time = time.time()
        
        # Subscribe to relevant events
        bus.subscribe("forage_success", self.record_forage)
        bus.subscribe("injury", self.record_injury)
        bus.subscribe("spotted_predator", self.record_predator)
    
    def record_forage(self, data: Dict[str, Any]) -> None:
        """Record successful foraging."""
        self.events.append(
            TelemetryEvent(
                name="forage",
                data={"cal": data["calories"]},
            )
        )

    def record_injury(self, data: Dict[str, Any]) -> None:
        """Record injury from predator."""
        self.events.append(
            TelemetryEvent(
                name="injury",
                data={"severity": data["severity"]},
            )
        )

    def record_predator(self, data: Dict[str, Any]) -> None:
        """Record predator sighting."""
        self.events.append(
            TelemetryEvent(
                name="spotted_predator",
                data={"distance": data["distance"]},
            )
        )

    def record_time_alive(self, seconds: float) -> None:
        """Store a dedicated event capturing the run duration."""

        self.events.append(
            TelemetryEvent(
                name="time_alive",
                data={"seconds": seconds},
            )
        )
    
    def calculate_fitness(self) -> float:
        """
        Calculate fitness score from recorded events.
        
        Formula:
        fitness = 0.02*t_alive + 1.2*calories - 30*inj_severity + 2*spots
        """
        time_alive = time.time() - self.run_start_time
        
        # Base time alive score
        fitness = 0.02 * time_alive
        
        # Sum up event contributions
        total_calories = 0
        total_injury = 0
        predator_spots = 0
        
        for event in self.events:
            if event.name == "forage":
                total_calories += event.data["cal"]
            elif event.name == "injury":
                total_injury += event.data["severity"]
            elif event.name == "spotted_predator":
                predator_spots += 1
        
        fitness += 1.2 * total_calories
        fitness -= 30.0 * total_injury
        fitness += 2.0 * predator_spots
        
        return max(0.0, fitness)

    def clear(self) -> None:
        """Reset telemetry for a new run."""
        self.events.clear()
        self.run_start_time = time.time()

