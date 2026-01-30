"""
Input Handling Example

Demonstrates how to handle keyboard and mouse input.
"""
from Engine import Engine, get_input, Key, MouseButton, info


def update(delta_time):
    """Update function with input handling."""
    input_manager = get_input()
    
    # Keyboard input
    if input_manager.is_key_pressed(Key.W):
        info("W key is being held")
    
    if input_manager.is_key_down(Key.SPACE):
        info("Space key was just pressed!")
    
    if input_manager.is_key_up(Key.SPACE):
        info("Space key was just released!")
    
    # Arrow keys
    if input_manager.is_key_pressed(Key.UP):
        info("Moving up")
    if input_manager.is_key_pressed(Key.DOWN):
        info("Moving down")
    if input_manager.is_key_pressed(Key.LEFT):
        info("Moving left")
    if input_manager.is_key_pressed(Key.RIGHT):
        info("Moving right")
    
    # Mouse input
    mouse_pos = input_manager.get_mouse_position()
    mouse_delta = input_manager.get_mouse_delta()
    
    if mouse_delta[0] != 0 or mouse_delta[1] != 0:
        info(f"Mouse moved: delta=({mouse_delta[0]:.2f}, {mouse_delta[1]:.2f})")
    
    if input_manager.is_mouse_button_pressed(MouseButton.LEFT):
        info(f"Left mouse button held at: ({mouse_pos[0]:.1f}, {mouse_pos[1]:.1f})")
    
    if input_manager.is_mouse_button_down(MouseButton.RIGHT):
        info("Right mouse button clicked!")
    
    # Mouse scroll
    scroll = input_manager.get_mouse_scroll()
    if scroll[1] != 0:
        info(f"Mouse scrolled: {scroll[1]:.2f}")
    
    # Exit
    if input_manager.is_key_pressed(Key.ESCAPE):
        engine.stop()


def render():
    """Render function."""
    pass


if __name__ == "__main__":
    engine = Engine(width=1280, height=720, title="Input Example")
    engine.set_update_callback(update)
    engine.set_render_callback(render)
    
    print("Input Example")
    print("Controls:")
    print("  W, A, S, D / Arrow Keys - Movement")
    print("  Space - Jump")
    print("  Mouse - Move and click")
    print("  Scroll - Zoom")
    print("  ESC - Exit")
    print("\nStarting engine...")
    
    engine.run()

