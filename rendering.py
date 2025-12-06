"""Advanced rendering features for AAA-quality graphics."""
import pygame
import pygame_gui
from typing import Tuple, Optional, List
import math


class ParticleSystem:
    """Particle system for visual effects."""
    
    def __init__(self, x: int, y: int, max_particles: int = 100):
        """Initialize particle system.
        
        Args:
            x: X position of emitter
            y: Y position of emitter
            max_particles: Maximum number of particles
        """
        self.x = x
        self.y = y
        self.particles: List[Particle] = []
        self.max_particles = max_particles
        
    def emit(self, count: int = 1, color: Tuple[int, int, int] = (255, 255, 255),
             speed_range: Tuple[float, float] = (1, 5),
             lifetime: int = 60) -> None:
        """Emit particles.
        
        Args:
            count: Number of particles to emit
            color: RGB color tuple
            speed_range: Min and max speed
            lifetime: Particle lifetime in frames
        """
        import random
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(*speed_range)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                particle = Particle(self.x, self.y, vx, vy, color, lifetime)
                self.particles.append(particle)
    
    def update(self) -> None:
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update()]
    
    def render(self, screen: pygame.Surface) -> None:
        """Render all particles.
        
        Args:
            screen: Surface to render to
        """
        for particle in self.particles:
            particle.render(screen)


class Particle:
    """Individual particle."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: Tuple[int, int, int], lifetime: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 3
        
    def update(self) -> bool:
        """Update particle position and lifetime.
        
        Returns:
            True if particle is still alive
        """
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the particle."""
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color, alpha)
        
        # Create a surface for the particle with per-pixel alpha
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color_with_alpha, 
                         (self.size, self.size), self.size)
        screen.blit(particle_surface, (int(self.x - self.size), int(self.y - self.size)))


class Camera:
    """2D camera for scrolling and zoom."""
    
    def __init__(self, width: int, height: int):
        """Initialize camera.
        
        Args:
            width: Viewport width
            height: Viewport height
        """
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.zoom = 1.0
        
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Apply camera transform to a rectangle.
        
        Args:
            rect: Original rectangle
            
        Returns:
            Transformed rectangle
        """
        return pygame.Rect(
            int((rect.x - self.x) * self.zoom),
            int((rect.y - self.y) * self.zoom),
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )
    
    def center_on(self, x: int, y: int) -> None:
        """Center camera on a position.
        
        Args:
            x: X position to center on
            y: Y position to center on
        """
        self.x = x - self.width // 2
        self.y = y - self.height // 2
        
    def set_zoom(self, zoom: float) -> None:
        """Set camera zoom level.
        
        Args:
            zoom: Zoom level (1.0 = normal, 2.0 = 2x zoom)
        """
        self.zoom = max(0.1, min(zoom, 5.0))


class LightingSystem:
    """Simple lighting system for atmospheric effects."""
    
    def __init__(self, width: int, height: int):
        """Initialize lighting system.
        
        Args:
            width: Screen width
            height: Screen height
        """
        self.width = width
        self.height = height
        self.ambient_light = 0.3  # 0.0 = dark, 1.0 = fully lit
        self.lights: List[Tuple[int, int, int, Tuple[int, int, int]]] = []
        
    def add_light(self, x: int, y: int, radius: int, 
                  color: Tuple[int, int, int] = (255, 255, 200)) -> None:
        """Add a point light.
        
        Args:
            x: Light X position
            y: Light Y position
            radius: Light radius
            color: Light color
        """
        self.lights.append((x, y, radius, color))
    
    def clear_lights(self) -> None:
        """Remove all lights."""
        self.lights.clear()
    
    def render(self, screen: pygame.Surface) -> pygame.Surface:
        """Render lighting overlay.
        
        Args:
            screen: Screen to apply lighting to
            
        Returns:
            Surface with lighting applied
        """
        # Create darkness overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        
        # Draw light circles
        for x, y, radius, color in self.lights:
            light_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                alpha = int(255 * (1 - r / radius) * (1 - self.ambient_light))
                pygame.draw.circle(light_surface, (*color, alpha), 
                                 (radius, radius), r)
            overlay.blit(light_surface, (x - radius, y - radius), 
                        special_flags=pygame.BLEND_RGBA_SUB)
        
        # Set overall darkness based on ambient light
        overlay.set_alpha(int(255 * (1 - self.ambient_light)))
        return overlay


class PostProcessing:
    """Post-processing effects for enhanced visuals."""
    
    @staticmethod
    def apply_bloom(surface: pygame.Surface, intensity: float = 0.5) -> pygame.Surface:
        """Apply bloom effect.
        
        Args:
            surface: Surface to apply bloom to
            intensity: Bloom intensity (0.0 to 1.0)
            
        Returns:
            Surface with bloom applied
        """
        # Create a blurred copy
        blurred = pygame.transform.smoothscale(surface, 
                                               (surface.get_width() // 4, 
                                                surface.get_height() // 4))
        blurred = pygame.transform.smoothscale(blurred, surface.get_size())
        
        # Blend with original
        result = surface.copy()
        blurred.set_alpha(int(128 * intensity))
        result.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return result
    
    @staticmethod
    def apply_vignette(surface: pygame.Surface, strength: float = 0.5) -> pygame.Surface:
        """Apply vignette effect.
        
        Args:
            surface: Surface to apply vignette to
            strength: Vignette strength (0.0 to 1.0)
            
        Returns:
            Surface with vignette applied
        """
        width, height = surface.get_size()
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(0, height, 4):  # Step by 4 for performance
            for x in range(0, width, 4):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                alpha = int(255 * (dist / max_dist) * strength)
                pygame.draw.rect(vignette, (0, 0, 0, alpha), (x, y, 4, 4))
        
        result = surface.copy()
        result.blit(vignette, (0, 0))
        return result
    
    @staticmethod
    def apply_chromatic_aberration(surface: pygame.Surface, 
                                   offset: int = 2) -> pygame.Surface:
        """Apply chromatic aberration effect.
        
        Args:
            surface: Surface to apply effect to
            offset: Pixel offset for color channels
            
        Returns:
            Surface with chromatic aberration
        """
        result = surface.copy()
        
        # Split into RGB channels
        r_channel = surface.copy()
        g_channel = surface.copy()
        b_channel = surface.copy()
        
        # Offset channels
        result.blit(r_channel, (-offset, 0), special_flags=pygame.BLEND_RGBA_MULT)
        result.blit(g_channel, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        result.blit(b_channel, (offset, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        return result
