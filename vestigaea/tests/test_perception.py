"""
Tests for perception and vision cone functionality.
"""
import pytest
import math
from vestigaea.core.ecs import World
from vestigaea.game.perception import VisionSystem, Stimulus

def test_vision_cone_detection():
    """Test basic vision cone stimulus detection."""
    world = World()
    vision_sys = VisionSystem()
    world.register_system(vision_sys)
    
    # Create observer
    observer = world.create_entity()
    world.add_component(observer.id, "transform", {
        "x": 100,
        "y": 100,
        "direction": 0.0  # Looking right
    })
    world.add_component(observer.id, "vision", {
        "range": 100,
        "fov_deg": 90,
        "stimuli": []
    })
    
    # Create target in front (should be visible)
    target1 = world.create_entity()
    world.add_component(target1.id, "transform", {
        "x": 150,  # 50 units ahead
        "y": 100,
        "direction": 0.0
    })
    world.add_component(target1.id, "predator", {})  # Mark as predator
    
    # Create target behind (should not be visible)
    target2 = world.create_entity()
    world.add_component(target2.id, "transform", {
        "x": 50,  # 50 units behind
        "y": 100,
        "direction": 0.0
    })
    world.add_component(target2.id, "predator", {})
    
    # Update vision system
    vision_sys.update(1/30)
    
    # Check observer's stimuli
    vision = world.get_component(observer.id, "vision")
    assert len(vision["stimuli"]) == 1  # Should only see target1
    
    stimulus = vision["stimuli"][0]
    assert stimulus.kind == "predator"
    assert stimulus.dir_rad == pytest.approx(0.0)  # Should be directly ahead
    assert stimulus.intensity == pytest.approx(0.5)  # Half of max range
    assert stimulus.recency_s == 0.0

def test_vision_cone_fov():
    """Test field of view limits."""
    world = World()
    vision_sys = VisionSystem()
    world.register_system(vision_sys)
    
    # Create observer with 90° FOV
    observer = world.create_entity()
    world.add_component(observer.id, "transform", {
        "x": 100,
        "y": 100,
        "direction": 0.0  # Looking right
    })
    world.add_component(observer.id, "vision", {
        "range": 100,
        "fov_deg": 90,
        "stimuli": []
    })
    
    # Create targets at different angles
    targets = []
    angles = [0, 30, 45, 60, 90]  # Degrees
    for angle in angles:
        rad = math.radians(angle)
        target = world.create_entity()
        world.add_component(target.id, "transform", {
            "x": 100 + math.cos(rad) * 50,  # 50 units away at angle
            "y": 100 + math.sin(rad) * 50,
            "direction": 0.0
        })
        world.add_component(target.id, "food", {})
        targets.append(target)
    
    # Update vision
    vision_sys.update(1/30)
    
    # Check which targets are visible
    vision = world.get_component(observer.id, "vision")
    stimuli = vision["stimuli"]
    
    # Should see targets up to 45° (half of 90° FOV)
    assert len(stimuli) == 3
    angles_seen = []
    
    for stim in stimuli:
        angle_deg = math.degrees(stim.dir_rad)
        angles_seen.append(abs(angle_deg))
    
    angles_seen.sort()
    assert angles_seen == pytest.approx([0, 30, 45], abs=1)

def test_vision_memory():
    """Test stimulus memory and decay."""
    world = World()
    vision_sys = VisionSystem()
    world.register_system(vision_sys)
    
    # Create observer with 2s memory span
    observer = world.create_entity()
    world.add_component(observer.id, "transform", {
        "x": 100,
        "y": 100,
        "direction": 0.0
    })
    world.add_component(observer.id, "vision", {
        "range": 100,
        "fov_deg": 90,
        "stimuli": []
    })
    world.add_component(observer.id, "genome", {
        "behavior": {"memory_span": 2.0}
    })
    
    # Create target
    target = world.create_entity()
    world.add_component(target.id, "transform", {
        "x": 150,
        "y": 100,
        "direction": 0.0
    })
    world.add_component(target.id, "food", {})
    
    # Initial sighting
    vision_sys.update(1/30)
    vision = world.get_component(observer.id, "vision")
    assert len(vision["stimuli"]) == 1
    
    # Move target out of view
    transform = world.get_component(target.id, "transform")
    transform["x"] = 0  # Move behind observer
    
    # Update with time passing
    for _ in range(30):  # 1 second at 30Hz
        vision_sys.update(1/30)
    
    # Should still remember
    vision = world.get_component(observer.id, "vision")
    assert len(vision["stimuli"]) == 1
    assert vision["stimuli"][0].recency_s == pytest.approx(1.0)
    
    # Update for another 1.5 seconds
    for _ in range(45):  # 1.5 seconds at 30Hz
        vision_sys.update(1/30)
    
    # Memory should have decayed
    vision = world.get_component(observer.id, "vision")
    assert len(vision["stimuli"]) == 0