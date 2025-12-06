"""Volumetric effects with graceful fallback when heavy deps are missing."""
from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    try:
        from scipy.ndimage import gaussian_filter
    except Exception:  # pragma: no cover - optional dep
        gaussian_filter = None
    from panda3d.core import Shader, Texture, Vec4
    VOLUMETRICS_AVAILABLE = True
except Exception as exc:  # pragma: no cover
    logger.warning("Volumetric system running in stub mode: %s", exc)
    VOLUMETRICS_AVAILABLE = False
    np = None
    gaussian_filter = None
    Shader = Texture = Vec4 = None  # type: ignore


class VolumetricFog:
    """GPU-accelerated volumetric fog with light scattering (stub-safe)."""
    
    def __init__(self, base):
        self.base = base
        self.density = 0.02
        self.color = Vec4(0.7, 0.7, 0.8, 1.0) if VOLUMETRICS_AVAILABLE else None
        self.height_falloff = 0.1
        self.base_height = 0.0
        self.scattering_coefficient = 0.5
        self.extinction_coefficient = 0.3
        self.anisotropy = 0.6
        self.volume_resolution = (128, 128, 64)
        self.volume_texture: Optional[Texture] = None
        self.noise_texture: Optional[Texture] = None
        self.shader: Optional[Shader] = None
        
        if VOLUMETRICS_AVAILABLE:
            self._create_volume_texture()
            self._create_noise_texture()
            self._create_shader()
        else:
            logger.info("VolumetricFog initialized in no-op mode.")
    
    def _create_volume_texture(self) -> None:
        self.volume_texture = Texture("fog_volume")
        self.volume_texture.setup_3d_texture(
            self.volume_resolution[0],
            self.volume_resolution[1],
            self.volume_resolution[2],
            Texture.T_float, Texture.F_rgba32
        )
        self.volume_texture.set_wrap_u(Texture.WM_clamp)
        self.volume_texture.set_wrap_v(Texture.WM_clamp)
        self.volume_texture.set_wrap_w(Texture.WM_clamp)
        self.volume_texture.set_minfilter(Texture.FT_linear)
        self.volume_texture.set_magfilter(Texture.FT_linear)
    
    def _create_noise_texture(self) -> None:
        res = self.volume_resolution
        noise_data = np.random.rand(res[0], res[1], res[2]).astype(np.float32)
        
        if gaussian_filter:
            noise_data = gaussian_filter(noise_data, sigma=2.0)
        
        self.noise_texture = Texture("fog_noise")
        self.noise_texture.setup_3d_texture(res[0], res[1], res[2], Texture.T_float, Texture.F_luminance)
        self.noise_texture.set_ram_image(noise_data.tobytes())
    
    def _create_shader(self) -> None:
        """Create volumetric fog shader."""
        vertex_shader = """
        #version 150
        in vec4 p3d_Vertex;
        in vec2 p3d_MultiTexCoord0;
        uniform mat4 p3d_ModelViewProjectionMatrix;
        out vec2 texcoord;
        out vec3 view_ray;
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            texcoord = p3d_MultiTexCoord0;
            view_ray = p3d_Vertex.xyz;
        }
        """
        fragment_shader = """
        #version 150
        in vec2 texcoord;
        in vec3 view_ray;
        uniform sampler2D depth_texture;
        uniform sampler3D volume_texture;
        uniform sampler3D noise_texture;
        uniform vec4 fog_color;
        uniform float fog_density;
        uniform float height_falloff;
        uniform float base_height;
        uniform float scattering;
        uniform float extinction;
        uniform float anisotropy;
        out vec4 frag_color;
        const int NUM_STEPS = 64;
        float phase_function(float cos_theta, float g) {
            return (1.0 - g * g) / (4.0 * 3.14159265 * pow(1.0 + g * g - 2.0 * g * cos_theta, 1.5));
        }
        void main() {
            float depth = texture(depth_texture, texcoord).r;
            if (depth == 1.0) { discard; }
            float view_len = length(view_ray);
            float step = view_len / float(NUM_STEPS);
            vec3 ray_dir = normalize(view_ray);
            float t = 0.0;
            vec3 accum = vec3(0.0);
            for (int i=0; i<NUM_STEPS; ++i) {
                vec3 sample_pos = ray_dir * t;
                float height = sample_pos.z - base_height;
                float density = fog_density * exp(-height * height_falloff);
                accum += density * step;
                t += step;
            }
            vec3 col = fog_color.rgb * accum * scattering;
            float alpha = 1.0 - exp(-accum * extinction);
            frag_color = vec4(col, clamp(alpha, 0.0, 1.0));
        }
        """
        try:
            self.shader = Shader.make(Shader.SL_GLSL, vertex=vertex_shader, fragment=fragment_shader)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("VolumetricFog shader compilation failed: %s", exc)
            self.shader = None
    
    def apply_to_camera(self, camera_np) -> None:
        """Attach shader to a camera quad or post-pass; safe no-op if unavailable."""
        if not VOLUMETRICS_AVAILABLE or not self.shader:
            return
        try:
            camera_np.set_shader(self.shader)
            camera_np.set_shader_input("fog_color", self.color)
            camera_np.set_shader_input("fog_density", self.density)
        except Exception as exc:  # pragma: no cover
            logger.debug("VolumetricFog apply skipped: %s", exc)


class VolumetricSystem:
    """Container for volumetric effects with feature toggles."""
    def __init__(self, base):
        self.base = base
        self.fog = VolumetricFog(base)
        self.enabled = True
    
    def enable(self) -> None:
        self.enabled = True
    
    def disable(self) -> None:
        self.enabled = False
    
    def update(self, _dt: float = 0.0) -> None:
        """Placeholder for animated volumetrics."""
        return

    def get_state(self) -> dict:
        """Expose volumetric state."""
        return {
            "enabled": self.enabled,
            "fog_density": getattr(self.fog, "density", None),
            "available": VOLUMETRICS_AVAILABLE,
        }
