"""Example: Basic scene setup with camera and lighting.

This example demonstrates:
- Creating a simple 3D scene
- Camera positioning and controls
- Basic lighting setup
- Loading and positioning 3D models

Run: python examples/basic_scene_example.py
"""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, Vec4
import sys
sys.path.insert(0, '..')


class BasicSceneDemo(ShowBase):
    """Basic scene demonstration."""
    
    def __init__(self):
        super().__init__()
        
        # Setup scene
        self.setup_camera()
        self.setup_lighting()
        self.create_environment()
        self.create_models()
        
        # Add tasks
        self.taskMgr.add(self.update, 'update')
        
        print("\n=== Basic Scene Demo ===")
        print("Controls:")
        print("  Arrow Keys: Move camera")
        print("  A/D: Rotate camera left/right")
        print("  W/S: Zoom in/out")
        print("  ESC: Quit")
        print("\nEnjoy the scene!")
        
        self.accept('escape', sys.exit)
        self.setup_controls()
        
        # Camera movement state
        self.camera_speed = 10
        self.rotation_speed = 50
        self.keys = {
            'up': False, 'down': False,
            'left': False, 'right': False,
            'w': False, 's': False,
            'a': False, 'd': False
        }
    
    def setup_camera(self):
        """Position the camera."""
        self.cam.set_pos(0, -20, 10)
        self.cam.look_at(0, 0, 0)
        self.camera_target = Vec3(0, 0, 0)
    
    def setup_lighting(self):
        """Create lighting for the scene."""
        from panda3d.core import AmbientLight, DirectionalLight
        
        # Ambient light for overall illumination
        ambient = AmbientLight('ambient')
        ambient.set_color(Vec4(0.3, 0.3, 0.4, 1))
        ambient_np = self.render.attach_new_node(ambient)
        self.render.set_light(ambient_np)
        
        # Directional light (sun)
        sun = DirectionalLight('sun')
        sun.set_color(Vec4(0.9, 0.9, 0.8, 1))
        sun_np = self.render.attach_new_node(sun)
        sun_np.set_hpr(45, -60, 0)
        self.render.set_light(sun_np)
        
        print("✓ Lighting setup complete")
    
    def create_environment(self):
        """Create ground plane and environment."""
        from panda3d.core import CardMaker
        
        # Ground plane
        cm = CardMaker('ground')
        cm.set_frame(-20, 20, -20, 20)
        ground = self.render.attach_new_node(cm.generate())
        ground.set_p(-90)  # Rotate to horizontal
        ground.set_pos(0, 0, 0)
        ground.set_color(0.2, 0.5, 0.2)  # Green ground
        
        # Grid pattern (optional visual aid)
        for i in range(-10, 11, 2):
            # X-axis lines
            line_cm = CardMaker(f'line_x_{i}')
            line_cm.set_frame(-20, 20, -0.05, 0.05)
            line = self.render.attach_new_node(line_cm.generate())
            line.set_p(-90)
            line.set_pos(0, i, 0.01)
            line.set_color(0.3, 0.6, 0.3)
            
            # Y-axis lines
            line_cm = CardMaker(f'line_y_{i}')
            line_cm.set_frame(-0.05, 0.05, -20, 20)
            line = self.render.attach_new_node(line_cm.generate())
            line.set_p(-90)
            line.set_pos(i, 0, 0.01)
            line.set_color(0.3, 0.6, 0.3)
        
        print("✓ Environment created")
    
    def create_models(self):
        """Load and position 3D models."""
        # Try to load Panda3D's built-in models
        models_to_load = [
            ('models/box', Vec3(-5, 0, 0.5), Vec4(1, 0.3, 0.3, 1), 0.5),
            ('models/box', Vec3(0, 0, 0.5), Vec4(0.3, 1, 0.3, 1), 0.5),
            ('models/box', Vec3(5, 0, 0.5), Vec4(0.3, 0.3, 1, 1), 0.5),
        ]
        
        loaded_count = 0
        for model_path, pos, color, scale in models_to_load:
            try:
                model = self.loader.load_model(model_path)
                model.reparent_to(self.render)
                model.set_pos(pos)
                model.set_color(color)
                model.set_scale(scale)
                loaded_count += 1
            except Exception as e:
                print(f"Could not load {model_path}: {e}")
        
        if loaded_count > 0:
            print(f"✓ Loaded {loaded_count} models")
        else:
            print("! No models loaded (built-in models not available)")
            print("  Scene will show ground and grid only")
    
    def setup_controls(self):
        """Setup keyboard controls."""
        # Arrow keys for camera position
        self.accept('arrow_up', self.set_key, ['up', True])
        self.accept('arrow_up-up', self.set_key, ['up', False])
        self.accept('arrow_down', self.set_key, ['down', True])
        self.accept('arrow_down-up', self.set_key, ['down', False])
        self.accept('arrow_left', self.set_key, ['left', True])
        self.accept('arrow_left-up', self.set_key, ['left', False])
        self.accept('arrow_right', self.set_key, ['right', True])
        self.accept('arrow_right-up', self.set_key, ['right', False])
        
        # WASD for zoom and rotation
        self.accept('w', self.set_key, ['w', True])
        self.accept('w-up', self.set_key, ['w', False])
        self.accept('s', self.set_key, ['s', True])
        self.accept('s-up', self.set_key, ['s', False])
        self.accept('a', self.set_key, ['a', True])
        self.accept('a-up', self.set_key, ['a', False])
        self.accept('d', self.set_key, ['d', True])
        self.accept('d-up', self.set_key, ['d', False])
    
    def set_key(self, key, value):
        """Set key state."""
        self.keys[key] = value
    
    def update(self, task):
        """Update scene each frame."""
        dt = globalClock.get_dt()
        
        # Camera movement
        camera_pos = self.cam.get_pos()
        camera_hpr = self.cam.get_hpr()
        
        # Forward/backward (W/S)
        if self.keys['w']:
            self.cam.set_y(camera_pos.y + self.camera_speed * dt)
        if self.keys['s']:
            self.cam.set_y(camera_pos.y - self.camera_speed * dt)
        
        # Left/right strafe (Arrow keys)
        if self.keys['left']:
            self.cam.set_x(camera_pos.x - self.camera_speed * dt)
        if self.keys['right']:
            self.cam.set_x(camera_pos.x + self.camera_speed * dt)
        
        # Up/down (Arrow keys)
        if self.keys['up']:
            self.cam.set_z(camera_pos.z + self.camera_speed * dt)
        if self.keys['down']:
            self.cam.set_z(camera_pos.z - self.camera_speed * dt)
        
        # Rotation (A/D)
        if self.keys['a']:
            self.cam.set_h(camera_hpr.x + self.rotation_speed * dt)
        if self.keys['d']:
            self.cam.set_h(camera_hpr.x - self.rotation_speed * dt)
        
        return task.cont


if __name__ == '__main__':
    app = BasicSceneDemo()
    app.run()
