"""
Component System Example

Demonstrates the entity-component system.
"""
from Engine import (
    get_entity_manager, get_time,
    TransformComponent
)
from Render_Pipeline import GameObject
from IntPy import vector3D
import math


def update(delta_time):
    """Update function."""
    entity_manager = get_entity_manager()
    time = get_time()
    
    # Update all entities (this calls update on all components)
    entity_manager.update(delta_time)
    
    # Example: Rotate an entity
    entities = entity_manager.get_entities_with_component("Transform")
    for entity in entities:
        transform_comp = entity.get_component("Transform")
        if transform_comp:
            # Rotate around Y axis
            current_rot = transform_comp.get_rotation()
            new_rot = vector3D(
                current_rot.x,
                current_rot.y + delta_time * 45.0,  # 45 degrees per second
                current_rot.z
            )
            transform_comp.set_rotation(new_rot)


def create_entities():
    """Create some entities with components."""
    entity_manager = get_entity_manager()
    
    # Create entity 1
    entity1 = entity_manager.create_entity("RotatingCube")
    transform1 = TransformComponent()
    transform1.set_position(vector3D(-2, 0, 0))
    transform1.set_scale(vector3D(1, 1, 1))
    entity1.add_component(transform1)
    
    # Create entity 2
    entity2 = entity_manager.create_entity("BouncingSphere")
    transform2 = TransformComponent()
    transform2.set_position(vector3D(2, 0, 0))
    transform2.set_scale(vector3D(0.5, 0.5, 0.5))
    entity2.add_component(transform2)
    
    # Create entity 3
    entity3 = entity_manager.create_entity("StaticPlane")
    transform3 = TransformComponent()
    transform3.set_position(vector3D(0, -1, 0))
    transform3.set_scale(vector3D(5, 1, 5))
    entity3.add_component(transform3)
    
    print(f"Created {entity_manager.get_entity_count()} entities")
    
    # Print entity info
    for entity_id, entity in entity_manager.entities.items():
        print(f"  {entity.name} (ID: {entity_id})")
        transform = entity.get_component("Transform")
        if transform:
            print(f"    Position: {transform.get_position()}")
            print(f"    Rotation: {transform.get_rotation()}")
            print(f"    Scale: {transform.get_scale()}")


def main():
    """Main function."""
    print("Component System Example\n")
    
    # Create entities
    create_entities()
    
    # Simulate a few frames
    print("\nSimulating 3 frames...")
    time = get_time()
    time.reset()
    
    for i in range(3):
        delta = 0.016  # ~60 FPS
        time.update()
        update(delta)
        print(f"\nFrame {i + 1} (t={time.get_time():.3f}):")
        
        entity_manager = get_entity_manager()
        for entity_id, entity in entity_manager.entities.items():
            transform = entity.get_component("Transform")
            if transform:
                print(f"  {entity.name}: rotation={transform.get_rotation()}")
    
    print("\nExample complete!")


if __name__ == "__main__":
    main()

