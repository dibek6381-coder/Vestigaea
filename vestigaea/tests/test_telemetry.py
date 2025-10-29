"""Tests for telemetry event recording and fitness calculation."""

import pytest

from vestigaea.core.events import bus
from vestigaea.game.telemetry import TelemetrySystem


def test_telemetry_records_and_fitness(monkeypatch):
    """TelemetrySystem should aggregate events into a positive fitness score."""
    bus.clear()
    telemetry = TelemetrySystem()

    # Pretend the run started 10 seconds ago
    telemetry.run_start_time -= 10

    telemetry.record_forage({"calories": 5})
    telemetry.record_injury({"severity": 0.1})
    telemetry.record_predator({"distance": 10})
    telemetry.record_time_alive(10.0)

    fitness = telemetry.calculate_fitness()
    expected = 0.02 * 10 + 1.2 * 5 - 30 * 0.1 + 2 * 1
    assert fitness == pytest.approx(expected)

    telemetry.clear()
    assert telemetry.events == []
    assert telemetry.calculate_fitness() == pytest.approx(0.0, abs=1e-3)

