"""
Tests for core ECS and fixed timestep functionality.
"""
import pytest
from vestigaea.core.ecs import World, System, Entity
from vestigaea.core.timer import FixedTimestep

def test_entity_creation():
    """Test basic entity creation and component management."""
    world = World()
    
    # Create entity
    entity = world.create_entity()
    assert entity.id == 1  # First entity should have ID 1
    
    # Add component
    world.add_component(entity.id, "transform", {
        "x": 100,
        "y": 200,
        "direction": 0.0
    })
    
    # Verify component exists
    comp = world.get_component(entity.id, "transform")
    assert comp is not None
    assert comp["x"] == 100
    assert comp["y"] == 200
    
    # Remove component
    world.remove_component(entity.id, "transform")
    assert world.get_component(entity.id, "transform") is None
    
    # Destroy entity
    world.destroy_entity(entity.id)
    assert world.get_component(entity.id, "transform") is None

def test_system_updates():
    """Test system registration and updates."""
    class TestSystem(System):
        def __init__(self):
            super().__init__()
            self.update_count = 0
        
        def update(self, dt):
            self.update_count += 1
            # Update all entities with test component
            entities = self.world.get_entities_with("test")
            for entity_id in entities:
                comp = self.world.get_component(entity_id, "test")
                comp["value"] += dt
    
    world = World()
    system = TestSystem()
    world.register_system(system)
    
    # Create test entity
    entity = world.create_entity()
    world.add_component(entity.id, "test", {"value": 0.0})
    
    # Run updates
    world.update(0.1)
    world.update(0.1)
    
    assert system.update_count == 2
    assert world.get_component(entity.id, "test")["value"] == pytest.approx(0.2)

def test_fixed_timestep():
    """Test fixed timestep accumulator pattern."""
    timer = FixedTimestep(dt=1/30)  # 30Hz fixed update
    updates = 0
    
    def update_fn(dt):
        nonlocal updates
        updates += 1
        assert dt == pytest.approx(1/30)
    
    # Simulate 0.1s frame (should cause 3 updates at 30Hz)
    steps = timer.update(0.1, update_fn)
    assert steps == 3
    assert updates == 3
    assert timer.accumulator < 1/30
    
    # Another 0.1s frame
    steps = timer.update(0.1, update_fn)
    assert steps == 3
    assert updates == 6
    
    # Small frame that doesn't trigger update
    steps = timer.update(0.01, update_fn)
    assert steps == 0
    assert updates == 6
    assert timer.accumulator == pytest.approx(0.01, abs=1e-6)

def test_entity_queries():
    """Test querying entities with specific components."""
    world = World()
    
    # Create entities with different component combinations
    e1 = world.create_entity()
    world.add_component(e1.id, "position", {"x": 0, "y": 0})
    world.add_component(e1.id, "velocity", {"dx": 1, "dy": 0})
    
    e2 = world.create_entity()
    world.add_component(e2.id, "position", {"x": 5, "y": 5})
    
    e3 = world.create_entity()
    world.add_component(e3.id, "position", {"x": 10, "y": 10})
    world.add_component(e3.id, "velocity", {"dx": 0, "dy": 1})
    
    # Query tests
    moving = world.get_entities_with("position", "velocity")
    assert len(moving) == 2
    assert e1.id in moving
    assert e3.id in moving
    assert e2.id not in moving
    
    stationary = world.get_entities_with("position")
    assert len(stationary) == 3
    assert e2.id in stationary

def test_system_dependencies():
    """Test systems interacting with shared entities."""
    class PhysicsSystem(System):
        def update(self, dt):
            entities = self.world.get_entities_with("position", "velocity")
            for eid in entities:
                pos = self.world.get_component(eid, "position")
                vel = self.world.get_component(eid, "velocity")
                pos["x"] += vel["dx"] * dt
                pos["y"] += vel["dy"] * dt
    
    class BoundsSystem(System):
        def update(self, dt):
            entities = self.world.get_entities_with("position")
            for eid in entities:
                pos = self.world.get_component(eid, "position")
                # Clamp to 0-100 range
                pos["x"] = max(0, min(100, pos["x"]))
                pos["y"] = max(0, min(100, pos["y"]))
    
    world = World()
    physics = PhysicsSystem()
    bounds = BoundsSystem()
    world.register_system(physics)
    world.register_system(bounds)
    
    # Create test entity
    entity = world.create_entity()
    world.add_component(entity.id, "position", {"x": 0, "y": 0})
    world.add_component(entity.id, "velocity", {"dx": 50, "dy": 0})
    
    # Update should move entity and clamp position
    world.update(3.0)
    pos = world.get_component(entity.id, "position")
    assert pos["x"] == 100  # Clamped at boundary
    assert pos["y"] == 0