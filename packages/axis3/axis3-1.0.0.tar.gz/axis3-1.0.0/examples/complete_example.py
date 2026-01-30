"""
Complete Example

A comprehensive example showing how to use all major features of Core together.
"""
from Engine import (
    Engine, get_time, get_input, get_event_dispatcher,
    Key, MouseButton, EventType, info, warning
)
from Render_Pipeline import (
    Camera, Scene, GameObject,
    PrimitiveFactory, MaterialLibrary,
    RenderPipeline, DirectionalLight, PointLight, AmbientLight
)
from IntPy import vector3D, degrees_to_radians
import math


class Game:
    """Main game class."""
    
    def __init__(self):
        """Initialize game."""
        self.engine = None
        self.scene = None
        self.renderer = None
        self.camera = None
        
        # Game state
        self.camera_rotation = vector3D(0, 0, 0)
        self.camera_distance = 5.0
        
    def initialize(self):
        """Initialize game systems."""
        # Create engine
        self.engine = Engine(
            width=1280,
            height=720,
            title="Core - Complete Example",
            fullscreen=False
        )
        
        # Create scene
        self.scene = self.create_scene()
        
        # Create renderer
        self.renderer = RenderPipeline(1280, 720)
        self.renderer.enable_culling(True)
        
        # Setup event handlers
        self.setup_events()
        
        # Set callbacks
        self.engine.set_update_callback(self.update)
        self.engine.set_render_callback(self.render)
        
    def create_scene(self):
        """Create the game scene."""
        scene = Scene("GameScene")
        scene.set_background_color(0.05, 0.05, 0.1, 1.0)
        
        # Create camera
        self.camera = Camera(
            position=vector3D(0, 2, self.camera_distance),
            target=vector3D(0, 0, 0),
            up=vector3D(0, 1, 0),
            fov=60.0,
            aspect_ratio=16.0 / 9.0
        )
        scene.set_main_camera(self.camera)
        
        # Create objects
        # Cube
        cube_mesh = PrimitiveFactory.create_cube(1.0)
        cube_material = MaterialLibrary.metallic_rough(metallic=0.9, roughness=0.1)
        cube_material.set_albedo(0.8, 0.2, 0.2)
        
        cube = GameObject("Cube", mesh=cube_mesh, material=cube_material)
        cube.transform.set_position(vector3D(-2, 0.5, 0))
        scene.add_object(cube)
        
        # Sphere
        sphere_mesh = PrimitiveFactory.create_sphere(radius=0.8, segments=32)
        sphere_material = MaterialLibrary.plastic((0.2, 0.8, 0.2))
        
        sphere = GameObject("Sphere", mesh=sphere_mesh, material=sphere_material)
        sphere.transform.set_position(vector3D(0, 0.8, 0))
        scene.add_object(sphere)
        
        # Ground plane
        plane_mesh = PrimitiveFactory.create_plane(width=10, height=10)
        plane_material = MaterialLibrary.default()
        plane_material.set_albedo(0.3, 0.3, 0.3)
        
        plane = GameObject("Ground", mesh=plane_mesh, material=plane_material)
        plane.transform.set_position(vector3D(0, -0.5, 0))
        scene.add_object(plane)
        
        # Add lights
        # Sun (directional)
        sun = DirectionalLight(
            direction=vector3D(-0.5, -1, -0.5),
            color=(1.0, 0.95, 0.8),
            intensity=1.2
        )
        scene.light_manager.add_directional(sun)
        
        # Point light
        point_light = PointLight(
            position=vector3D(2, 2, 2),
            color=(1.0, 0.8, 0.6),
            intensity=1.5,
            range=8.0
        )
        scene.light_manager.add_point(point_light)
        
        # Ambient
        ambient = AmbientLight(color=(1.0, 1.0, 1.0), intensity=0.15)
        scene.light_manager.set_ambient(ambient)
        
        return scene
    
    def setup_events(self):
        """Setup event handlers."""
        dispatcher = get_event_dispatcher()
        
        def on_resize(event):
            data = event.data
            if data:
                width = data.get('width', 1280)
                height = data.get('height', 720)
                self.renderer.set_render_target_size(width, height)
                if self.camera:
                    self.camera.set_aspect_ratio(width / height)
                info(f"Window resized to {width}x{height}")
        
        dispatcher.subscribe(EventType.WINDOW_RESIZE, on_resize)
    
    def update(self, delta_time):
        """Update game logic."""
        input_manager = get_input()
        time = get_time()
        
        # Camera rotation with mouse
        mouse_delta = input_manager.get_mouse_delta()
        if input_manager.is_mouse_button_pressed(MouseButton.LEFT):
            self.camera_rotation.y += mouse_delta[0] * 0.5
            self.camera_rotation.x += mouse_delta[1] * 0.5
            self.camera_rotation.x = max(-89, min(89, self.camera_rotation.x))
        
        # Camera zoom with scroll
        scroll = input_manager.get_mouse_scroll()
        if scroll[1] != 0:
            self.camera_distance += scroll[1] * 0.5
            self.camera_distance = max(2.0, min(10.0, self.camera_distance))
        
        # Update camera position (orbit around origin)
        if self.camera:
            yaw = degrees_to_radians(self.camera_rotation.y)
            pitch = degrees_to_radians(self.camera_rotation.x)
            
            x = self.camera_distance * math.cos(pitch) * math.sin(yaw)
            y = self.camera_distance * math.sin(pitch)
            z = self.camera_distance * math.cos(pitch) * math.cos(yaw)
            
            self.camera.set_position(vector3D(x, y, z))
            self.camera.look_at(vector3D(0, 0, 0))
        
        # Rotate objects
        for obj in self.scene.get_active_objects():
            if obj.name == "Cube":
                rot = obj.transform.get_rotation()
                obj.transform.set_rotation(vector3D(
                    rot.x,
                    rot.y + delta_time * 45.0,
                    rot.z
                ))
            elif obj.name == "Sphere":
                # Bounce animation
                pos = obj.transform.get_position()
                bounce = math.sin(time.get_time() * 2.0) * 0.3
                obj.transform.set_position(vector3D(pos.x, 0.8 + bounce, pos.z))
        
        # Exit
        if input_manager.is_key_pressed(Key.ESCAPE):
            self.engine.stop()
        
        # Print FPS occasionally
        if int(time.get_time()) % 5 == 0 and time.get_time() > 0:
            stats = self.renderer.get_stats()
            info(f"FPS: {time.get_fps():.1f} | "
                 f"Objects: {stats.objects_rendered} | "
                 f"Triangles: {stats.triangles_rendered}")
    
    def render(self):
        """Render the scene."""
        if self.scene and self.renderer:
            self.renderer.render_scene(self.scene)
    
    def run(self):
        """Run the game."""
        if not self.engine:
            self.initialize()
        
        print("=" * 50)
        print("Core - Complete Example")
        print("=" * 50)
        print("Controls:")
        print("  Mouse + Left Click - Rotate camera")
        print("  Mouse Scroll - Zoom in/out")
        print("  ESC - Exit")
        print("=" * 50)
        print()
        
        self.engine.run()


if __name__ == "__main__":
    game = Game()
    game.run()

