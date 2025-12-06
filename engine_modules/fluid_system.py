"""
CFT-ENGINE0 Fluid, Cloth and Destruction System
SPH fluid simulation, enhanced cloth physics, destructible meshes
"""

import numpy as np
from panda3d.core import Point3, Vec3, Vec4, NodePath, GeomNode, Geom, GeomVertexData, GeomVertexFormat
from panda3d.core import GeomVertexWriter, GeomTriangles, GeomPoints, BoundingSphere
from panda3d.bullet import BulletSoftBodyNode, BulletSoftBodyConfig, BulletWorld
from typing import List, Tuple, Optional
import random


# ==================== SPH Fluid Simulation ====================

class SPHParticle:
    """Single particle in SPH simulation"""
    
    def __init__(self, position: Point3, mass: float = 1.0):
        self.position = np.array([position.x, position.y, position.z], dtype=np.float32)
        self.velocity = np.zeros(3, dtype=np.float32)
        self.force = np.zeros(3, dtype=np.float32)
        self.density = 0.0
        self.pressure = 0.0
        self.mass = mass


class SPHFluidSimulation:
    """Smoothed Particle Hydrodynamics fluid simulation"""
    
    def __init__(self, particle_count: int = 1000):
        self.particles: List[SPHParticle] = []
        
        # SPH parameters
        self.smoothing_radius = 0.5
        self.rest_density = 1000.0  # kg/m³
        self.gas_constant = 2000.0
        self.viscosity = 0.02
        self.gravity = np.array([0, 0, -9.81], dtype=np.float32)
        self.time_step = 0.01
        
        # Spatial grid for neighbor search
        self.grid_cell_size = self.smoothing_radius
        self.grid: dict = {}
        
        # Rendering
        self.visual_node: Optional[NodePath] = None
        self.update_visual = True
    
    def add_particle(self, position: Point3, velocity: Vec3 = Vec3(0, 0, 0)):
        """Add particle to simulation"""
        particle = SPHParticle(position)
        particle.velocity = np.array([velocity.x, velocity.y, velocity.z], dtype=np.float32)
        self.particles.append(particle)
    
    def spawn_cube(self, center: Point3, size: float, spacing: float):
        """Spawn particles in a cube formation"""
        half_size = size / 2
        count_per_axis = int(size / spacing)
        
        for x in range(count_per_axis):
            for y in range(count_per_axis):
                for z in range(count_per_axis):
                    pos = Point3(
                        center.x - half_size + x * spacing,
                        center.y - half_size + y * spacing,
                        center.z - half_size + z * spacing
                    )
                    self.add_particle(pos)
    
    def _update_grid(self):
        """Update spatial hash grid"""
        self.grid.clear()
        
        for particle in self.particles:
            cell = self._get_cell(particle.position)
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append(particle)
    
    def _get_cell(self, position: np.ndarray) -> Tuple[int, int, int]:
        """Get grid cell for position"""
        return (
            int(position[0] / self.grid_cell_size),
            int(position[1] / self.grid_cell_size),
            int(position[2] / self.grid_cell_size)
        )
    
    def _get_neighbors(self, particle: SPHParticle) -> List[SPHParticle]:
        """Get neighboring particles within smoothing radius"""
        cell = self._get_cell(particle.position)
        neighbors = []
        
        # Check 27 neighboring cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    check_cell = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                    if check_cell in self.grid:
                        for other in self.grid[check_cell]:
                            if other != particle:
                                dist = np.linalg.norm(particle.position - other.position)
                                if dist < self.smoothing_radius:
                                    neighbors.append(other)
        
        return neighbors
    
    def _poly6_kernel(self, r: float, h: float) -> float:
        """Poly6 smoothing kernel"""
        if r >= 0 and r <= h:
            coefficient = 315.0 / (64.0 * np.pi * h**9)
            return coefficient * (h**2 - r**2)**3
        return 0.0
    
    def _spiky_gradient(self, r_vec: np.ndarray, h: float) -> np.ndarray:
        """Spiky kernel gradient for pressure"""
        r = np.linalg.norm(r_vec)
        if r > 0 and r <= h:
            coefficient = -45.0 / (np.pi * h**6)
            return coefficient * (h - r)**2 * (r_vec / r)
        return np.zeros(3, dtype=np.float32)
    
    def _viscosity_laplacian(self, r: float, h: float) -> float:
        """Viscosity kernel laplacian"""
        if r >= 0 and r <= h:
            coefficient = 45.0 / (np.pi * h**6)
            return coefficient * (h - r)
        return 0.0
    
    def _compute_density_pressure(self):
        """Compute density and pressure for all particles"""
        for particle in self.particles:
            particle.density = 0.0
            neighbors = self._get_neighbors(particle)
            
            for other in neighbors:
                r = np.linalg.norm(particle.position - other.position)
                particle.density += other.mass * self._poly6_kernel(r, self.smoothing_radius)
            
            # Add self contribution
            particle.density += particle.mass * self._poly6_kernel(0, self.smoothing_radius)
            
            # Compute pressure from density
            particle.pressure = self.gas_constant * (particle.density - self.rest_density)
    
    def _compute_forces(self):
        """Compute pressure and viscosity forces"""
        for particle in self.particles:
            particle.force = self.gravity * particle.mass
            neighbors = self._get_neighbors(particle)
            
            for other in neighbors:
                r_vec = particle.position - other.position
                r = np.linalg.norm(r_vec)
                
                if r > 0:
                    # Pressure force
                    pressure_force = -other.mass * (particle.pressure + other.pressure) / (2.0 * other.density)
                    pressure_force *= self._spiky_gradient(r_vec, self.smoothing_radius)
                    particle.force += pressure_force
                    
                    # Viscosity force
                    velocity_diff = other.velocity - particle.velocity
                    viscosity_force = self.viscosity * other.mass * velocity_diff / other.density
                    viscosity_force *= self._viscosity_laplacian(r, self.smoothing_radius)
                    particle.force += viscosity_force
    
    def _integrate(self, dt: float):
        """Integrate particles forward in time"""
        for particle in self.particles:
            # Update velocity
            particle.velocity += (particle.force / particle.mass) * dt
            
            # Update position
            particle.position += particle.velocity * dt
            
            # Simple boundary conditions (box)
            bounds = 10.0
            for i in range(3):
                if particle.position[i] < -bounds:
                    particle.position[i] = -bounds
                    particle.velocity[i] *= -0.5
                elif particle.position[i] > bounds:
                    particle.position[i] = bounds
                    particle.velocity[i] *= -0.5
    
    def update(self, dt: float):
        """Update fluid simulation"""
        substeps = max(1, int(dt / self.time_step))
        step_dt = dt / substeps
        
        for _ in range(substeps):
            self._update_grid()
            self._compute_density_pressure()
            self._compute_forces()
            self._integrate(step_dt)
    
    def create_visual(self, render: NodePath) -> NodePath:
        """Create particle visualization"""
        vdata = GeomVertexData('fluid', GeomVertexFormat.get_v3(), Geom.UH_dynamic)
        vdata.set_num_rows(len(self.particles))
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        for particle in self.particles:
            vertex.add_data3(particle.position[0], particle.position[1], particle.position[2])
        
        points = GeomPoints(Geom.UH_dynamic)
        points.add_next_vertices(len(self.particles))
        
        geom = Geom(vdata)
        geom.add_primitive(points)
        
        node = GeomNode('fluid_particles')
        node.add_geom(geom)
        
        self.visual_node = render.attach_new_node(node)
        self.visual_node.set_render_mode_thickness(5)
        self.visual_node.set_color(0.2, 0.5, 1.0, 0.8)
        
        return self.visual_node
    
    def update_visual(self):
        """Update particle positions in visual"""
        if not self.visual_node:
            return
        
        geom_node = self.visual_node.node()
        geom = geom_node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        for particle in self.particles:
            vertex.set_data3(particle.position[0], particle.position[1], particle.position[2])


# ==================== Enhanced Cloth Physics ====================

class ClothSystem:
    """Advanced cloth simulation using Bullet soft bodies"""
    
    def __init__(self, physics_world: BulletWorld):
        self.world = physics_world
        self.cloth_bodies: List[BulletSoftBodyNode] = []
    
    def create_cloth(self, corner1: Point3, corner2: Point3, resolution_x: int = 20, resolution_y: int = 20) -> NodePath:
        """Create cloth mesh"""
        # This is a simplified version - full implementation would use Bullet's cloth API
        cloth_node = BulletSoftBodyNode.make_patch(
            corner1, corner2,
            resolution_x, resolution_y,
            0, True  # Generate diagonal links
        )
        
        # Configure cloth material
        cfg = cloth_node.get_cfg()
        cfg.set_dynamic_friction_coefficient(0.5)
        cfg.set_damping_coefficient(0.01)
        cfg.set_pressure_coefficient(0.0)
        
        # Set cloth properties
        cloth_node.get_material(0).set_linear_stiffness(0.9)
        cloth_node.set_total_mass(1.0)
        
        self.world.attach(cloth_node)
        self.cloth_bodies.append(cloth_node)
        
        return NodePath(cloth_node)
    
    def pin_cloth_corner(self, cloth: NodePath, corner_index: int):
        """Pin a corner of the cloth"""
        cloth_node = cloth.node()
        if isinstance(cloth_node, BulletSoftBodyNode):
            # Pin node at corner
            cloth_node.set_mass(corner_index, 0)


# ==================== Destruction System ====================

class FracturePattern:
    """Pattern for fracturing meshes"""
    
    @staticmethod
    def voronoi_fracture(center: Point3, num_fragments: int = 10, radius: float = 5.0) -> List[Point3]:
        """Generate Voronoi fracture points"""
        points = []
        for _ in range(num_fragments):
            # Random point in sphere
            theta = random.uniform(0, 2 * np.pi)
            phi = random.uniform(0, np.pi)
            r = random.uniform(0, radius)
            
            x = center.x + r * np.sin(phi) * np.cos(theta)
            y = center.y + r * np.sin(phi) * np.sin(theta)
            z = center.z + r * np.cos(phi)
            
            points.append(Point3(x, y, z))
        
        return points


class DestructibleObject:
    """Object that can be fractured and destroyed"""
    
    def __init__(self, node_path: NodePath, physics_world: BulletWorld):
        self.node_path = node_path
        self.physics_world = physics_world
        self.is_fractured = False
        self.fragments: List[NodePath] = []
        self.health = 100.0
        self.fracture_threshold = 50.0
    
    def take_damage(self, damage: float, impact_point: Point3):
        """Apply damage and potentially fracture"""
        self.health -= damage
        
        if self.health <= self.fracture_threshold and not self.is_fractured:
            self.fracture(impact_point)
    
    def fracture(self, impact_point: Point3, num_fragments: int = 8):
        """Fracture object into pieces"""
        if self.is_fractured:
            return
        
        self.is_fractured = True
        
        # Generate fracture pattern
        fracture_points = FracturePattern.voronoi_fracture(impact_point, num_fragments)
        
        # For each fracture point, create a fragment
        # (Simplified - real implementation would use mesh splitting)
        for i, point in enumerate(fracture_points):
            # Clone original mesh (simplified)
            fragment = self.node_path.copy_to(self.node_path.get_parent())
            fragment.set_pos(point)
            fragment.set_scale(0.3)  # Make fragments smaller
            
            # Add physics to fragment
            # (Would need proper collision shape from fractured mesh)
            
            self.fragments.append(fragment)
        
        # Hide original
        self.node_path.hide()


# ==================== Fluid System Manager ====================

class FluidSystem:
    """Manages all fluid, cloth and destruction simulations"""
    
    def __init__(self, base, physics_world: BulletWorld):
        self.base = base
        self.physics_world = physics_world
        
        self.fluid_simulations: List[SPHFluidSimulation] = []
        self.cloth_system = ClothSystem(physics_world)
        self.destructible_objects: List[DestructibleObject] = []
    
    def create_fluid_simulation(self, particle_count: int = 1000) -> SPHFluidSimulation:
        """Create new fluid simulation"""
        sim = SPHFluidSimulation(particle_count)
        self.fluid_simulations.append(sim)
        return sim
    
    def create_cloth(self, corner1: Point3, corner2: Point3, resolution_x: int = 20, resolution_y: int = 20) -> NodePath:
        """Create cloth"""
        return self.cloth_system.create_cloth(corner1, corner2, resolution_x, resolution_y)
    
    def make_destructible(self, node_path: NodePath) -> DestructibleObject:
        """Make object destructible"""
        obj = DestructibleObject(node_path, self.physics_world)
        self.destructible_objects.append(obj)
        return obj
    
    def update(self, dt: float):
        """Update all systems"""
        for sim in self.fluid_simulations:
            sim.update(dt)
            if sim.update_visual and sim.visual_node:
                sim.update_visual()


def create_fluid_system(base, physics_world: BulletWorld) -> FluidSystem:
    """Factory function"""
    return FluidSystem(base, physics_world)
