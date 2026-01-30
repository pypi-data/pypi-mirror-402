"""
Component system for entity-component architecture.
"""
from typing import Dict, Any, Optional, Type, List
from abc import ABC, abstractmethod
from .events import EventDispatcher, EventType, get_event_dispatcher


class Component(ABC):
    """Base component class."""
    
    def __init__(self):
        """Initialize component."""
        self.entity_id: Optional[int] = None
        self.enabled = True
    
    @abstractmethod
    def get_type(self) -> str:
        """Get component type name."""
        pass
    
    def on_attach(self, entity_id: int):
        """Called when component is attached to entity."""
        self.entity_id = entity_id
    
    def on_detach(self):
        """Called when component is detached from entity."""
        self.entity_id = None
    
    def update(self, delta_time: float):
        """Update component (called each frame)."""
        pass
    
    def __repr__(self):
        return f"{self.get_type()}(entity_id={self.entity_id}, enabled={self.enabled})"


class TransformComponent(Component):
    """Transform component (position, rotation, scale)."""
    
    def __init__(self):
        """Initialize transform component."""
        super().__init__()
        from IntPy.vectors import vector3D
        from Render_Pipeline.transform import Transform
        
        self.transform = Transform()
    
    def get_type(self) -> str:
        return "Transform"
    
    def get_position(self):
        """Get position."""
        return self.transform.position
    
    def set_position(self, position):
        """Set position."""
        self.transform.set_position(position)
    
    def get_rotation(self):
        """Get rotation."""
        return self.transform.rotation
    
    def set_rotation(self, rotation):
        """Set rotation."""
        self.transform.set_rotation(rotation)
    
    def get_scale(self):
        """Get scale."""
        return self.transform.scale
    
    def set_scale(self, scale):
        """Set scale."""
        self.transform.set_scale(scale)


class Entity:
    """Entity in the entity-component system."""
    
    def __init__(self, entity_id: int):
        """
        Initialize entity.
        
        Args:
            entity_id: Unique entity ID
        """
        self.id = entity_id
        self.components: Dict[str, Component] = {}
        self.enabled = True
        self.name = f"Entity_{entity_id}"
    
    def add_component(self, component: Component) -> Component:
        """Add component to entity."""
        component_type = component.get_type()
        if component_type in self.components:
            raise ValueError(f"Entity already has component of type: {component_type}")
        
        self.components[component_type] = component
        component.on_attach(self.id)
        
        # Dispatch event
        event_dispatcher = get_event_dispatcher()
        event_dispatcher.dispatch_immediate(
            EventType.COMPONENT_ADDED,
            {"entity_id": self.id, "component": component}
        )
        
        return component
    
    def get_component(self, component_type: str) -> Optional[Component]:
        """Get component by type."""
        return self.components.get(component_type)
    
    def has_component(self, component_type: str) -> bool:
        """Check if entity has component."""
        return component_type in self.components
    
    def remove_component(self, component_type: str):
        """Remove component from entity."""
        if component_type in self.components:
            component = self.components[component_type]
            component.on_detach()
            del self.components[component_type]
            
            # Dispatch event
            event_dispatcher = get_event_dispatcher()
            event_dispatcher.dispatch_immediate(
                EventType.COMPONENT_REMOVED,
                {"entity_id": self.id, "component_type": component_type}
            )
    
    def update(self, delta_time: float):
        """Update all components."""
        if not self.enabled:
            return
        
        for component in self.components.values():
            if component.enabled:
                component.update(delta_time)
    
    def __repr__(self):
        return f"Entity(id={self.id}, name='{self.name}', components={list(self.components.keys())})"


class EntityManager:
    """Manages entities and components."""
    
    def __init__(self):
        """Initialize entity manager."""
        self.entities: Dict[int, Entity] = {}
        self.next_entity_id = 1
        self.event_dispatcher = get_event_dispatcher()
    
    def create_entity(self, name: str = None) -> Entity:
        """Create a new entity."""
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        
        entity = Entity(entity_id)
        if name:
            entity.name = name
        
        self.entities[entity_id] = entity
        
        # Dispatch event
        self.event_dispatcher.dispatch_immediate(
            EventType.ENTITY_CREATED,
            {"entity_id": entity_id, "entity": entity}
        )
        
        return entity
    
    def destroy_entity(self, entity_id: int):
        """Destroy an entity."""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            
            # Remove all components
            for component_type in list(entity.components.keys()):
                entity.remove_component(component_type)
            
            del self.entities[entity_id]
            
            # Dispatch event
            self.event_dispatcher.dispatch_immediate(
                EventType.ENTITY_DESTROYED,
                {"entity_id": entity_id}
            )
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_entities_with_component(self, component_type: str) -> List[Entity]:
        """Get all entities with a specific component."""
        return [entity for entity in self.entities.values() 
                if entity.has_component(component_type)]
    
    def update(self, delta_time: float):
        """Update all entities."""
        for entity in self.entities.values():
            entity.update(delta_time)
    
    def clear(self):
        """Clear all entities."""
        for entity_id in list(self.entities.keys()):
            self.destroy_entity(entity_id)
    
    def get_entity_count(self) -> int:
        """Get number of entities."""
        return len(self.entities)


# Global entity manager instance
_entity_manager: Optional[EntityManager] = None


def get_entity_manager() -> EntityManager:
    """Get global entity manager instance."""
    global _entity_manager
    if _entity_manager is None:
        _entity_manager = EntityManager()
    return _entity_manager

