"""Vehicle Physics Demo - showcases advanced Bullet physics features.

Demonstrates:
- Raycast vehicle with suspension
- Wheel physics and steering
- Soft body cloth/rope
- Character controller
- Physics constraints
"""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, Point3
from engine_modules.physics import PhysicsManager
import sys

class VehicleDemo(ShowBase):
    """Demo showcasing vehicle and advanced physics."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Setup camera
        self.camera.setPos(0, -20, 10)
        self.camera.lookAt(0, 0, 0)
        
        # Initialize physics
        self.physics = PhysicsManager()
        
        # Create ground
        ground = self.physics.create_ground_plane(name="ground")
        
        # Create a vehicle
        self.setup_vehicle()
        
        # Create soft bodies
        self.setup_soft_bodies()
        
        # Create character controller
        self.setup_character()
        
        # Controls
        self.accept("arrow_up", self.accelerate)
        self.accept("arrow_down", self.brake)
        self.accept("arrow_left", self.steer_left)
        self.accept("arrow_right", self.steer_right)
        self.accept("space", self.jump)
        self.accept("escape", sys.exit)
        
        # Update task
        self.taskMgr.add(self.update, "update")
        
        print("Vehicle Physics Demo")
        print("Controls:")
        print("  Arrow Keys - Drive vehicle")
        print("  Space - Jump character")
        print("  ESC - Exit")
    
    def setup_vehicle(self):
        """Create a vehicle with wheels."""
        # Create chassis (box shape)
        chassis_node = self.physics.create_box(
            name="chassis",
            size=Vec3(2, 4, 1),
            mass=800.0,
            pos=Point3(0, 0, 2)
        )
        
        # Create vehicle
        self.vehicle = self.physics.create_vehicle(chassis_node, "race_car")
        
        # Add wheels
        wheel_radius = 0.4
        suspension_length = 0.5
        
        # Front left
        self.physics.add_wheel(
            self.vehicle,
            connection_point=Vec3(-1, 2, 0.5),
            direction=Vec3(0, 0, -1),
            axle=Vec3(-1, 0, 0),
            suspension_rest_length=suspension_length,
            wheel_radius=wheel_radius,
            is_front_wheel=True
        )
        
        # Front right
        self.physics.add_wheel(
            self.vehicle,
            connection_point=Vec3(1, 2, 0.5),
            direction=Vec3(0, 0, -1),
            axle=Vec3(-1, 0, 0),
            suspension_rest_length=suspension_length,
            wheel_radius=wheel_radius,
            is_front_wheel=True
        )
        
        # Rear left
        self.physics.add_wheel(
            self.vehicle,
            connection_point=Vec3(-1, -2, 0.5),
            direction=Vec3(0, 0, -1),
            axle=Vec3(-1, 0, 0),
            suspension_rest_length=suspension_length,
            wheel_radius=wheel_radius,
            is_front_wheel=False
        )
        
        # Rear right
        self.physics.add_wheel(
            self.vehicle,
            connection_point=Vec3(1, -2, 0.5),
            direction=Vec3(0, 0, -1),
            axle=Vec3(-1, 0, 0),
            suspension_rest_length=suspension_length,
            wheel_radius=wheel_radius,
            is_front_wheel=False
        )
        
        print("Vehicle created with 4 wheels")
    
    def setup_soft_bodies(self):
        """Create soft body physics objects."""
        # Create a cloth
        cloth = self.physics.create_soft_body_patch(
            name="flag",
            corner1=Point3(-5, 5, 5),
            corner2=Point3(-3, 5, 5),
            corner3=Point3(-5, 5, 3),
            corner4=Point3(-3, 5, 3),
            res_x=10,
            res_y=10,
            fixed_corners=1  # Fix top-left corner
        )
        
        # Create a rope
        rope = self.physics.create_soft_body_rope(
            name="rope",
            start=Point3(5, 5, 5),
            end=Point3(5, 5, 0),
            segments=20,
            fixed_ends=1  # Fix top end
        )
        
        print("Soft bodies created: cloth and rope")
    
    def setup_character(self):
        """Create character controller."""
        self.character = self.physics.create_character_controller(
            name="player",
            radius=0.5,
            height=1.8,
            step_height=0.4
        )
        
        # Position character
        if self.character:
            self.character.setPos(10, 0, 2)
        
        print("Character controller created")
    
    def accelerate(self):
        """Accelerate vehicle."""
        if hasattr(self, 'vehicle') and self.vehicle:
            # Apply engine force to rear wheels
            self.vehicle.setEngineForce(2000, 2)  # Rear left
            self.vehicle.setEngineForce(2000, 3)  # Rear right
    
    def brake(self):
        """Apply brakes."""
        if hasattr(self, 'vehicle') and self.vehicle:
            # Apply brake force to all wheels
            for i in range(4):
                self.vehicle.setBrake(100, i)
    
    def steer_left(self):
        """Steer left."""
        if hasattr(self, 'vehicle') and self.vehicle:
            self.vehicle.setSteeringValue(0.5, 0)  # Front left
            self.vehicle.setSteeringValue(0.5, 1)  # Front right
    
    def steer_right(self):
        """Steer right."""
        if hasattr(self, 'vehicle') and self.vehicle:
            self.vehicle.setSteeringValue(-0.5, 0)  # Front left
            self.vehicle.setSteeringValue(-0.5, 1)  # Front right
    
    def jump(self):
        """Make character jump."""
        if hasattr(self, 'character') and self.character:
            self.character.setLinearVelocity(Vec3(0, 0, 5))
    
    def update(self, task):
        """Update physics simulation."""
        dt = globalClock.getDt()
        self.physics.update(dt)
        return task.cont


if __name__ == "__main__":
    demo = VehicleDemo()
    demo.run()
