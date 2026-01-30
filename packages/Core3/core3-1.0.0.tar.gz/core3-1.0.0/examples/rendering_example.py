"""
Rendering Example

Demonstrates how to set up a scene with objects, lights, and camera.
"""
from Render_Pipeline import (
    Camera, Scene, GameObject,
    PrimitiveFactory, MaterialLibrary,
    RenderPipeline, DirectionalLight, PointLight
)
from IntPy import vector3D


def create_scene():
    """Create a sample scene."""
    # Create scene
    scene = Scene("ExampleScene")
    scene.set_background_color(0.1, 0.1, 0.15, 1.0)
    
    # Create camera
    camera = Camera(
        position=vector3D(0, 2, 5),
        target=vector3D(0, 0, 0),
        up=vector3D(0, 1, 0),
        fov=60.0,
        aspect_ratio=16.0 / 9.0,
        near_plane=0.1,
        far_plane=100.0
    )
    scene.set_main_camera(camera)
    
    # Create a cube
    cube_mesh = PrimitiveFactory.create_cube(1.0)
    cube_material = MaterialLibrary.metallic_rough(metallic=0.8, roughness=0.2)
    cube_material.set_albedo(0.8, 0.2, 0.2)  # Red
    
    cube = GameObject("Cube", mesh=cube_mesh, material=cube_material)
    cube.transform.set_position(vector3D(-2, 0, 0))
    scene.add_object(cube)
    
    # Create a sphere
    sphere_mesh = PrimitiveFactory.create_sphere(radius=0.8, segments=32)
    sphere_material = MaterialLibrary.plastic((0.2, 0.8, 0.2))  # Green
    
    sphere = GameObject("Sphere", mesh=sphere_mesh, material=sphere_material)
    sphere.transform.set_position(vector3D(0, 0, 0))
    scene.add_object(sphere)
    
    # Create a plane (ground)
    plane_mesh = PrimitiveFactory.create_plane(width=10, height=10)
    plane_material = MaterialLibrary.default()
    plane_material.set_albedo(0.5, 0.5, 0.5)
    
    plane = GameObject("Ground", mesh=plane_mesh, material=plane_material)
    plane.transform.set_position(vector3D(0, -1, 0))
    scene.add_object(plane)
    
    # Add lights
    # Directional light (sun)
    sun = DirectionalLight(
        direction=vector3D(-1, -1, -1),
        color=(1.0, 0.95, 0.8),
        intensity=1.0
    )
    scene.light_manager.add_directional(sun)
    
    # Point light
    point_light = PointLight(
        position=vector3D(2, 2, 2),
        color=(1.0, 1.0, 1.0),
        intensity=2.0,
        range=10.0
    )
    scene.light_manager.add_point(point_light)
    
    # Ambient light
    from Render_Pipeline import AmbientLight
    ambient = AmbientLight(color=(1.0, 1.0, 1.0), intensity=0.2)
    scene.light_manager.set_ambient(ambient)
    
    return scene


def main():
    """Main function."""
    print("Creating scene...")
    scene = create_scene()
    
    print(f"Scene created with {scene.get_object_count()} objects")
    print(f"Lights: {scene.light_manager}")
    
    # Create render pipeline
    renderer = RenderPipeline(width=1920, height=1080)
    renderer.enable_culling(True)
    renderer.enable_frustum_culling(True)
    
    # Render scene (in a real application, this would be in the render callback)
    print("\nRendering scene...")
    renderer.render_scene(scene)
    
    # Print render stats
    stats = renderer.get_stats()
    print(f"\nRender Stats:")
    print(f"  Draw Calls: {stats.draw_calls}")
    print(f"  Triangles: {stats.triangles_rendered}")
    print(f"  Objects Rendered: {stats.objects_rendered}")
    print(f"  Objects Culled: {stats.objects_culled}")
    
    print("\nExample complete!")


if __name__ == "__main__":
    main()

