"""
Lightweight Entity Component System for Vestigaea MVP.
Entities are just IDs, components are dicts, systems are classes with update(dt).
"""
from typing import Dict, Any, Set, Optional
from dataclasses import dataclass, field

@dataclass
class Entity:
    """Entity is just an ID container."""
    id: int
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class World:
    """Central ECS container tracking all entities and components."""
    def __init__(self):
        self._next_id = 1
        self._entities: Dict[int, Entity] = {}
        self._components: Dict[str, Dict[int, Dict[str, Any]]] = {}
        self._systems: Set['System'] = set()
    
    def create_entity(self) -> Entity:
        """Create a new entity with a unique ID."""
        ent = Entity(self._next_id)
        self._entities[ent.id] = ent
        self._next_id += 1
        return ent
    
    def add_component(self, entity_id: int, comp_type: str, data: Dict[str, Any]) -> None:
        """Add a component to an entity."""
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity_id] = data
        self._entities[entity_id].components[comp_type] = data

    def get_component(self, entity_id: int, comp_type: str) -> Optional[Dict[str, Any]]:
        """Get a component from an entity if it exists."""
        return self._components.get(comp_type, {}).get(entity_id)

    def remove_component(self, entity_id: int, comp_type: str) -> None:
        """Remove a component from an entity."""
        if comp_type in self._components and entity_id in self._components[comp_type]:
            del self._components[comp_type][entity_id]
            del self._entities[entity_id].components[comp_type]

    def destroy_entity(self, entity_id: int) -> None:
        """Remove an entity and all its components."""
        if entity_id in self._entities:
            for comp_type in list(self._components.keys()):
                if entity_id in self._components[comp_type]:
                    del self._components[comp_type][entity_id]
            del self._entities[entity_id]

    def register_system(self, system: 'System') -> None:
        """Add a system to be updated each frame."""
        self._systems.add(system)
        system.world = self

    def update(self, dt: float) -> None:
        """Update all registered systems."""
        for system in self._systems:
            system.update(dt)

    def get_entities_with(self, *comp_types: str) -> Set[int]:
        """Get all entity IDs that have all the specified component types."""
        if not comp_types:
            return set()
        entities = set(self._components.get(comp_types[0], {}).keys())
        for comp_type in comp_types[1:]:
            entities &= set(self._components.get(comp_type, {}).keys())
        return entities

class System:
    """Base class for all systems that operate on entities."""
    def __init__(self):
        self.world: Optional[World] = None
    
    def update(self, dt: float) -> None:
        """Override this to implement system behavior."""
        pass