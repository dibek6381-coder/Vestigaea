# Vestigaea

Vestigaea is a lightweight survival evolution prototype. A tiny ECS powers the
simulation while a handful of systems (world generation, perception,
utility-based AI, verbs, telemetry) provide the core gameplay loop.

## Features

* Deterministic entity/component system with safe event bus helpers.
* Utility-based predator AI that reacts to the player's vision stimuli.
* Procedurally generated world grid with respawning forage resources.
* Telemetry-driven evolution loop that mutates genomes between runs.
* Simple pygame HUD and post-run screen to surface key information.

## Development

### Running the Game

```bash
python -m vestigaea.main
```

The game launches in a 1024×1024 window. Use **WASD** to move, **E** to
forage, **Q** to toggle the vision cone overlay and **Esc** to quit.

### Tests

Automated tests live under `vestigaea/tests`. Run them with:

```bash
pytest
```

### Linting & Formatting

The codebase follows standard Python type hints and docstrings. There is no
enforced formatter, but `black`/`ruff` presets with a line length of 88 work
well.

