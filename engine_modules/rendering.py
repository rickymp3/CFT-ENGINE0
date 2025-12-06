"""Rendering helpers with PBR/HDR/post toggles and lighting utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any

from panda3d.core import (
    Shader,
    NodePath,
    AmbientLight,
    DirectionalLight,
    Spotlight,
    PointLight,
    LVector3,
    LColor,
)

logger = logging.getLogger(__name__)


class RenderQuality(Enum):
    """Feature presets for quick setup."""
    LOW = "low"          # Forward, minimal post
    MEDIUM = "medium"    # Auto-shader PBR-ish
    HIGH = "high"        # Add HDR + post toggles
    ULTRA = "ultra"      # Enable everything exposed


@dataclass
class PostProcessSettings:
    """Soft toggles for a lightweight post stack."""
    bloom: bool = False
    bloom_strength: float = 0.3
    vignette: bool = False
    chromatic_aberration: bool = False
    sharpen: bool = False
    color_grade_lut: str | None = None
    film_grain: bool = False


class RenderingManager:
    """Manages shaders, lighting, and post-processing effects with safe fallbacks."""
    
    def __init__(self, render_node: NodePath, quality: RenderQuality | str = RenderQuality.MEDIUM):
        """Initialize rendering manager.
        
        Args:
            render_node: Main render node path
            quality: RenderQuality preset or string
        """
        self.render = render_node
        self.pbr_enabled = False
        self.hdr_enabled = False
        self.bloom_enabled = False
        self.tonemap_mode = "aces"
        self.exposure = 1.0
        self.shadow_resolution = 1024
        self.quality = quality if isinstance(quality, RenderQuality) else RenderQuality(quality.lower())
        self.lights: Dict[str, NodePath] = {}
        self.shaders_path = Path("assets/shaders")
        self.post = PostProcessSettings()
        
        logger.info("Rendering manager initialized (quality=%s)", self.quality.value)
        self._apply_quality_defaults()
    
    def _apply_quality_defaults(self) -> None:
        """Lightweight quality configuration that is safe in headless mode."""
        if self.quality in (RenderQuality.MEDIUM, RenderQuality.HIGH, RenderQuality.ULTRA):
            self.enable_pbr()
        if self.quality in (RenderQuality.HIGH, RenderQuality.ULTRA):
            self.enable_hdr()
            self.enable_bloom(strength=0.35 if self.quality == RenderQuality.HIGH else 0.5)
    
    # -------- Rendering toggles --------
    def enable_pbr(self) -> None:
        """Enable Physically Based Rendering (auto-shader fallback)."""
        if self.pbr_enabled:
            return
        try:
            self.render.set_shader_auto()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("PBR auto-shader unavailable: %s", exc)
        self.pbr_enabled = True
        logger.info("PBR rendering enabled (auto-shader mode)")
    
    def disable_pbr(self) -> None:
        """Disable PBR rendering."""
        if not self.pbr_enabled:
            return
        try:
            self.render.clear_shader()
        except Exception:
            pass
        self.pbr_enabled = False
        logger.info("PBR rendering disabled")
    
    def enable_hdr(self, exposure: float = 1.0) -> None:
        """Toggle HDR pipeline flags (conceptual placeholder)."""
        self.hdr_enabled = True
        self.exposure = exposure
        logger.info("HDR enabled (exposure=%.2f)", exposure)

    def disable_hdr(self) -> None:
        """Disable HDR flag."""
        self.hdr_enabled = False
        logger.info("HDR disabled")

    def enable_bloom(self, strength: float = 0.3) -> None:
        """Enable bloom placeholder; stores intensity for downstream use."""
        self.bloom_enabled = True
        self.bloom_strength = strength
        self.post.bloom = True
        self.post.bloom_strength = strength
        logger.info("Bloom enabled (strength=%.2f)", strength)

    def disable_bloom(self) -> None:
        self.bloom_enabled = False
        self.post.bloom = False
        logger.info("Bloom disabled")

    def set_tonemap(self, mode: str = "aces") -> None:
        """Set tonemapping mode hint."""
        self.tonemap_mode = mode
        logger.info("Tonemap set to %s", mode)

    def set_exposure(self, exposure: float) -> None:
        """Adjust exposure when HDR is on."""
        self.exposure = exposure
        logger.info("Exposure set to %.2f", exposure)

    def configure_post(self, **kwargs: Any) -> None:
        """Batch update post-process settings."""
        for key, value in kwargs.items():
            if hasattr(self.post, key):
                setattr(self.post, key, value)
        logger.info("Post-process updated: %s", {k: getattr(self.post, k) for k in kwargs if hasattr(self.post, k)})

    def set_color_grading_lut(self, lut_path: str | None) -> None:
        """Assign a LUT path for downstream post-processing."""
        self.post.color_grade_lut = lut_path
        logger.info("Color grading LUT set to %s", lut_path)

    # -------- Lighting helpers --------
    def add_ambient_light(self, name: str, color: tuple = (0.3, 0.3, 0.3, 1.0)) -> NodePath:
        """Add ambient light to the scene."""
        light = AmbientLight(name)
        light.set_color(LColor(*color))
        light_np = self.render.attach_new_node(light)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info("Added ambient light: %s", name)
        return light_np
    
    def add_directional_light(self, name: str, 
                             direction: tuple = (1, -2, -2),
                             color: tuple = (0.8, 0.8, 0.7, 1.0)) -> NodePath:
        """Add directional light (sun) to the scene."""
        light = DirectionalLight(name)
        light.set_color(LColor(*color))
        light_np = self.render.attach_new_node(light)
        try:
            light_np.look_at(*direction)
        except Exception:
            pass
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info("Added directional light: %s", name)
        return light_np
    
    def add_point_light(self, name: str,
                       position: tuple = (0, 0, 5),
                       color: tuple = (1.0, 1.0, 1.0, 1.0),
                       attenuation: tuple = (1.0, 0.0, 0.0),
                       shadows: bool = False) -> NodePath:
        """Add point light to the scene."""
        light = PointLight(name)
        light.set_color(LColor(*color))
        light.set_attenuation(LVector3(*attenuation))
        if shadows and hasattr(light, "setShadowCaster"):
            light.setShadowCaster(True, self.shadow_resolution, self.shadow_resolution)
        light_np = self.render.attach_new_node(light)
        light_np.set_pos(*position)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info("Added point light: %s", name)
        return light_np
    
    def add_spot_light(self, name: str, position: tuple = (0, 0, 0),
                      direction: tuple = (0, 0, -1),
                      fov: float = 40.0,
                      color: tuple = (1, 1, 1, 1),
                      shadows: bool = False) -> NodePath:
        """Add spotlight."""
        light = Spotlight(name)
        light.set_color(LColor(*color))
        lens = light.get_lens()
        lens.set_fov(fov)
        
        if shadows and hasattr(light, "setShadowCaster"):
            light.setShadowCaster(True, self.shadow_resolution * 2, self.shadow_resolution * 2)
        
        light_np = self.render.attach_new_node(light)
        light_np.set_pos(*position)
        light_np.look_at(*direction)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info("Added spotlight: %s", name)
        return light_np
    
    def remove_light(self, name: str) -> None:
        """Remove a light from the scene."""
        light_np = self.lights.pop(name, None)
        if light_np:
            self.render.clear_light(light_np)
            light_np.remove_node()
            logger.info("Removed light: %s", name)
    
    def set_shadow_quality(self, resolution: int = 1024) -> None:
        """Hint for shadow map resolution; stored for downstream consumers."""
        self.shadow_resolution = resolution
        logger.info("Shadow quality set to %d", resolution)
    
    # -------- Shader utilities --------
    def load_shader(self, vertex_path: str, fragment_path: str) -> Shader | None:
        """Load a shader from vertex and fragment shader files."""
        try:
            shader = Shader.load(
                Shader.SL_GLSL,
                vertex=str(self.shaders_path / vertex_path),
                fragment=str(self.shaders_path / fragment_path),
            )
            logger.info("Loaded shader: %s, %s", vertex_path, fragment_path)
            return shader
        except Exception as e:
            logger.error("Failed to load shader: %s", e)
            return None
    
    def apply_shader(self, node: NodePath, shader: Shader) -> None:
        """Apply a shader to a node."""
        node.set_shader(shader)
    
    def set_background_color(self, color: tuple = (0.05, 0.1, 0.2, 1.0)) -> None:
        """Set the background clear color."""
        try:
            self.render.set_background_color(*color)
        except Exception:
            logger.info("Background color set to %s (render node has no background setter)", color)
    
    # -------- Introspection --------
    def get_state(self) -> Dict[str, Any]:
        """Expose current render state for debugging/telemetry."""
        return {
            "pbr": self.pbr_enabled,
            "hdr": self.hdr_enabled,
            "bloom": self.bloom_enabled,
            "exposure": self.exposure,
            "tonemap": self.tonemap_mode,
            "quality": self.quality.value,
            "lights": list(self.lights.keys()),
            "shadow_resolution": self.shadow_resolution,
            "post": vars(self.post),
        }
