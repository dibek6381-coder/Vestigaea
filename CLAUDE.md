# CLAUDE.md — Vestigaea Codebase Guide

Vestigaea is a lightweight survival-evolution prototype written in Python. A
single game run lasts up to 120 seconds; at the end the player's genome is
mutated based on a telemetry-driven fitness score, and the next run begins.

---

## Repository Layout

```
Vestigaea/
├── CLAUDE.md                  # This file
├── README.md                  # Human-facing project overview
├── LICENSE                    # MIT
├── .gitignore
└── vestigaea/                 # Importable package (python -m vestigaea.main)
    ├── __init__.py
    ├── main.py                # Game class, main loop, GameState enum
    ├── core/                  # Reusable, game-agnostic infrastructure
    │   ├── ecs.py             # Entity, World, System base classes
    │   ├── events.py          # EventBus + module-level `bus` singleton
    │   └── timer.py           # FixedTimestep: decouples sim from render
    ├── game/                  # Game-specific systems and logic
    │   ├── ai.py              # UtilityAI: predator behaviour
    │   ├── entities.py        # create_player() / create_predator() factories
    │   ├── evolution.py       # Evolution class: genome mutation & persistence
    │   ├── perception.py      # VisionSystem: vision cones, Stimulus dataclass
    │   ├── telemetry.py       # TelemetrySystem: event recording, fitness calc
    │   ├── verbs.py           # VerbSystem: move, forage, hide actions
    │   └── world.py           # WorldSystem: tile grid, resource spawning
    ├── ui/
    │   ├── hud.py             # In-game heads-up display
    │   └── postrun.py         # Post-run results + mutation deltas screen
    ├── data/
    │   ├── genome.json        # Current genome (mutated in-place each run)
    │   ├── genome.jsonl       # Append-only history of all genomes + fitness
    │   └── milestones.json    # Boolean achievement flags (auto-created)
    └── tests/
        ├── conftest.py        # seed_rng, test_world, base_genome fixtures
        ├── test_core.py       # ECS + timer unit tests
        ├── test_evolution.py  # Genome mutation tests
        ├── test_perception.py # Vision system tests
        └── test_telemetry.py  # Telemetry + fitness tests
```

---

## Running the Project

```bash
# Launch the game (requires pygame)
python -m vestigaea.main

# Run all tests
pytest

# Linting / formatting (not enforced by CI, but follow these settings)
black --line-length 88 vestigaea/
ruff check vestigaea/
```

No `requirements.txt` or `pyproject.toml` exists yet. The only third-party
dependency is **pygame**. Install it with `pip install pygame`.

---

## Architecture

### Entity Component System (`core/ecs.py`)

All game objects are entities managed by a single `World` instance.

| Concept | Implementation |
|---|---|
| **Entity** | Dataclass with an integer `id` and a `components` dict |
| **Component** | Plain `Dict[str, Any]` stored by string key (e.g. `"metabolism"`) |
| **System** | Subclass of `System`; must implement `update(dt: float)` |

Key `World` methods:

```python
world.create_entity() -> Entity
world.add_component(entity_id, comp_type, data)
world.get_component(entity_id, comp_type) -> dict | None
world.remove_component(entity_id, comp_type)
world.destroy_entity(entity_id)
world.get_entities_with(*comp_types) -> Set[int]   # component query
world.register_system(system)                       # order matters
world.update(dt)                                    # updates all systems in order
```

Systems are updated in **registration order** — this is intentional for
determinism. Register systems in `Game.__init__` in the order they must run:
`WorldSystem → VisionSystem → VerbSystem → UtilityAI`.

### Event Bus (`core/events.py`)

A module-level singleton `bus` is the sole communication channel between
systems and the game loop. Import it anywhere with:

```python
from vestigaea.core.events import bus
```

API:

```python
bus.subscribe(event_type: str, callback: Callable) -> None
bus.unsubscribe(event_type: str, callback: Callable) -> None
bus.publish(event_type: str, data: Any | None = None) -> None
bus.clear(event_type: str | None = None) -> None   # use in tests
```

Currently published events:

| Event | Publisher | Payload |
|---|---|---|
| `"move"` | `Game.update` (keyboard) | `{"dx": int, "dy": int}` |
| `"forage"` | `Game.handle_events` (E key) | `None` |
| `"toggle_vision"` | `Game.handle_events` (Q key) | `None` |
| `"forage_success"` | `VerbSystem` | resource data dict |
| `"injury"` | `UtilityAI` | `{"entity_id": int, "severity": float}` |
| `"spotted_predator"` | `VisionSystem` | stimulus data |

Always call `bus.clear()` in tests that publish events to avoid cross-test
pollution (the conftest `seed_rng` fixture does not do this automatically).

### Fixed Timestep (`core/timer.py`)

`FixedTimestep` decouples physics (30 Hz) from rendering (60 FPS):

```python
timer = FixedTimestep(1.0 / SIM_RATE)   # dt = 1/30 s
timer.update(frame_time, callback)       # calls callback(dt) as many times as needed
timer.reset()                            # call on restart to clear accumulator
```

### Game Constants (`main.py`)

```python
SCREEN_WIDTH  = 1024   # pixels (64 tiles × 16 px)
SCREEN_HEIGHT = 1024
TILE_SIZE     = 16     # pixels per tile
WORLD_SIZE    = 64     # tiles per side
TARGET_FPS    = 60
SIM_RATE      = 30     # Hz — simulation fixed timestep
MAX_RUN_TIME  = 120    # seconds — hard cap per run
```

---

## Key Game Systems

### WorldSystem (`game/world.py`)

- Manages a 64×64 tile grid with tile types: `WATER`, `LAND`, `MUD`, `REEDS`.
- Tiles have movement cost multipliers (1.0–2.0).
- Handles procedural forage resource spawning and respawning.
- `render(screen)` draws tiles and resources.
- `reset()` regenerates the world for a new run (call before re-registering).

### VisionSystem / Perception (`game/perception.py`)

- Computes vision cones from entity position, range, and FOV (from genome).
- Produces `Stimulus` dataclass objects (kind: `"food"` | `"predator"` | ...).
- Stimuli decay over `memory_span` seconds (from genome `behavior` key).
- `show_debug` toggle (Q key) draws the vision cone overlay.

### VerbSystem (`game/verbs.py`)

- Subscribes to `"move"` and `"forage"` events.
- `move`: applies speed from genome locomotion, respects tile cost, clamps to screen.
- `forage`: spends stamina, emits `"forage_success"` if resource present.
- `hide`: reduces visibility (used by predator avoidance logic).

### UtilityAI (`game/ai.py`)

Utility-based AI for the predator entity:

- Evaluates two actions each tick: **hunt** (score ≈ 0.8–1.0 if prey visible)
  and **wander** (score ≈ 0.2).
- Hunts if player is within vision range; attacks at 20 px distance, publishing
  `"injury"` with severity 0.3.
- Wanders at 80 px/s when no prey is visible.

### TelemetrySystem (`game/telemetry.py`)

Records events during a run and computes fitness at run end:

```
fitness = 0.02 * time_alive
        + 1.2  * total_calories
        - 30   * injury_severity
        + 2    * predator_spots
```

Call `telemetry.clear()` on restart. `record_time_alive(seconds)` must be
called explicitly from `Game.end_run()`.

### Evolution (`game/evolution.py`)

Manages genome mutation between runs.

```python
evolution = Evolution(data_path: Path)
new_genome, deltas = evolution.evolve(fitness: float)
# evolve() → appends to history, mutates, saves, returns (genome, delta_dict)
```

Mutation uses Gaussian noise (~5% std for multiplicative traits,
absolute ±0.04 for `risk_tolerance`) with hard clamps:

| Gene | Range |
|---|---|
| `sense.vision.range` | 80 – 280 px |
| `sense.vision.fov_deg` | 60 – 150° |
| `behavior.risk_tolerance` | 0.0 – 1.0 |
| `locomotion.speed` | 70 – 200 px/s |
| `metabolism.stamina_max` | 60 – 150 |

---

## Genome Format (`data/genome.json`)

```json
{
  "morphology":  { "size": 0.9 },
  "locomotion":  { "type": "wade", "speed": 120 },
  "metabolism":  { "rate": 1.0, "stamina_max": 100 },
  "sense":       { "vision": { "range": 180, "fov_deg": 110 } },
  "behavior":    { "risk_tolerance": 0.3, "memory_span": 2 },
  "verbs":       ["move", "forage", "hide"]
}
```

`genome.json` is mutated in-place by `Evolution.save_genome()`. Do not
hand-edit it while the game is running. `genome.jsonl` and `milestones.json`
are auto-created in `vestigaea/data/` on first run.

---

## Entity Factories (`game/entities.py`)

```python
player   = create_player(world, genome, x, y)   # adds position, metabolism, status, vision comps
predator = create_predator(world, x, y)          # adds position, ai, vision comps
```

Components added to the player entity:

| Component key | Notable fields |
|---|---|
| `"position"` | `x`, `y` (pixels) |
| `"metabolism"` | `stamina`, `stamina_max`, `calories`, `rate` |
| `"status"` | `injured: bool`, `injury_severity: float` |
| `"vision"` | `range`, `fov_deg`, `stimuli: list` |

---

## Game State Machine (`main.py`)

```
PLAYING ──(timeout / death / starvation)──► POSTRUN
POSTRUN ──(SPACE key)──► RESTART ──► PLAYING
```

- **PLAYING**: fixed-timestep sim + render HUD.
- **POSTRUN**: shows results screen; on first render calculates fitness and
  calls `evolution.evolve()`. Subsequent renders reuse cached values (be
  careful — `evolve()` must only be called once per run).
- **RESTART**: calls `restart_run()` which tears down and rebuilds the ECS
  World, resets systems, spawns fresh entities.

---

## Testing Conventions

Tests live in `vestigaea/tests/` and use **pytest**.

**Shared fixtures** (`conftest.py`):

| Fixture | Description |
|---|---|
| `seed_rng` | Sets `random.seed(42)` before test, resets after |
| `test_world` | Fresh `World()` instance per test |
| `base_genome` | Standard genome dict with known values |

Guidelines:
- Always use `seed_rng` when testing any mutation or randomised behaviour.
- Call `bus.clear()` in tests that publish events, or use a local `EventBus()`
  instance to avoid polluting the global `bus`.
- Tests must not write to `vestigaea/data/` — use `tmp_path` (pytest built-in)
  for file-writing tests (see `test_evolution.py`).

---

## Code Style

- **Python 3.10+** syntax (`X | Y` union types, `match`, etc.).
- `from __future__ import annotations` at the top of files that use forward
  references in type hints.
- Type hints on all public functions; `Dict`, `List`, `Optional` from `typing`
  for Python <3.10 compatibility where still needed.
- Docstrings on all modules, classes, and public methods.
- Line length: **88 characters** (black default).
- No enforced CI formatter yet; run `black` and `ruff` locally before
  committing.

---

## Adding New Systems

1. Create a class in `game/` that extends `System` from `core/ecs.py`.
2. Implement `update(self, dt: float) -> None`.
3. Register the system in `Game.__init__()` **and** in `Game.restart_run()` in
   the correct order relative to existing systems.
4. Subscribe to any `bus` events in `__init__`; unsubscribe in a `teardown()`
   method if the system can be replaced mid-session.
5. Add unit tests under `vestigaea/tests/`.

## Adding New Components

Components are plain dicts. Define their schema via a factory function or
inline in `entities.py`. Document the keys and their types in a docstring.
Access via `world.get_component(entity_id, "comp_key")` — always check for
`None` before reading fields.

---

## Known Limitations / Design Decisions

- **No CI pipeline**: tests must be run manually with `pytest`.
- **No package manifest**: `pip install pygame` is the only setup step.
- **Global `bus` singleton**: convenient but requires `bus.clear()` discipline
  in tests.
- **Evolution side-effects in render**: `evolution.evolve()` is called inside
  `Game.render()` during `POSTRUN` state — this is intentional to keep the
  post-run screen rendering immediate, but means render is not purely
  presentational.
- **Hardcoded constants**: all tuning values (FPS, world size, max run time,
  genome clamp ranges) live in `main.py` or inline in `evolution.py` — there
  is no external config file for them.
