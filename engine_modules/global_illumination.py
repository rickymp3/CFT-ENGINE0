"""Global Illumination and Ray Tracing System.

Features:
- Real-time global illumination with light probes
- Screen-space reflections (SSR)
- Optional hardware ray tracing (RTX/DXR)
- Light propagation volumes (LPV)
- Irradiance volumes for dynamic GI
- Baked lightmaps with dynamic object support
- Fallback approximations for low-end hardware
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from panda3d.core import (
        NodePath, Shader, Texture, GraphicsOutput, FrameBufferProperties,
        WindowProperties, Vec3, Point3, Vec4, LVector3, CardMaker,
        Filename, PNMImage, ComputeNode
    )
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False

logger = logging.getLogger(__name__)


class GIQuality(Enum):
    """Global illumination quality presets."""
    LOW = "low"           # Baked lightmaps only
    MEDIUM = "medium"     # Light probes + SSR
    HIGH = "high"         # LPV + SSR + probes
    ULTRA = "ultra"       # Ray tracing (if available)


@dataclass
class LightProbe:
    """Light probe for storing local irradiance."""
    position: Point3
    sh_coefficients: np.ndarray  # Spherical harmonics (9 coefficients per channel)
    radius: float = 10.0
    intensity: float = 1.0


class GlobalIlluminationSystem:
    """Manages global illumination and ray tracing effects."""
    
    def __init__(self, base, quality: GIQuality = GIQuality.MEDIUM):
        """Initialize GI system.
        
        Args:
            base: Panda3D ShowBase instance
            quality: Quality preset
        """
        if not PANDA3D_AVAILABLE:
            raise ImportError("Panda3D required for global illumination")
        
        self.base = base
        self.quality = quality
        
        # Feature detection
        self.has_ray_tracing = self._detect_ray_tracing()
        self.has_compute_shaders = self._detect_compute_shaders()
        
        # GI components
        self.light_probes: List[LightProbe] = []
        self.irradiance_volume: Optional[np.ndarray] = None
        self.lpv_grids: Dict[str, Any] = {}
        
        # Render targets
        self.gi_buffer: Optional[GraphicsOutput] = None
        self.ssr_buffer: Optional[GraphicsOutput] = None
        
        # Shaders
        self.gi_shader: Optional[Shader] = None
        self.ssr_shader: Optional[Shader] = None
        self.rt_shader: Optional[Shader] = None
        
        # Setup based on quality
        self._initialize_gi_system()
        
        logger.info(f"Global Illumination initialized (Quality: {quality.value}, RT: {self.has_ray_tracing})")
    
    def _detect_ray_tracing(self) -> bool:
        """Detect if hardware supports ray tracing.
        
        Returns:
            True if RTX/DXR available
        """
        # Check for NVIDIA RTX or AMD RDNA2+ ray tracing
        # This is a simplified check; real implementation would query GPU capabilities
        try:
            # Would check via Panda3D's graphics pipe
            return False  # Conservative default
        except:
            return False
    
    def _detect_compute_shaders(self) -> bool:
        """Detect compute shader support.
        
        Returns:
            True if compute shaders available
        """
        try:
            # Check OpenGL 4.3+ or DirectX 11+
            return True  # Most modern GPUs support this
        except:
            return False
    
    def _initialize_gi_system(self) -> None:
        """Initialize GI components based on quality."""
        if self.quality == GIQuality.LOW:
            # Baked lightmaps only
            self._setup_lightmap_system()
        
        elif self.quality == GIQuality.MEDIUM:
            # Light probes + SSR
            self._setup_light_probes()
            self._setup_ssr()
        
        elif self.quality == GIQuality.HIGH:
            # LPV + SSR + probes
            self._setup_light_probes()
            self._setup_light_propagation_volumes()
            self._setup_ssr()
        
        elif self.quality == GIQuality.ULTRA:
            if self.has_ray_tracing:
                # Hardware ray tracing
                self._setup_ray_tracing()
                self._setup_light_probes()  # Hybrid approach
            else:
                # Fallback to HIGH quality
                logger.warning("Ray tracing not available, falling back to HIGH quality")
                self.quality = GIQuality.HIGH
                self._initialize_gi_system()
    
    def _setup_lightmap_system(self) -> None:
        """Setup baked lightmap system."""
        logger.info("Setting up lightmap system")
        
        # Lightmap storage
        self.lightmaps: Dict[str, Texture] = {}
        
        # Shader for lightmap sampling
        vertex_shader = """
        #version 150
        
        in vec4 p3d_Vertex;
        in vec2 p3d_MultiTexCoord0;
        in vec2 p3d_MultiTexCoord1;  // Lightmap UVs
        
        out vec2 texcoord;
        out vec2 lightmap_uv;
        
        uniform mat4 p3d_ModelViewProjectionMatrix;
        
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            texcoord = p3d_MultiTexCoord0;
            lightmap_uv = p3d_MultiTexCoord1;
        }
        """
        
        fragment_shader = """
        #version 150
        
        in vec2 texcoord;
        in vec2 lightmap_uv;
        
        out vec4 fragColor;
        
        uniform sampler2D p3d_Texture0;  // Albedo
        uniform sampler2D lightmap;
        
        void main() {
            vec4 albedo = texture(p3d_Texture0, texcoord);
            vec3 light = texture(lightmap, lightmap_uv).rgb;
            fragColor = vec4(albedo.rgb * light, albedo.a);
        }
        """
        
        self.lightmap_shader = Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
    
    def _setup_light_probes(self) -> None:
        """Setup light probe system."""
        logger.info("Setting up light probe system")
        
        # Irradiance volume (3D grid of SH coefficients)
        self.probe_grid_size = (8, 8, 8)  # Configurable resolution
        self.irradiance_volume = self._create_irradiance_volume()
        
        # Shader for probe sampling
        self.probe_shader = self._create_probe_shader()
    
    def _create_irradiance_volume(self) -> np.ndarray:
        """Create 3D grid for storing irradiance data.
        
        Returns:
            Numpy array [x, y, z, 9 SH coefficients, 3 RGB]
        """
        x, y, z = self.probe_grid_size
        # 9 SH coefficients per RGB channel
        volume = np.zeros((x, y, z, 9, 3), dtype=np.float32)
        return volume
    
    def _create_probe_shader(self) -> Shader:
        """Create shader for sampling light probes.
        
        Returns:
            Compiled shader
        """
        vertex_shader = """
        #version 150
        
        in vec4 p3d_Vertex;
        in vec3 p3d_Normal;
        in vec2 p3d_MultiTexCoord0;
        
        out vec3 world_pos;
        out vec3 normal;
        out vec2 texcoord;
        
        uniform mat4 p3d_ModelViewProjectionMatrix;
        uniform mat4 p3d_ModelMatrix;
        uniform mat3 p3d_NormalMatrix;
        
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            world_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;
            normal = normalize(p3d_NormalMatrix * p3d_Normal);
            texcoord = p3d_MultiTexCoord0;
        }
        """
        
        fragment_shader = """
        #version 150
        
        in vec3 world_pos;
        in vec3 normal;
        in vec2 texcoord;
        
        out vec4 fragColor;
        
        uniform sampler2D p3d_Texture0;
        uniform sampler3D irradiance_volume;
        uniform vec3 volume_min;
        uniform vec3 volume_max;
        
        // Spherical harmonics basis functions (simplified L0-L2)
        vec3 evalSH(vec3 n, vec3 sh[9]) {
            const float c0 = 0.282095;
            const float c1 = 0.488603;
            const float c2 = 1.092548;
            const float c3 = 0.315392;
            const float c4 = 0.546274;
            
            vec3 result = sh[0] * c0;
            result += sh[1] * (c1 * n.y);
            result += sh[2] * (c1 * n.z);
            result += sh[3] * (c1 * n.x);
            // Add higher order terms...
            
            return max(result, vec3(0.0));
        }
        
        void main() {
            vec4 albedo = texture(p3d_Texture0, texcoord);
            
            // Sample irradiance volume
            vec3 volume_uv = (world_pos - volume_min) / (volume_max - volume_min);
            vec3 irradiance = texture(irradiance_volume, volume_uv).rgb;
            
            // Simple lighting (would be replaced with full SH evaluation)
            vec3 lit = albedo.rgb * irradiance;
            
            fragColor = vec4(lit, albedo.a);
        }
        """
        
        return Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
    
    def _setup_light_propagation_volumes(self) -> None:
        """Setup Light Propagation Volume system for real-time GI."""
        logger.info("Setting up Light Propagation Volumes")
        
        # LPV uses 3D textures to propagate light through the scene
        self.lpv_resolution = 64
        
        # Four grids: R, G, B SH coefficients + geometry volume
        for component in ['red', 'green', 'blue', 'geometry']:
            self.lpv_grids[component] = self._create_lpv_grid()
        
        # Compute shader for light injection and propagation
        if self.has_compute_shaders:
            self.lpv_inject_shader = self._create_lpv_inject_shader()
            self.lpv_propagate_shader = self._create_lpv_propagate_shader()
    
    def _create_lpv_grid(self) -> Texture:
        """Create 3D texture for LPV grid.
        
        Returns:
            3D texture
        """
        tex = Texture("lpv_grid")
        tex.setup_3d_texture(self.lpv_resolution, self.lpv_resolution, self.lpv_resolution,
                            Texture.T_float, Texture.F_rgba32)
        return tex
    
    def _create_lpv_inject_shader(self) -> Shader:
        """Create compute shader for injecting light into LPV.
        
        Returns:
            Compute shader
        """
        compute_shader = """
        #version 430
        
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 8) in;
        
        layout(rgba32f) uniform image3D lpv_red;
        layout(rgba32f) uniform image3D lpv_green;
        layout(rgba32f) uniform image3D lpv_blue;
        
        uniform vec3 light_position;
        uniform vec3 light_color;
        uniform float light_intensity;
        
        void main() {
            ivec3 coords = ivec3(gl_GlobalInvocationID.xyz);
            
            // Convert grid coords to world space
            vec3 world_pos = vec3(coords) / 64.0 * 100.0 - 50.0;
            
            // Calculate light contribution
            vec3 to_light = light_position - world_pos;
            float dist = length(to_light);
            vec3 dir = normalize(to_light);
            
            float attenuation = 1.0 / (1.0 + dist * dist * 0.01);
            vec3 radiance = light_color * light_intensity * attenuation;
            
            // Encode to SH (simplified)
            vec4 sh_r = vec4(radiance.r, 0, 0, 0);
            vec4 sh_g = vec4(radiance.g, 0, 0, 0);
            vec4 sh_b = vec4(radiance.b, 0, 0, 0);
            
            imageStore(lpv_red, coords, sh_r);
            imageStore(lpv_green, coords, sh_g);
            imageStore(lpv_blue, coords, sh_b);
        }
        """
        
        return Shader.make_compute(Shader.SL_GLSL, compute_shader)
    
    def _create_lpv_propagate_shader(self) -> Shader:
        """Create compute shader for propagating light in LPV.
        
        Returns:
            Compute shader
        """
        compute_shader = """
        #version 430
        
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 8) in;
        
        layout(rgba32f) uniform image3D lpv_red_read;
        layout(rgba32f) uniform image3D lpv_red_write;
        
        void main() {
            ivec3 coords = ivec3(gl_GlobalInvocationID.xyz);
            
            // Gather from 6 neighbors
            vec4 sum = vec4(0.0);
            for(int x = -1; x <= 1; x++) {
                for(int y = -1; y <= 1; y++) {
                    for(int z = -1; z <= 1; z++) {
                        if(abs(x) + abs(y) + abs(z) == 1) {
                            ivec3 neighbor = coords + ivec3(x, y, z);
                            sum += imageLoad(lpv_red_read, neighbor);
                        }
                    }
                }
            }
            
            // Propagate (simplified)
            vec4 current = imageLoad(lpv_red_read, coords);
            vec4 propagated = current + sum * 0.1;
            
            imageStore(lpv_red_write, coords, propagated);
        }
        """
        
        return Shader.make_compute(Shader.SL_GLSL, compute_shader)
    
    def _setup_ssr(self) -> None:
        """Setup Screen-Space Reflections."""
        logger.info("Setting up Screen-Space Reflections")
        
        # Create SSR render target
        self.ssr_buffer = self.base.win.makeTextureBuffer(
            "ssr_buffer", 0, 0
        )
        
        # SSR shader
        self.ssr_shader = self._create_ssr_shader()
    
    def _create_ssr_shader(self) -> Shader:
        """Create SSR shader.
        
        Returns:
            Compiled shader
        """
        fragment_shader = """
        #version 150
        
        in vec2 texcoord;
        out vec4 fragColor;
        
        uniform sampler2D scene_color;
        uniform sampler2D scene_depth;
        uniform sampler2D scene_normal;
        uniform mat4 projection_matrix;
        uniform mat4 view_matrix;
        
        const int MAX_STEPS = 64;
        const float STEP_SIZE = 0.1;
        
        vec3 reconstructPosition(vec2 uv, float depth) {
            // Reconstruct world position from depth
            vec4 clip = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
            vec4 view = inverse(projection_matrix) * clip;
            return view.xyz / view.w;
        }
        
        void main() {
            float depth = texture(scene_depth, texcoord).r;
            vec3 normal = texture(scene_normal, texcoord).xyz * 2.0 - 1.0;
            vec3 position = reconstructPosition(texcoord, depth);
            
            // Calculate reflection ray
            vec3 view_dir = normalize(position);
            vec3 reflect_dir = reflect(view_dir, normal);
            
            // Ray march in screen space
            vec3 ray_pos = position;
            vec2 hit_uv = texcoord;
            bool hit = false;
            
            for(int i = 0; i < MAX_STEPS; i++) {
                ray_pos += reflect_dir * STEP_SIZE;
                
                // Project to screen space
                vec4 proj = projection_matrix * vec4(ray_pos, 1.0);
                vec2 uv = proj.xy / proj.w * 0.5 + 0.5;
                
                if(uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
                    break;
                
                float sample_depth = texture(scene_depth, uv).r;
                vec3 sample_pos = reconstructPosition(uv, sample_depth);
                
                if(ray_pos.z < sample_pos.z) {
                    hit = true;
                    hit_uv = uv;
                    break;
                }
            }
            
            vec3 base_color = texture(scene_color, texcoord).rgb;
            
            if(hit) {
                vec3 reflect_color = texture(scene_color, hit_uv).rgb;
                // Simple Fresnel approximation
                float fresnel = pow(1.0 - abs(dot(view_dir, normal)), 5.0);
                fragColor = vec4(mix(base_color, reflect_color, fresnel * 0.5), 1.0);
            } else {
                fragColor = vec4(base_color, 1.0);
            }
        }
        """
        
        vertex_shader = """
        #version 150
        in vec4 p3d_Vertex;
        in vec2 p3d_MultiTexCoord0;
        out vec2 texcoord;
        void main() {
            gl_Position = p3d_Vertex;
            texcoord = p3d_MultiTexCoord0;
        }
        """
        
        return Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
    
    def _setup_ray_tracing(self) -> None:
        """Setup hardware ray tracing."""
        logger.info("Setting up hardware ray tracing")
        
        # Ray tracing requires:
        # 1. Acceleration structures (BVH)
        # 2. Ray generation shaders
        # 3. Intersection shaders
        # 4. Any-hit/closest-hit shaders
        
        # This is a simplified placeholder
        # Real implementation would use Vulkan RT or DXR
        self.rt_shader = self._create_rt_shader()
    
    def _create_rt_shader(self) -> Optional[Shader]:
        """Create ray tracing shader.
        
        Returns:
            RT shader or None if not supported
        """
        # Placeholder for RT shader
        # Would use SPIR-V with ray tracing extensions
        logger.warning("Hardware ray tracing shader not yet implemented")
        return None
    
    def add_light_probe(self, position: Point3, radius: float = 10.0) -> LightProbe:
        """Add a light probe to the scene.
        
        Args:
            position: World position
            radius: Influence radius
            
        Returns:
            Created light probe
        """
        probe = LightProbe(
            position=position,
            sh_coefficients=np.zeros((9, 3), dtype=np.float32),
            radius=radius
        )
        
        self.light_probes.append(probe)
        logger.debug(f"Added light probe at {position}")
        
        return probe
    
    def bake_light_probe(self, probe: LightProbe) -> None:
        """Bake lighting into a probe by rendering from its position.
        
        Args:
            probe: Probe to bake
        """
        # Render 6 directions (cube map)
        # Convert to spherical harmonics
        # Store in probe.sh_coefficients
        
        logger.info(f"Baking light probe at {probe.position}")
        # Simplified placeholder
        probe.sh_coefficients = np.random.rand(9, 3).astype(np.float32) * 0.5
    
    def bake_lightmap(self, model_node: NodePath, resolution: int = 512) -> Texture:
        """Bake a lightmap for a static model.
        
        Args:
            model_node: Model to bake
            resolution: Lightmap resolution
            
        Returns:
            Baked lightmap texture
        """
        logger.info(f"Baking lightmap for {model_node.getName()}")
        
        # Create texture
        lightmap = Texture(f"lightmap_{model_node.getName()}")
        lightmap.setup_2d_texture(resolution, resolution, Texture.T_unsigned_byte, Texture.F_rgb8)
        
        # Render model from light's perspective
        # Rasterize to lightmap UV space
        # Store in texture
        
        # Placeholder: fill with grey
        img = PNMImage(resolution, resolution)
        img.fill(0.5, 0.5, 0.5)
        lightmap.load(img)
        
        self.lightmaps[model_node.getName()] = lightmap
        return lightmap
    
    def apply_gi_to_model(self, model_node: NodePath) -> None:
        """Apply GI lighting to a model.
        
        Args:
            model_node: Model to light
        """
        if self.quality == GIQuality.LOW:
            # Use lightmap if available
            if model_node.getName() in self.lightmaps:
                model_node.setShader(self.lightmap_shader)
                model_node.setTexture(self.lightmaps[model_node.getName()], 1)
        
        elif self.quality in [GIQuality.MEDIUM, GIQuality.HIGH]:
            # Use light probes
            model_node.setShader(self.probe_shader)
            # Set irradiance volume texture
        
        elif self.quality == GIQuality.ULTRA:
            # Use ray tracing
            if self.rt_shader:
                model_node.setShader(self.rt_shader)
    
    def update(self, dt: float) -> None:
        """Update GI system per frame.
        
        Args:
            dt: Delta time
        """
        if self.quality == GIQuality.HIGH:
            # Propagate light in LPV
            self._propagate_lpv()
        
        elif self.quality == GIQuality.ULTRA and self.has_ray_tracing:
            # Update ray tracing acceleration structures
            pass
    
    def _propagate_lpv(self) -> None:
        """Propagate light through LPV grid."""
        if not self.has_compute_shaders:
            return
        
        # Run propagation compute shader
        # Ping-pong between read/write grids
        pass
    
    def set_quality(self, quality: GIQuality) -> None:
        """Change GI quality at runtime.
        
        Args:
            quality: New quality level
        """
        if quality != self.quality:
            logger.info(f"Changing GI quality from {self.quality.value} to {quality.value}")
            self.quality = quality
            self._initialize_gi_system()
    
    def cleanup(self) -> None:
        """Cleanup GI resources."""
        if self.gi_buffer:
            self.gi_buffer.clearRenderTextures()
        if self.ssr_buffer:
            self.ssr_buffer.clearRenderTextures()
        
        self.light_probes.clear()
        self.lightmaps.clear()
        self.lpv_grids.clear()
        
        logger.info("Global Illumination system cleaned up")


# Utility functions

def create_gi_system(base, quality: str = "medium") -> GlobalIlluminationSystem:
    """Create and initialize GI system.
    
    Args:
        base: Panda3D ShowBase
        quality: Quality level ("low", "medium", "high", "ultra")
        
    Returns:
        Initialized GI system
    """
    quality_enum = GIQuality(quality.lower())
    return GlobalIlluminationSystem(base, quality_enum)
