"""Physics system using Panda3D's Bullet integration.

Supports:
- Rigid bodies (static, dynamic, kinematic)
- Soft bodies (cloth, rope, deformable meshes)
- Constraints (hinge, slider, point-to-point, cone-twist)
- Vehicles with raycast suspension
- Character controllers
- Trigger volumes
"""
import logging
from typing import Optional, Tuple, List, Dict
from panda3d.core import Vec3, BitMask32, NodePath, TransformState
from panda3d.bullet import (
    BulletWorld,
    BulletRigidBodyNode,
    BulletBoxShape,
    BulletSphereShape,
    BulletPlaneShape,
    BulletCapsuleShape,
    BulletCylinderShape,
    BulletConeShape,
    BulletDebugNode,
    BulletVehicle,
    BulletCharacterControllerNode,
    BulletHingeConstraint,
    BulletSliderConstraint,
    BulletConeTwistConstraint,
    BulletPoint2PointConstraint,
    BulletGenericConstraint,
    BulletSoftBodyNode,
    BulletSoftBodyConfig,
    ZUp
)

logger = logging.getLogger(__name__)


class PhysicsManager:
    """Manages Bullet physics simulation."""
    
    def __init__(self, gravity: float = -9.81, simulation_rate: int = 60):
        """Initialize physics world.
        
        Args:
            gravity: Gravity acceleration (default: -9.81 m/s²)
            simulation_rate: Physics simulation rate in Hz
        """
        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, gravity))
        self.simulation_rate = simulation_rate
        self.time_step = 1.0 / simulation_rate
        self.accumulator = 0.0
        self.debug_node: Optional[BulletDebugNode] = None
        self.debug_enabled = False
        
        logger.info(f"Physics initialized: gravity={gravity}, rate={simulation_rate}Hz")
    
    def update(self, dt: float) -> None:
        """Update physics simulation.
        
        Uses fixed timestep for deterministic physics.
        
        Args:
            dt: Delta time since last frame
        """
        self.accumulator += dt
        
        while self.accumulator >= self.time_step:
            self.world.do_physics(self.time_step)
            self.accumulator -= self.time_step
    
    def add_rigid_body(self, node: BulletRigidBodyNode) -> None:
        """Add a rigid body to the physics world.
        
        Args:
            node: Bullet rigid body node to add
        """
        self.world.attach(node)
    
    def remove_rigid_body(self, node: BulletRigidBodyNode) -> None:
        """Remove a rigid body from the physics world.
        
        Args:
            node: Bullet rigid body node to remove
        """
        self.world.remove(node)
    
    def create_box(self, name: str, half_extents: Tuple[float, float, float],
                   mass: float = 1.0) -> BulletRigidBodyNode:
        """Create a box-shaped rigid body.
        
        Args:
            name: Node name
            half_extents: Half extents (width/2, depth/2, height/2)
            mass: Mass in kg (0 = static)
            
        Returns:
            Configured rigid body node
        """
        shape = BulletBoxShape(Vec3(*half_extents))
        node = BulletRigidBodyNode(name)
        node.set_mass(mass)
        node.add_shape(shape)
        self.add_rigid_body(node)
        return node
    
    def create_sphere(self, name: str, radius: float,
                      mass: float = 1.0) -> BulletRigidBodyNode:
        """Create a sphere-shaped rigid body.
        
        Args:
            name: Node name
            radius: Sphere radius
            mass: Mass in kg (0 = static)
            
        Returns:
            Configured rigid body node
        """
        shape = BulletSphereShape(radius)
        node = BulletRigidBodyNode(name)
        node.set_mass(mass)
        node.add_shape(shape)
        self.add_rigid_body(node)
        return node
    
    def create_ground_plane(self, name: str = "ground") -> BulletRigidBodyNode:
        """Create an infinite ground plane at Z=0.
        
        Args:
            name: Node name
            
        Returns:
            Static ground plane rigid body
        """
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode(name)
        node.add_shape(shape)
        node.set_mass(0)  # Static
        self.add_rigid_body(node)
        return node
    
    def enable_debug(self, render_node) -> None:
        """Enable physics debug visualization.
        
        Args:
            render_node: Panda3D render node to attach debug geometry
        """
        if not self.debug_enabled:
            self.debug_node = BulletDebugNode('physics_debug')
            self.debug_node.show_wireframe(True)
            self.debug_node.show_constraints(True)
            self.debug_node.show_bounding_boxes(False)
            self.debug_node.show_normals(False)
            
            self.world.set_debug_node(self.debug_node)
            debug_np = render_node.attach_new_node(self.debug_node)
            debug_np.show()
            
            self.debug_enabled = True
            logger.info("Physics debug visualization enabled")
    
    def disable_debug(self) -> None:
        """Disable physics debug visualization."""
        if self.debug_enabled and self.debug_node:
            self.world.set_debug_node(None)
            self.debug_enabled = False
            logger.info("Physics debug visualization disabled")
    
    def raycast(self, from_pos: Vec3, to_pos: Vec3) -> Optional[any]:
        """Perform a ray cast in the physics world.
        
        Args:
            from_pos: Ray start position
            to_pos: Ray end position
            
        Returns:
            Hit result or None
        """
        result = self.world.ray_test_closest(from_pos, to_pos)
        if result.has_hit():
            return result
        return None
    
    def set_gravity(self, gravity: float) -> None:
        """Change gravity.
        
        Args:
            gravity: New gravity value
        """
        self.world.set_gravity(Vec3(0, 0, gravity))
        logger.info(f"Gravity changed to {gravity}")
    
    # ========== Advanced Shape Creators ==========
    
    def create_capsule(self, name: str, radius: float, height: float,
                       mass: float = 1.0, axis: str = 'Z') -> BulletRigidBodyNode:
        """Create a capsule-shaped rigid body.
        
        Args:
            name: Node name
            radius: Capsule radius
            height: Capsule height
            mass: Mass in kg
            axis: Capsule axis ('X', 'Y', or 'Z')
            
        Returns:
            Configured rigid body node
        """
        if axis == 'Z':
            shape = BulletCapsuleShape(radius, height, ZUp)
        elif axis == 'Y':
            shape = BulletCapsuleShape(radius, height)
        else:  # X
            shape = BulletCapsuleShape(radius, height)
        
        node = BulletRigidBodyNode(name)
        node.set_mass(mass)
        node.add_shape(shape)
        self.add_rigid_body(node)
        return node
    
    def create_cylinder(self, name: str, radius: float, height: float,
                        mass: float = 1.0) -> BulletRigidBodyNode:
        """Create a cylinder-shaped rigid body.
        
        Args:
            name: Node name
            radius: Cylinder radius
            height: Cylinder height
            mass: Mass in kg
            
        Returns:
            Configured rigid body node
        """
        shape = BulletCylinderShape(radius, height, ZUp)
        node = BulletRigidBodyNode(name)
        node.set_mass(mass)
        node.add_shape(shape)
        self.add_rigid_body(node)
        return node
    
    def create_cone(self, name: str, radius: float, height: float,
                    mass: float = 1.0) -> BulletRigidBodyNode:
        """Create a cone-shaped rigid body.
        
        Args:
            name: Node name
            radius: Cone base radius
            height: Cone height
            mass: Mass in kg
            
        Returns:
            Configured rigid body node
        """
        shape = BulletConeShape(radius, height, ZUp)
        node = BulletRigidBodyNode(name)
        node.set_mass(mass)
        node.add_shape(shape)
        self.add_rigid_body(node)
        return node
    
    # ========== Constraints ==========
    
    def add_hinge_constraint(self, node_a: NodePath, node_b: NodePath,
                             pivot_a: Vec3, pivot_b: Vec3,
                             axis_a: Vec3, axis_b: Vec3,
                             limits: Optional[Tuple[float, float]] = None) -> BulletHingeConstraint:
        """Create a hinge constraint between two bodies.
        
        Args:
            node_a: First body
            node_b: Second body
            pivot_a: Pivot point in A's local space
            pivot_b: Pivot point in B's local space
            axis_a: Hinge axis in A's local space
            axis_b: Hinge axis in B's local space
            limits: Optional (min_angle, max_angle) in radians
            
        Returns:
            Created constraint
        """
        constraint = BulletHingeConstraint(
            node_a.node(), node_b.node(),
            pivot_a, pivot_b,
            axis_a, axis_b
        )
        
        if limits:
            constraint.set_limit(limits[0], limits[1])
        
        self.world.attach(constraint)
        logger.info(f"Hinge constraint added between {node_a.name} and {node_b.name}")
        return constraint
    
    def add_slider_constraint(self, node_a: NodePath, node_b: NodePath,
                               frame_a: TransformState, frame_b: TransformState,
                               limits: Optional[Tuple[float, float]] = None) -> BulletSliderConstraint:
        """Create a slider constraint between two bodies.
        
        Args:
            node_a: First body
            node_b: Second body
            frame_a: Transform in A's local space
            frame_b: Transform in B's local space
            limits: Optional (min_distance, max_distance)
            
        Returns:
            Created constraint
        """
        constraint = BulletSliderConstraint(
            node_a.node(), node_b.node(),
            frame_a, frame_b
        )
        
        if limits:
            constraint.set_lower_linear_limit(limits[0])
            constraint.set_upper_linear_limit(limits[1])
        
        self.world.attach(constraint)
        logger.info(f"Slider constraint added between {node_a.name} and {node_b.name}")
        return constraint
    
    def add_point_to_point_constraint(self, node_a: NodePath, node_b: NodePath,
                                       pivot_a: Vec3, pivot_b: Vec3) -> BulletPoint2PointConstraint:
        """Create a point-to-point (ball socket) constraint.
        
        Args:
            node_a: First body
            node_b: Second body
            pivot_a: Pivot point in A's local space
            pivot_b: Pivot point in B's local space
            
        Returns:
            Created constraint
        """
        constraint = BulletPoint2PointConstraint(
            node_a.node(), node_b.node(),
            pivot_a, pivot_b
        )
        
        self.world.attach(constraint)
        logger.info(f"Point-to-point constraint added between {node_a.name} and {node_b.name}")
        return constraint
    
    def add_cone_twist_constraint(self, node_a: NodePath, node_b: NodePath,
                                   frame_a: TransformState, frame_b: TransformState) -> BulletConeTwistConstraint:
        """Create a cone-twist constraint (ragdoll joints).
        
        Args:
            node_a: First body
            node_b: Second body
            frame_a: Transform in A's local space
            frame_b: Transform in B's local space
            
        Returns:
            Created constraint
        """
        constraint = BulletConeTwistConstraint(
            node_a.node(), node_b.node(),
            frame_a, frame_b
        )
        
        self.world.attach(constraint)
        logger.info(f"Cone-twist constraint added between {node_a.name} and {node_b.name}")
        return constraint
    
    # ========== Vehicles ==========
    
    def create_vehicle(self, chassis_node: NodePath, name: str = "vehicle") -> BulletVehicle:
        """Create a raycast vehicle.
        
        Args:
            chassis_node: NodePath containing the rigid body chassis
            name: Vehicle name
            
        Returns:
            BulletVehicle instance
        """
        vehicle = BulletVehicle(self.world, chassis_node.node())
        vehicle.set_coordinate_system(ZUp)
        self.world.attach(vehicle)
        
        logger.info(f"Vehicle '{name}' created")
        return vehicle
    
    def add_wheel(self, vehicle: BulletVehicle,
                  connection_point: Vec3,
                  direction: Vec3,
                  axle: Vec3,
                  suspension_rest_length: float,
                  wheel_radius: float,
                  is_front_wheel: bool) -> None:
        """Add a wheel to a vehicle.
        
        Args:
            vehicle: BulletVehicle instance
            connection_point: Wheel connection point in chassis space
            direction: Suspension direction (usually down)
            axle: Wheel axle direction
            suspension_rest_length: Natural suspension length
            wheel_radius: Wheel radius
            is_front_wheel: Whether this is a steering wheel
        """
        wheel = vehicle.create_wheel()
        wheel.set_node(None)  # Visual model set later
        wheel.set_chassis_connection_point_cs(connection_point)
        wheel.set_front_wheel(is_front_wheel)
        wheel.set_wheel_direction_cs(direction)
        wheel.set_wheel_axle_cs(axle)
        wheel.set_wheel_radius(wheel_radius)
        wheel.set_max_suspension_travel_cm(500.0)
        wheel.set_suspension_stiffness(20.0)
        wheel.set_wheels_damping_compression(4.4)
        wheel.set_wheels_damping_relaxation(2.3)
        wheel.set_friction_slip(10.5)
        wheel.set_roll_influence(0.1)
        
        logger.debug(f"Wheel added to vehicle at {connection_point}")
    
    # ========== Character Controller ==========
    
    def create_character_controller(self, name: str, radius: float, height: float,
                                     step_height: float = 0.4) -> BulletCharacterControllerNode:
        """Create a character controller for player movement.
        
        Args:
            name: Controller name
            radius: Character capsule radius
            height: Character height
            step_height: Maximum step height
            
        Returns:
            Character controller node
        """
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)
        node = BulletCharacterControllerNode(shape, step_height, name)
        node.set_gravity(abs(self.world.get_gravity().z))
        
        self.world.attach(node)
        logger.info(f"Character controller '{name}' created")
        return node
    
    # ========== Soft Bodies ==========
    
    def create_soft_body_patch(self, name: str, corner_1: Vec3, corner_2: Vec3,
                                corner_3: Vec3, corner_4: Vec3,
                                res_x: int = 10, res_y: int = 10,
                                fixed_corners: int = 0) -> BulletSoftBodyNode:
        """Create a soft body cloth patch.
        
        Args:
            name: Node name
            corner_1, corner_2, corner_3, corner_4: Patch corners
            res_x: Resolution in X direction
            res_y: Resolution in Y direction
            fixed_corners: Bitmask of fixed corners (0-15)
            
        Returns:
            Soft body node
        """
        node = BulletSoftBodyNode.make_patch(
            self.world.get_world_info(),
            corner_1, corner_2, corner_3, corner_4,
            res_x, res_y,
            fixed_corners, True
        )
        node.set_name(name)
        
        # Configure soft body
        cfg = node.get_cfg()
        cfg.set_positions_solver_iterations(2)
        cfg.set_collisions_flag(BulletSoftBodyConfig.CF_vertex_face_soft_soft, True)
        
        # Material properties
        mat = node.append_material()
        mat.set_linear_stiffness(0.4)
        node.generate_bending_constraints(2, mat)
        
        node.set_total_mass(1.0)
        
        self.world.attach(node)
        logger.info(f"Soft body patch '{name}' created")
        return node
    
    def create_soft_body_rope(self, name: str, start: Vec3, end: Vec3,
                              segments: int = 10, fixed_ends: int = 1) -> BulletSoftBodyNode:
        """Create a soft body rope.
        
        Args:
            name: Node name
            start: Rope start position
            end: Rope end position
            segments: Number of rope segments
            fixed_ends: Bitmask (1=start, 2=end, 3=both)
            
        Returns:
            Soft body node
        """
        node = BulletSoftBodyNode.make_rope(
            self.world.get_world_info(),
            start, end,
            segments, fixed_ends
        )
        node.set_name(name)
        
        # Configure rope
        cfg = node.get_cfg()
        cfg.set_positions_solver_iterations(4)
        
        mat = node.append_material()
        mat.set_linear_stiffness(0.8)
        
        node.set_total_mass(0.5)
        
        self.world.attach(node)
        logger.info(f"Soft body rope '{name}' created")
        return node
    
    # ========== Trigger Volumes ==========
    
    def create_trigger(self, name: str, shape, callback=None) -> BulletRigidBodyNode:
        """Create a trigger volume (ghost object).
        
        Args:
            name: Trigger name
            shape: Bullet shape
            callback: Function called when objects enter/exit
            
        Returns:
            Trigger node (with mass=0, kinematic=True)
        """
        node = BulletRigidBodyNode(name)
        node.add_shape(shape)
        node.set_mass(0)
        node.set_kinematic(True)
        node.set_ghost(True)
        
        self.add_rigid_body(node)
        
        if callback:
            # Store callback for later use
            if not hasattr(self, 'trigger_callbacks'):
                self.trigger_callbacks = {}
            self.trigger_callbacks[name] = callback
        
        logger.info(f"Trigger volume '{name}' created")
        return node
    
    def check_trigger_overlaps(self, trigger_node: BulletRigidBodyNode) -> List:
        """Check what objects overlap with a trigger.
        
        Args:
            trigger_node: Trigger to check
            
        Returns:
            List of overlapping nodes
        """
        overlapping = []
        for contact in self.world.contact_test(trigger_node).get_contacts():
            node0 = contact.get_node0()
            node1 = contact.get_node1()
            other = node1 if node0 == trigger_node else node0
            overlapping.append(other)
        
        return overlapping
