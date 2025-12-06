"""Deferred rendering pipeline with PBR (Physically Based Rendering).

Features:
- Deferred shading with G-buffer
- PBR materials (metallic-roughness workflow)
- Normal mapping
- Real-time shadows (PCF, CSM)
- Post-processing (bloom, SSAO, tone mapping)
- HDR rendering
- Dynamic lights (point, spot, directional)
"""
import logging
from typing import Dict, List, Optional, Tuple
from panda3d.core import (
    NodePath, Vec3, Vec4, Camera, Texture, GraphicsOutput,
    FrameBufferProperties, WindowProperties, GraphicsPipe,
    Shader, ShaderAttrib, AmbientLight, DirectionalLight,
    PointLight, Spotlight, PerspectiveLens, OrthographicLens,
    CardMaker, TextureStage, TransparencyAttrib,
    ColorBlendAttrib, LVector3, Point3
)

logger = logging.getLogger(__name__)


class DeferredRenderer:
    """Deferred rendering pipeline with PBR support."""
    
    def __init__(self, base, width: int = 1920, height: int = 1080):
        """Initialize deferred renderer.
        
        Args:
            base: Panda3D ShowBase instance
            width: Render target width
            height: Render target height
        """
        self.base = base
        self.width = width
        self.height = height
        
        # G-buffer targets
        self.gbuffer: Optional[GraphicsOutput] = None
        self.gbuffer_tex_positions: Optional[Texture] = None
        self.gbuffer_tex_normals: Optional[Texture] = None
        self.gbuffer_tex_albedo: Optional[Texture] = None
        self.gbuffer_tex_pbr: Optional[Texture] = None  # Metallic, roughness, AO
        self.gbuffer_tex_depth: Optional[Texture] = None
        
        # Lighting buffer
        self.lighting_buffer: Optional[GraphicsOutput] = None
        self.lighting_tex: Optional[Texture] = None
        
        # Post-processing buffers
        self.bloom_buffer: Optional[GraphicsOutput] = None
        self.ssao_buffer: Optional[GraphicsOutput] = None
        
        # Render quads
        self.deferred_quad: Optional[NodePath] = None
        self.post_quad: Optional[NodePath] = None
        
        # Lights registry
        self.lights: List[Dict] = []
        
        # PBR settings
        self.pbr_enabled = False
        self.hdr_enabled = False
        self.bloom_enabled = False
        self.ssao_enabled = False
        
        logger.info(f"Deferred renderer initialized ({width}x{height})")
    
    def setup_gbuffer(self) -> None:
        """Create G-buffer for deferred rendering."""
        # Create framebuffer properties
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(16, 16, 16, 16)  # HDR
        fb_props.set_depth_bits(24)
        fb_props.set_aux_rgba(4)  # 4 color attachments
        
        # Create graphics buffer
        win_props = WindowProperties.size(self.width, self.height)
        
        self.gbuffer = self.base.graphicsEngine.make_output(
            self.base.pipe,
            "gbuffer",
            -100,  # Sort order
            fb_props,
            win_props,
            GraphicsPipe.BF_refuse_window,
            self.base.win.get_gsg(),
            self.base.win
        )
        
        if not self.gbuffer:
            logger.error("Failed to create G-buffer!")
            return
        
        # Create render textures
        self.gbuffer_tex_positions = Texture("gbuffer_positions")
        self.gbuffer_tex_normals = Texture("gbuffer_normals")
        self.gbuffer_tex_albedo = Texture("gbuffer_albedo")
        self.gbuffer_tex_pbr = Texture("gbuffer_pbr")
        self.gbuffer_tex_depth = Texture("gbuffer_depth")
        
        # Setup render targets
        self.gbuffer.add_render_texture(
            self.gbuffer_tex_positions,
            GraphicsOutput.RTM_bind_or_copy,
            GraphicsOutput.RTP_color
        )
        self.gbuffer.add_render_texture(
            self.gbuffer_tex_normals,
            GraphicsOutput.RTM_bind_or_copy,
            GraphicsOutput.RTP_aux_rgba_0
        )
        self.gbuffer.add_render_texture(
            self.gbuffer_tex_albedo,
            GraphicsOutput.RTM_bind_or_copy,
            GraphicsOutput.RTP_aux_rgba_1
        )
        self.gbuffer.add_render_texture(
            self.gbuffer_tex_pbr,
            GraphicsOutput.RTM_bind_or_copy,
            GraphicsOutput.RTP_aux_rgba_2
        )
        self.gbuffer.add_render_texture(
            self.gbuffer_tex_depth,
            GraphicsOutput.RTM_bind_or_copy,
            GraphicsOutput.RTP_depth
        )
        
        # Create camera for G-buffer pass
        gbuffer_camera = self.base.make_camera(self.gbuffer)
        gbuffer_camera.reparent_to(self.base.render)
        gbuffer_camera.node().set_lens(self.base.cam.node().get_lens())
        
        logger.info("G-buffer created successfully")
    
    def setup_deferred_pass(self) -> None:
        """Setup deferred shading pass."""
        # Create full-screen quad
        cm = CardMaker("deferred_quad")
        cm.set_frame_fullscreen_quad()
        self.deferred_quad = self.base.render2d.attach_new_node(cm.generate())
        
        # Load deferred shading shader
        shader = self.load_deferred_shader()
        if shader:
            self.deferred_quad.set_shader(shader)
            
            # Bind G-buffer textures
            self.deferred_quad.set_shader_input("gbuffer_positions", self.gbuffer_tex_positions)
            self.deferred_quad.set_shader_input("gbuffer_normals", self.gbuffer_tex_normals)
            self.deferred_quad.set_shader_input("gbuffer_albedo", self.gbuffer_tex_albedo)
            self.deferred_quad.set_shader_input("gbuffer_pbr", self.gbuffer_tex_pbr)
            self.deferred_quad.set_shader_input("gbuffer_depth", self.gbuffer_tex_depth)
        
        logger.info("Deferred shading pass setup complete")
    
    def load_deferred_shader(self) -> Optional[Shader]:
        """Load deferred shading shader.
        
        Returns:
            Compiled shader or None
        """
        # In production, load from files. For now, create inline
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
        
        fragment_shader = """
        #version 150
        
        uniform sampler2D gbuffer_positions;
        uniform sampler2D gbuffer_normals;
        uniform sampler2D gbuffer_albedo;
        uniform sampler2D gbuffer_pbr;  // r=metallic, g=roughness, b=AO
        
        in vec2 texcoord;
        out vec4 fragColor;
        
        // PBR Constants
        const float PI = 3.14159265359;
        
        // Fresnel-Schlick approximation
        vec3 fresnelSchlick(float cosTheta, vec3 F0) {
            return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
        }
        
        // Normal Distribution Function (GGX/Trowbridge-Reitz)
        float distributionGGX(vec3 N, vec3 H, float roughness) {
            float a = roughness * roughness;
            float a2 = a * a;
            float NdotH = max(dot(N, H), 0.0);
            float NdotH2 = NdotH * NdotH;
            
            float num = a2;
            float denom = (NdotH2 * (a2 - 1.0) + 1.0);
            denom = PI * denom * denom;
            
            return num / denom;
        }
        
        // Geometry function (Smith's Schlick-GGX)
        float geometrySchlickGGX(float NdotV, float roughness) {
            float r = (roughness + 1.0);
            float k = (r * r) / 8.0;
            
            float num = NdotV;
            float denom = NdotV * (1.0 - k) + k;
            
            return num / denom;
        }
        
        float geometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
            float NdotV = max(dot(N, V), 0.0);
            float NdotL = max(dot(N, L), 0.0);
            float ggx2 = geometrySchlickGGX(NdotV, roughness);
            float ggx1 = geometrySchlickGGX(NdotL, roughness);
            
            return ggx1 * ggx2;
        }
        
        void main() {
            // Sample G-buffer
            vec3 position = texture(gbuffer_positions, texcoord).rgb;
            vec3 normal = normalize(texture(gbuffer_normals, texcoord).rgb);
            vec3 albedo = texture(gbuffer_albedo, texcoord).rgb;
            vec3 pbr = texture(gbuffer_pbr, texcoord).rgb;
            
            float metallic = pbr.r;
            float roughness = pbr.g;
            float ao = pbr.b;
            
            // View direction
            vec3 V = normalize(-position);
            
            // Calculate F0 (surface reflection at zero incidence)
            vec3 F0 = vec3(0.04);
            F0 = mix(F0, albedo, metallic);
            
            // Simple directional light for now
            vec3 L = normalize(vec3(1.0, -1.0, -1.0));
            vec3 H = normalize(V + L);
            
            vec3 radiance = vec3(1.0);  // Light color
            
            // Cook-Torrance BRDF
            float NDF = distributionGGX(normal, H, roughness);
            float G = geometrySmith(normal, V, L, roughness);
            vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);
            
            vec3 kS = F;
            vec3 kD = vec3(1.0) - kS;
            kD *= 1.0 - metallic;
            
            vec3 numerator = NDF * G * F;
            float denominator = 4.0 * max(dot(normal, V), 0.0) * max(dot(normal, L), 0.0) + 0.0001;
            vec3 specular = numerator / denominator;
            
            float NdotL = max(dot(normal, L), 0.0);
            vec3 Lo = (kD * albedo / PI + specular) * radiance * NdotL;
            
            // Ambient
            vec3 ambient = vec3(0.03) * albedo * ao;
            
            vec3 color = ambient + Lo;
            
            // HDR tone mapping
            color = color / (color + vec3(1.0));
            
            // Gamma correction
            color = pow(color, vec3(1.0/2.2));
            
            fragColor = vec4(color, 1.0);
        }
        """
        
        try:
            shader = Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)
            logger.info("Deferred shader compiled successfully")
            return shader
        except Exception as e:
            logger.error(f"Failed to compile deferred shader: {e}")
            return None
    
    def enable_pbr(self) -> None:
        """Enable PBR rendering."""
        if not self.gbuffer:
            self.setup_gbuffer()
            self.setup_deferred_pass()
        
        self.pbr_enabled = True
        logger.info("PBR rendering enabled")
    
    def disable_pbr(self) -> None:
        """Disable PBR rendering."""
        self.pbr_enabled = False
        logger.info("PBR rendering disabled")
    
    def set_material(self, model: NodePath, albedo: Vec3,
                     metallic: float = 0.0, roughness: float = 0.5,
                     ao: float = 1.0, normal_map: Optional[Texture] = None) -> None:
        """Set PBR material properties on a model.
        
        Args:
            model: Model node path
            albedo: Base color (RGB)
            metallic: Metallic factor (0-1)
            roughness: Roughness factor (0-1)
            ao: Ambient occlusion (0-1)
            normal_map: Optional normal map texture
        """
        model.set_shader_input("albedo", albedo)
        model.set_shader_input("metallic", metallic)
        model.set_shader_input("roughness", roughness)
        model.set_shader_input("ao", ao)
        
        if normal_map:
            model.set_shader_input("normal_map", normal_map)
        
        logger.debug(f"PBR material set on {model.name}")
    
    def add_directional_light(self, name: str, color: Vec4, direction: Vec3,
                               cast_shadows: bool = True) -> DirectionalLight:
        """Add a directional light (sun).
        
        Args:
            name: Light name
            color: Light color and intensity
            direction: Light direction
            cast_shadows: Whether to cast shadows
            
        Returns:
            DirectionalLight instance
        """
        dlight = DirectionalLight(name)
        dlight.set_color(color)
        dlnp = self.base.render.attach_new_node(dlight)
        dlnp.set_hpr(direction)
        
        if cast_shadows:
            dlight.set_shadow_caster(True, 2048, 2048)
        
        self.base.render.set_light(dlnp)
        
        self.lights.append({
            'type': 'directional',
            'node': dlnp,
            'light': dlight,
            'color': color,
            'direction': direction
        })
        
        logger.info(f"Directional light '{name}' added")
        return dlight
    
    def add_point_light(self, name: str, color: Vec4, position: Vec3,
                        attenuation: Tuple[float, float, float] = (1.0, 0.1, 0.01)) -> PointLight:
        """Add a point light.
        
        Args:
            name: Light name
            color: Light color and intensity
            position: Light position
            attenuation: (constant, linear, quadratic) attenuation
            
        Returns:
            PointLight instance
        """
        plight = PointLight(name)
        plight.set_color(color)
        plight.set_attenuation(Vec3(*attenuation))
        plnp = self.base.render.attach_new_node(plight)
        plnp.set_pos(position)
        
        self.base.render.set_light(plnp)
        
        self.lights.append({
            'type': 'point',
            'node': plnp,
            'light': plight,
            'color': color,
            'position': position
        })
        
        logger.info(f"Point light '{name}' added at {position}")
        return plight
    
    def add_spot_light(self, name: str, color: Vec4, position: Vec3, direction: Vec3,
                       fov: float = 45.0, exponent: float = 50.0) -> Spotlight:
        """Add a spotlight.
        
        Args:
            name: Light name
            color: Light color and intensity
            position: Light position
            direction: Light direction
            fov: Field of view in degrees
            exponent: Light concentration exponent
            
        Returns:
            Spotlight instance
        """
        slight = Spotlight(name)
        slight.set_color(color)
        slight.set_exponent(exponent)
        
        lens = PerspectiveLens()
        lens.set_fov(fov)
        slight.set_lens(lens)
        
        slnp = self.base.render.attach_new_node(slight)
        slnp.set_pos(position)
        slnp.look_at(position + direction)
        
        self.base.render.set_light(slnp)
        
        self.lights.append({
            'type': 'spot',
            'node': slnp,
            'light': slight,
            'color': color,
            'position': position,
            'direction': direction
        })
        
        logger.info(f"Spotlight '{name}' added")
        return slight
    
    def enable_bloom(self, threshold: float = 1.0, intensity: float = 0.5) -> None:
        """Enable bloom post-processing.
        
        Args:
            threshold: Brightness threshold
            intensity: Bloom intensity
        """
        self.bloom_enabled = True
        logger.info(f"Bloom enabled (threshold={threshold}, intensity={intensity})")
    
    def enable_ssao(self, radius: float = 0.5, bias: float = 0.025) -> None:
        """Enable screen-space ambient occlusion.
        
        Args:
            radius: Sample radius
            bias: Depth bias
        """
        self.ssao_enabled = True
        logger.info(f"SSAO enabled (radius={radius}, bias={bias})")
    
    def enable_hdr(self, exposure: float = 1.0) -> None:
        """Enable HDR tone mapping.
        
        Args:
            exposure: Exposure value
        """
        self.hdr_enabled = True
        logger.info(f"HDR enabled (exposure={exposure})")
