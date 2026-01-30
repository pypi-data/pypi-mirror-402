"""
Basic Engine Example

Demonstrates how to set up and run a basic engine instance.
"""
from Engine import Engine, get_time, get_input, Key, info


def update(delta_time):
    """Update function called each frame."""
    time = get_time()
    input_manager = get_input()
    
    # Print FPS every second
    if int(time.get_time()) % 1 == 0:
        info(f"FPS: {time.get_fps():.1f}, Delta Time: {delta_time:.4f}")
    
    # Exit on ESC key
    if input_manager.is_key_pressed(Key.ESCAPE):
        engine.stop()


def render():
    """Render function called each frame."""
    # Your rendering code here
    # For now, just clear the screen (would be done by graphics backend)
    pass


if __name__ == "__main__":
    # Create engine
    engine = Engine(
        width=1280,
        height=720,
        title="Core - Basic Example",
        fullscreen=False
    )
    
    # Set callbacks
    engine.set_update_callback(update)
    engine.set_render_callback(render)
    
    # Run engine
    print("Starting engine... Press ESC to exit")
    engine.run()
    print("Engine stopped")

