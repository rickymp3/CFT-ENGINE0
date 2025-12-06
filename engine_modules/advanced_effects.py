"""
CFT-ENGINE0 Advanced Water, Particles, and Cinematic Systems
Dynamic water simulation, GPU particle compute, and timeline-based cinematics
"""

import numpy as np
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.interval.IntervalGlobal import *
from typing import List, Dict, Optional, Callable, Tuple
import json


# ==================== Water Simulation ====================

class WaterSurface:
    """Dynamic water with waves, reflections, and refraction"""
    
    def __init__(self, base: ShowBase, size: Tuple[float, float] = (100, 100), resolution: int = 64):
        self.base = base
        self.size = size
        self.resolution = resolution
        
        # Water properties
        self.wave_amplitude = 0.5
        self.wave_frequency = 1.0
        self.wave_speed = 2.0
        self.water_color = Vec4(0.0, 0.3, 0.5, 0.8)
        self.foam_threshold = 0.3
        
        # Physical simulation
        self.height_field = np.zeros((resolution, resolution), dtype=np.float32)
        self.velocity_field = np.zeros((resolution, resolution), dtype=np.float32)
        self.dampening = 0.99
        
        # Rendering
        self.water_node: Optional[NodePath] = None
        self.reflection_buffer: Optional[GraphicsOutput] = None
        self.refraction_buffer: Optional[GraphicsOutput] = None
        self.reflection_texture: Optional[Texture] = None
        self.refraction_texture: Optional[Texture] = None
        
        # Shader
        self.shader: Optional[Shader] = None
        
        self.time = 0.0
        
        self._create_water_mesh()
        self._create_render_targets()
        self._create_shader()
    
    def _create_water_mesh(self):
        """Create water surface mesh"""
        format = GeomVertexFormat.get_v3n3t2()
        vdata = GeomVertexData('water', format, Geom.UH_dynamic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Generate grid
        step_x = self.size[0] / (self.resolution - 1)
        step_y = self.size[1] / (self.resolution - 1)
        
        for y in range(self.resolution):
            for x in range(self.resolution):
                px = x * step_x - self.size[0] / 2
                py = y * step_y - self.size[1] / 2
                pz = 0.0
                
                vertex.add_data3(px, py, pz)
                normal.add_data3(0, 0, 1)
                texcoord.add_data2(x / (self.resolution - 1), y / (self.resolution - 1))
        
        # Generate triangles
        tris = GeomTriangles(Geom.UH_static)
        for y in range(self.resolution - 1):
            for x in range(self.resolution - 1):
                i0 = y * self.resolution + x
                i1 = i0 + 1
                i2 = i0 + self.resolution
                i3 = i2 + 1
                
                tris.add_vertices(i0, i2, i1)
                tris.add_vertices(i1, i2, i3)
        
        geom = Geom(vdata)
        geom.add_primitive(tris)
        
        node = GeomNode('water_surface')
        node.add_geom(geom)
        
        self.water_node = self.base.render.attach_new_node(node)
        self.water_node.set_two_sided(True)
    
    def _create_render_targets(self):
        """Create reflection and refraction render targets"""
        # Reflection camera
        self.reflection_buffer = self.base.win.make_texture_buffer('reflection', 512, 512)
        self.reflection_texture = self.reflection_buffer.get_texture()
        
        reflection_cam = self.base.make_camera(self.reflection_buffer)
        reflection_cam.reparent_to(self.base.render)
        
        # Refraction camera
        self.refraction_buffer = self.base.win.make_texture_buffer('refraction', 512, 512)
        self.refraction_texture = self.refraction_buffer.get_texture()
        
        refraction_cam = self.base.make_camera(self.refraction_buffer)
        refraction_cam.reparent_to(self.base.render)
    
    def _create_shader(self):
        """Create water shader with reflection/refraction"""
        vertex_shader = """
        #version 150
        
        in vec4 p3d_Vertex;
        in vec3 p3d_Normal;
        in vec2 p3d_MultiTexCoord0;
        
        uniform mat4 p3d_ModelViewProjectionMatrix;
        uniform mat4 p3d_ModelMatrix;
        uniform float time;
        uniform float wave_amplitude;
        uniform float wave_frequency;
        
        out vec3 world_pos;
        out vec3 world_normal;
        out vec2 texcoord;
        out vec4 screen_pos;
        
        void main() {
            vec4 pos = p3d_Vertex;
            
            // Wave displacement
            float wave = sin(pos.x * wave_frequency + time) * cos(pos.y * wave_frequency + time);
            pos.z += wave * wave_amplitude;
            
            gl_Position = p3d_ModelViewProjectionMatrix * pos;
            world_pos = (p3d_ModelMatrix * pos).xyz;
            world_normal = normalize(p3d_Normal);
            texcoord = p3d_MultiTexCoord0;
            screen_pos = gl_Position;
        }
        """
        
        fragment_shader = """
        #version 150
        
        in vec3 world_pos;
        in vec3 world_normal;
        in vec2 texcoord;
        in vec4 screen_pos;
        
        uniform sampler2D reflection_texture;
        uniform sampler2D refraction_texture;
        uniform vec4 water_color;
        uniform vec3 camera_position;
        uniform float time;
        
        out vec4 frag_color;
        
        void main() {
            // Screen-space coordinates for reflection/refraction
            vec2 screen_uv = (screen_pos.xy / screen_pos.w) * 0.5 + 0.5;
            
            // Distort based on normal
            vec2 distortion = world_normal.xy * 0.02;
            
            vec4 reflection = texture(reflection_texture, screen_uv + distortion);
            vec4 refraction = texture(refraction_texture, screen_uv - distortion);
            
            // Fresnel effect
            vec3 view_dir = normalize(camera_position - world_pos);
            float fresnel = pow(1.0 - max(dot(view_dir, world_normal), 0.0), 3.0);
            
            // Mix reflection and refraction
            vec4 water = mix(refraction, reflection, fresnel);
            water = mix(water, water_color, 0.3);
            
            frag_color = water;
        }
        """
        
        self.shader = Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
        self.water_node.set_shader(self.shader)
    
    def simulate_waves(self, dt: float):
        """Simulate wave propagation"""
        # Simple wave equation: ∂²h/∂t² = c²∇²h
        wave_speed_sq = self.wave_speed ** 2
        
        # Calculate Laplacian
        laplacian = np.zeros_like(self.height_field)
        laplacian[1:-1, 1:-1] = (
            self.height_field[:-2, 1:-1] +
            self.height_field[2:, 1:-1] +
            self.height_field[1:-1, :-2] +
            self.height_field[1:-1, 2:] -
            4 * self.height_field[1:-1, 1:-1]
        )
        
        # Update velocity and position
        self.velocity_field += wave_speed_sq * laplacian * dt
        self.velocity_field *= self.dampening
        self.height_field += self.velocity_field * dt
    
    def add_disturbance(self, x: float, y: float, strength: float):
        """Add wave disturbance at position"""
        # Convert world coordinates to grid
        grid_x = int((x + self.size[0] / 2) / self.size[0] * self.resolution)
        grid_y = int((y + self.size[1] / 2) / self.size[1] * self.resolution)
        
        if 0 <= grid_x < self.resolution and 0 <= grid_y < self.resolution:
            self.height_field[grid_y, grid_x] += strength
    
    def update(self, dt: float):
        """Update water simulation"""
        self.time += dt
        
        # Simulate waves
        self.simulate_waves(dt)
        
        # Update shader
        if self.shader:
            self.water_node.set_shader_input("time", self.time)
            self.water_node.set_shader_input("wave_amplitude", self.wave_amplitude)
            self.water_node.set_shader_input("wave_frequency", self.wave_frequency)
            self.water_node.set_shader_input("water_color", self.water_color)
            self.water_node.set_shader_input("camera_position", self.base.camera.get_pos())
            self.water_node.set_shader_input("reflection_texture", self.reflection_texture)
            self.water_node.set_shader_input("refraction_texture", self.refraction_texture)


# ==================== GPU Particle System ====================

class GPUParticleSystem:
    """High-performance GPU-based particle system"""
    
    def __init__(self, base: ShowBase, max_particles: int = 100000):
        self.base = base
        self.max_particles = max_particles
        
        # Particle properties
        self.emission_rate = 1000.0
        self.particle_lifetime = 3.0
        self.particle_size = 0.1
        self.spawn_radius = 1.0
        
        # Forces
        self.gravity = Vec3(0, 0, -9.81)
        self.wind = Vec3(0, 0, 0)
        self.drag = 0.1
        
        # Appearance
        self.particle_texture: Optional[Texture] = None
        self.color_over_lifetime: List[Vec4] = [
            Vec4(1, 1, 1, 1),
            Vec4(1, 1, 0, 0.5),
            Vec4(1, 0, 0, 0)
        ]
        
        # GPU resources
        self.particle_buffer: Optional[Texture] = None
        self.compute_shader: Optional[ComputeNode] = None
        
        # State
        self.active_particles = 0
        self.emission_accumulator = 0.0
    
    def spawn_particle(self, position: Point3, velocity: Vec3):
        """Spawn new particle"""
        # Would write to particle buffer
        pass
    
    def spawn_burst(self, count: int, position: Point3):
        """Spawn burst of particles"""
        for _ in range(min(count, self.max_particles - self.active_particles)):
            # Random direction
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)
            
            velocity = Vec3(
                np.sin(phi) * np.cos(theta),
                np.sin(phi) * np.sin(theta),
                np.cos(phi)
            ) * 5.0
            
            self.spawn_particle(position, velocity)
    
    def update(self, dt: float):
        """Update particle simulation on GPU"""
        # Emit new particles
        self.emission_accumulator += self.emission_rate * dt
        while self.emission_accumulator >= 1.0:
            # Spawn particle
            self.emission_accumulator -= 1.0


# ==================== Cinematic Camera System ====================

class CameraRig:
    """Configurable camera rig for cinematics"""
    
    def __init__(self, name: str):
        self.name = name
        self.position = Point3(0, 0, 0)
        self.look_at = Point3(0, 0, 0)
        self.fov = 60.0
        self.near = 0.1
        self.far = 1000.0
        
        # Motion properties
        self.velocity = Vec3(0, 0, 0)
        self.path: List[Point3] = []
        self.path_time = 0.0
        self.path_duration = 1.0


class CinematicSequence:
    """Timeline-based cinematic sequence"""
    
    def __init__(self, name: str):
        self.name = name
        self.duration = 10.0
        self.current_time = 0.0
        self.is_playing = False
        
        # Timeline tracks
        self.camera_track: List[Tuple[float, CameraRig]] = []  # (time, camera_state)
        self.animation_track: List[Tuple[float, str, str]] = []  # (time, actor, anim_name)
        self.audio_track: List[Tuple[float, str]] = []  # (time, sound_name)
        self.event_track: List[Tuple[float, Callable]] = []  # (time, callback)
        
        # Post-processing
        self.depth_of_field_enabled = False
        self.dof_focus_distance = 10.0
        self.dof_blur_amount = 0.5
        
        self.motion_blur_enabled = False
        self.motion_blur_amount = 0.3
    
    def add_camera_keyframe(self, time: float, camera: CameraRig):
        """Add camera keyframe"""
        self.camera_track.append((time, camera))
        self.camera_track.sort(key=lambda x: x[0])
    
    def add_animation(self, time: float, actor: str, animation: str):
        """Add animation trigger"""
        self.animation_track.append((time, actor, animation))
    
    def add_audio(self, time: float, sound: str):
        """Add audio cue"""
        self.audio_track.append((time, sound))
    
    def add_event(self, time: float, callback: Callable):
        """Add custom event"""
        self.event_track.append((time, callback))
    
    def play(self):
        """Start playback"""
        self.is_playing = True
        self.current_time = 0.0
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
    
    def update(self, dt: float, camera: NodePath, audio_manager=None):
        """Update sequence"""
        if not self.is_playing:
            return
        
        self.current_time += dt
        
        if self.current_time >= self.duration:
            self.stop()
            return
        
        # Update camera
        if len(self.camera_track) >= 2:
            # Find surrounding keyframes
            prev_kf = None
            next_kf = None
            
            for time, cam in self.camera_track:
                if time <= self.current_time:
                    prev_kf = (time, cam)
                elif time > self.current_time and next_kf is None:
                    next_kf = (time, cam)
                    break
            
            if prev_kf and next_kf:
                # Interpolate
                t = (self.current_time - prev_kf[0]) / (next_kf[0] - prev_kf[0])
                
                pos = prev_kf[1].position + (next_kf[1].position - prev_kf[1].position) * t
                look = prev_kf[1].look_at + (next_kf[1].look_at - prev_kf[1].look_at) * t
                
                camera.set_pos(pos)
                camera.look_at(look)
        
        # Trigger events at current time
        for time, callback in self.event_track:
            if abs(time - self.current_time) < dt:
                callback()
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'name': self.name,
            'duration': self.duration,
            'camera_track': [
                {
                    'time': time,
                    'position': [cam.position.x, cam.position.y, cam.position.z],
                    'look_at': [cam.look_at.x, cam.look_at.y, cam.look_at.z],
                    'fov': cam.fov
                }
                for time, cam in self.camera_track
            ],
            'depth_of_field': {
                'enabled': self.depth_of_field_enabled,
                'focus_distance': self.dof_focus_distance,
                'blur_amount': self.dof_blur_amount
            },
            'motion_blur': {
                'enabled': self.motion_blur_enabled,
                'amount': self.motion_blur_amount
            }
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'CinematicSequence':
        """Deserialize from dictionary"""
        seq = CinematicSequence(data['name'])
        seq.duration = data['duration']
        
        for cam_data in data.get('camera_track', []):
            cam = CameraRig(f"keyframe_{cam_data['time']}")
            cam.position = Point3(*cam_data['position'])
            cam.look_at = Point3(*cam_data['look_at'])
            cam.fov = cam_data['fov']
            seq.add_camera_keyframe(cam_data['time'], cam)
        
        dof = data.get('depth_of_field', {})
        seq.depth_of_field_enabled = dof.get('enabled', False)
        seq.dof_focus_distance = dof.get('focus_distance', 10.0)
        seq.dof_blur_amount = dof.get('blur_amount', 0.5)
        
        mb = data.get('motion_blur', {})
        seq.motion_blur_enabled = mb.get('enabled', False)
        seq.motion_blur_amount = mb.get('amount', 0.3)
        
        return seq


class CinematicSystem:
    """Manages cinematic sequences"""
    
    def __init__(self, base: ShowBase):
        self.base = base
        self.sequences: Dict[str, CinematicSequence] = {}
        self.active_sequence: Optional[CinematicSequence] = None
    
    def create_sequence(self, name: str, duration: float = 10.0) -> CinematicSequence:
        """Create new cinematic sequence"""
        seq = CinematicSequence(name)
        seq.duration = duration
        self.sequences[name] = seq
        return seq
    
    def play_sequence(self, name: str):
        """Play cinematic sequence"""
        if name in self.sequences:
            self.active_sequence = self.sequences[name]
            self.active_sequence.play()
    
    def stop_sequence(self):
        """Stop active sequence"""
        if self.active_sequence:
            self.active_sequence.stop()
            self.active_sequence = None
    
    def save_sequence(self, name: str, filename: str):
        """Save sequence to file"""
        if name in self.sequences:
            with open(filename, 'w') as f:
                json.dump(self.sequences[name].to_dict(), f, indent=2)
    
    def load_sequence(self, filename: str) -> CinematicSequence:
        """Load sequence from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            seq = CinematicSequence.from_dict(data)
            self.sequences[seq.name] = seq
            return seq
    
    def update(self, dt: float):
        """Update active sequence"""
        if self.active_sequence:
            self.active_sequence.update(dt, self.base.camera)


# ==================== Combined System ====================

class AdvancedEffectsSystem:
    """Combines water, particles, and cinematics"""
    
    def __init__(self, base: ShowBase):
        self.base = base
        
        self.water_surfaces: List[WaterSurface] = []
        self.particle_systems: List[GPUParticleSystem] = []
        self.cinematic_system = CinematicSystem(base)
    
    def create_water(self, size: Tuple[float, float] = (100, 100)) -> WaterSurface:
        """Create water surface"""
        water = WaterSurface(self.base, size)
        self.water_surfaces.append(water)
        return water
    
    def create_particle_system(self, max_particles: int = 10000) -> GPUParticleSystem:
        """Create particle system"""
        particles = GPUParticleSystem(self.base, max_particles)
        self.particle_systems.append(particles)
        return particles
    
    def update(self, dt: float):
        """Update all systems"""
        for water in self.water_surfaces:
            water.update(dt)
        
        for particles in self.particle_systems:
            particles.update(dt)
        
        self.cinematic_system.update(dt)


def create_advanced_effects_system(base: ShowBase) -> AdvancedEffectsSystem:
    """Factory function"""
    return AdvancedEffectsSystem(base)
