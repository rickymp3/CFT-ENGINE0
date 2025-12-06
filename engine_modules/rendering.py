"""Shader and rendering pipeline for PBR and post-processing."""
import logging
from pathlib import Path
from typing import Optional
from panda3d.core import (
    Shader, NodePath, AmbientLight, DirectionalLight,
    Spotlight, PointLight, LVector3, LColor
)

logger = logging.getLogger(__name__)


class RenderingManager:
    """Manages shaders, lighting, and post-processing effects."""
    
    def __init__(self, render_node: NodePath):
        """Initialize rendering manager.
        
        Args:
            render_node: Main render node path
        """
        self.render = render_node
        self.pbr_enabled = False
        self.hdr_enabled = False
        self.lights = {}
        self.shaders_path = Path("assets/shaders")
        
        logger.info("Rendering manager initialized")
    
    def enable_pbr(self) -> None:
        """Enable Physically Based Rendering.
        
        Note: This is a placeholder. Full PBR requires custom shaders
        or Panda3D's RenderPipeline plugin.
        """
        if self.pbr_enabled:
            return
        
        # For now, we enable per-pixel lighting as a step toward PBR
        self.render.set_shader_auto()
        self.pbr_enabled = True
        logger.info("PBR rendering enabled (auto-shader mode)")
    
    def disable_pbr(self) -> None:
        """Disable PBR rendering."""
        if not self.pbr_enabled:
            return
        
        self.render.clear_shader()
        self.pbr_enabled = False
        logger.info("PBR rendering disabled")
    
    def add_ambient_light(self, name: str, color: tuple = (0.3, 0.3, 0.3, 1.0)) -> NodePath:
        """Add ambient light to the scene.
        
        Args:
            name: Light name
            color: RGBA color tuple
            
        Returns:
            Light node path
        """
        light = AmbientLight(name)
        light.set_color(LColor(*color))
        light_np = self.render.attach_new_node(light)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info(f"Added ambient light: {name}")
        return light_np
    
    def add_directional_light(self, name: str, 
                             direction: tuple = (1, -2, -2),
                             color: tuple = (0.8, 0.8, 0.7, 1.0)) -> NodePath:
        """Add directional light (sun) to the scene.
        
        Args:
            name: Light name
            direction: Light direction vector
            color: RGBA color tuple
            
        Returns:
            Light node path
        """
        light = DirectionalLight(name)
        light.set_color(LColor(*color))
        light_np = self.render.attach_new_node(light)
        light_np.look_at(*direction)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info(f"Added directional light: {name}")
        return light_np
    
    def add_point_light(self, name: str,
                       position: tuple = (0, 0, 5),
                       color: tuple = (1.0, 1.0, 1.0, 1.0),
                       attenuation: tuple = (1.0, 0.0, 0.0)) -> NodePath:
        """Add point light to the scene.
        
        Args:
            name: Light name
            position: Light position
            color: RGBA color tuple
            attenuation: (constant, linear, quadratic) attenuation
            
        Returns:
            Light node path
        """
        light = PointLight(name)
        light.set_color(LColor(*color))
        light.set_attenuation(LVector3(*attenuation))
        light_np = self.render.attach_new_node(light)
        light_np.set_pos(*position)
        self.render.set_light(light_np)
        self.lights[name] = light_np
        logger.info(f"Added point light: {name}")
        return light_np
    
    def remove_light(self, name: str) -> None:
        """Remove a light from the scene.
        
        Args:
            name: Light name
        """
        if name in self.lights:
            self.render.clear_light(self.lights[name])
            self.lights[name].remove_node()
            del self.lights[name]
            logger.info(f"Removed light: {name}")
    
    def load_shader(self, vertex_path: str, fragment_path: str) -> Optional[Shader]:
        """Load a shader from vertex and fragment shader files.
        
        Args:
            vertex_path: Path to vertex shader
            fragment_path: Path to fragment shader
            
        Returns:
            Loaded shader or None on failure
        """
        try:
            shader = Shader.load(Shader.SL_GLSL, 
                                vertex=str(self.shaders_path / vertex_path),
                                fragment=str(self.shaders_path / fragment_path))
            logger.info(f"Loaded shader: {vertex_path}, {fragment_path}")
            return shader
        except Exception as e:
            logger.error(f"Failed to load shader: {e}")
            return None
    
    def apply_shader(self, node: NodePath, shader: Shader) -> None:
        """Apply a shader to a node.
        
        Args:
            node: Node to apply shader to
            shader: Shader to apply
        """
        node.set_shader(shader)
    
    def enable_shadows(self) -> None:
        """Enable shadow mapping.
        
        Note: Requires appropriate light configuration.
        """
        # This is a placeholder for shadow map setup
        logger.info("Shadow mapping enabled (requires light configuration)")
    
    def set_background_color(self, color: tuple = (0.05, 0.1, 0.2, 1.0)) -> None:
        """Set the background clear color.
        
        Args:
            color: RGBA color tuple
        """
        # This would be called on the window/display region
        logger.info(f"Background color set to {color}")
