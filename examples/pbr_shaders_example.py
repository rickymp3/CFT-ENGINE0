"""Example: PBR shader demonstration with multiple materials.

This example demonstrates:
- Loading 3D models
- Applying PBR (Physically Based Rendering) shaders
- Different material properties (metallic, roughness)
- Dynamic lighting with multiple light sources

Run: python examples/pbr_shaders_example.py
"""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, Vec4
import sys
sys.path.insert(0, '..')

try:
    from engine_modules.rendering import RenderingManager
    from engine_modules.config import get_config
except ImportError:
    print("Warning: Engine modules not found, using basic rendering")
    RenderingManager = None


class PBRDemo(ShowBase):
    """PBR shader demonstration app."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize config
        config = get_config() if 'get_config' in dir() else None
        
        # Initialize rendering manager
        if RenderingManager:
            self.renderer = RenderingManager(self.render)
            self.renderer.enable_pbr()
        else:
            self.renderer = None
        
        # Camera setup
        self.cam.set_pos(0, -15, 8)
        self.cam.look_at(0, 0, 2)
        
        # Create demonstration objects with different materials
        self.create_material_spheres()
        
        # Setup lighting
        self.setup_lighting()
        
        # Add rotation task
        self.taskMgr.add(self.rotate_objects, 'rotate')
        
        print("PBR Shader Demo running!")
        print("Observe different material properties:")
        print("  - Metallic surfaces (left)")
        print("  - Rough surfaces (right)")
        print("  - Different colors and reflections")
        print("\nPress ESC to quit")
        
        self.accept('escape', sys.exit)
        
        # Store object reference
        self.objects = []
    
    def create_material_spheres(self):
        """Create spheres with different PBR materials."""
        try:
            # Load base model (sphere or box)
            base_model = None
            for model_path in ['models/sphere', 'models/box', 'models/misc/sphere']:
                try:
                    base_model = self.loader.load_model(model_path)
                    break
                except:
                    continue
            
            if not base_model:
                print("Warning: No models available, creating simple geometry")
                return
            
            # Create material showcase grid
            materials = [
                # (x, y, z, color, metallic, roughness, name)
                (-4, 0, 2, Vec4(1.0, 0.2, 0.2, 1), 0.0, 0.1, "Smooth Plastic"),
                (-2, 0, 2, Vec4(0.2, 1.0, 0.2, 1), 0.5, 0.3, "Semi-Metal"),
                (0, 0, 2, Vec4(0.2, 0.2, 1.0, 1), 1.0, 0.1, "Polished Metal"),
                (2, 0, 2, Vec4(1.0, 1.0, 0.2, 1), 0.0, 0.8, "Rough Plastic"),
                (4, 0, 2, Vec4(0.8, 0.8, 0.8, 1), 1.0, 0.5, "Brushed Metal"),
            ]
            
            for x, y, z, color, metallic, roughness, name in materials:
                obj = base_model.copy_to(self.render)
                obj.set_pos(x, y, z)
                obj.set_scale(0.8)
                obj.set_color(color)
                
                # Set material properties (if PBR is enabled)
                if self.renderer:
                    # Material properties would be set via shader inputs
                    obj.set_shader_input('metallic', metallic)
                    obj.set_shader_input('roughness', roughness)
                
                self.objects.append({'node': obj, 'name': name})
                print(f"Created: {name}")
        
        except Exception as e:
            print(f"Error creating materials: {e}")
    
    def setup_lighting(self):
        """Setup multiple light sources."""
        if self.renderer:
            # Use rendering manager for advanced lighting
            self.renderer.add_ambient_light('ambient', Vec4(0.2, 0.2, 0.3, 1))
            self.renderer.add_directional_light('sun', Vec4(1.0, 0.95, 0.8, 1), Vec3(-1, -1, -1))
            self.renderer.add_point_light('key', Vec4(1.0, 0.8, 0.6, 1), Vec3(-5, -5, 8))
            self.renderer.add_point_light('fill', Vec4(0.4, 0.6, 1.0, 1), Vec3(5, -5, 5))
        else:
            # Basic lighting fallback
            from panda3d.core import AmbientLight, DirectionalLight, PointLight
            
            # Ambient light
            alight = AmbientLight('alight')
            alight.set_color((0.2, 0.2, 0.3, 1))
            alnp = self.render.attach_new_node(alight)
            self.render.set_light(alnp)
            
            # Directional light (sun)
            dlight = DirectionalLight('dlight')
            dlight.set_color((1.0, 0.95, 0.8, 1))
            dlnp = self.render.attach_new_node(dlight)
            dlnp.set_hpr(45, -45, 0)
            self.render.set_light(dlnp)
            
            # Point light 1 (key light)
            plight1 = PointLight('plight1')
            plight1.set_color((1.0, 0.8, 0.6, 1))
            plnp1 = self.render.attach_new_node(plight1)
            plnp1.set_pos(-5, -5, 8)
            self.render.set_light(plnp1)
            
            # Point light 2 (fill light)
            plight2 = PointLight('plight2')
            plight2.set_color((0.4, 0.6, 1.0, 1))
            plnp2 = self.render.attach_new_node(plight2)
            plnp2.set_pos(5, -5, 5)
            self.render.set_light(plnp2)
    
    def rotate_objects(self, task):
        """Rotate objects to show material properties."""
        for obj_data in self.objects:
            obj_data['node'].set_h(obj_data['node'].get_h() + 20 * globalClock.get_dt())
        return task.cont


if __name__ == '__main__':
    app = PBRDemo()
    app.run()
