"""Example: Basic physics simulation with falling objects.

This example demonstrates:
- Setting up the physics world
- Creating rigid bodies (boxes and spheres)
- Adding a ground plane
- Running the physics simulation

Run: python examples/physics_example.py
"""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, LVector3
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape, BulletSphereShape, BulletPlaneShape
import sys
sys.path.insert(0, '..')


class PhysicsDemo(ShowBase):
    """Physics demonstration app."""
    
    def __init__(self):
        super().__init__()
        
        # Setup physics world
        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))
        
        # Create ground plane
        ground_shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        ground_node = BulletRigidBodyNode('ground')
        ground_node.add_shape(ground_shape)
        ground_np = self.render.attach_new_node(ground_node)
        ground_np.set_pos(0, 0, 0)
        self.world.attach(ground_node)
        
        # Visual ground
        from panda3d.core import CardMaker
        cm = CardMaker('ground_visual')
        cm.set_frame(-50, 50, -50, 50)
        ground_visual = self.render.attach_new_node(cm.generate())
        ground_visual.set_p(-90)
        ground_visual.set_color(0.3, 0.5, 0.3)
        
        # Create falling boxes
        for i in range(3):
            box_shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
            box_node = BulletRigidBodyNode(f'box_{i}')
            box_node.add_shape(box_shape)
            box_node.set_mass(1.0)
            box_np = self.render.attach_new_node(box_node)
            box_np.set_pos(i * 2 - 2, 0, 5 + i * 2)
            self.world.attach(box_node)
            
            # Visual box
            box_visual = self.loader.load_model('models/box')
            box_visual.reparent_to(box_np)
            box_visual.set_scale(0.5)
            box_visual.set_color(1, 0.5, 0)
        
        # Create falling spheres
        for i in range(3):
            sphere_shape = BulletSphereShape(0.5)
            sphere_node = BulletRigidBodyNode(f'sphere_{i}')
            sphere_node.add_shape(sphere_shape)
            sphere_node.set_mass(0.5)
            sphere_np = self.render.attach_new_node(sphere_node)
            sphere_np.set_pos(i * 2 - 2, 3, 8 + i * 2)
            self.world.attach(sphere_node)
            
            # Visual sphere
            from panda3d.core import GeomNode
            from panda3d.core import Geom, GeomVertexFormat, GeomVertexData
            # Use simple sphere model
            try:
                sphere_visual = self.loader.load_model('models/sphere')
                sphere_visual.reparent_to(sphere_np)
                sphere_visual.set_scale(0.5)
                sphere_visual.set_color(0, 0.5, 1)
            except:
                pass  # Model not available
        
        # Camera setup
        self.cam.set_pos(0, -20, 10)
        self.cam.look_at(0, 0, 0)
        
        # Lighting
        from panda3d.core import AmbientLight, DirectionalLight
        alight = AmbientLight('alight')
        alight.set_color((0.4, 0.4, 0.4, 1))
        alnp = self.render.attach_new_node(alight)
        self.render.set_light(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.set_color((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attach_new_node(dlight)
        dlnp.set_hpr(45, -60, 0)
        self.render.set_light(dlnp)
        
        # Update task
        self.taskMgr.add(self.update, 'update')
        
        print("Physics demo running!")
        print("Objects will fall and collide with the ground.")
        print("Press ESC to quit")
        
        self.accept('escape', sys.exit)
    
    def update(self, task):
        """Update physics simulation."""
        dt = globalClock.get_dt()
        self.world.do_physics(dt, 10, 1.0/180.0)
        return task.cont


if __name__ == '__main__':
    app = PhysicsDemo()
    app.run()
