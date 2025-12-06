"""Asset management system for loading and managing game resources."""
import pygame
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import os


class AssetManager:
    """Manages loading and caching of game assets."""
    
    def __init__(self, base_path: str = "assets"):
        """Initialize the asset manager.
        
        Args:
            base_path: Root directory for assets
        """
        self.base_path = Path(base_path)
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.music: Optional[str] = None
        
        # Ensure asset directories exist
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Create asset directories if they don't exist."""
        for subdir in ['images', 'sounds', 'fonts', 'music']:
            path = self.base_path / subdir
            path.mkdir(parents=True, exist_ok=True)
    
    def load_image(self, filename: str, scale: Optional[tuple] = None, 
                   alpha: bool = True) -> pygame.Surface:
        """Load an image file.
        
        Args:
            filename: Image filename in assets/images/
            scale: Optional (width, height) to scale image
            alpha: Whether to convert with alpha channel
            
        Returns:
            Pygame Surface containing the image
        """
        key = f"{filename}_{scale}_{alpha}"
        
        if key in self.images:
            return self.images[key]
            
        path = self.base_path / "images" / filename
        
        if not path.exists():
            # Create placeholder image if file doesn't exist
            print(f"Warning: Image not found: {path}, creating placeholder")
            surface = self._create_placeholder(scale or (64, 64))
        else:
            if alpha:
                surface = pygame.image.load(str(path)).convert_alpha()
            else:
                surface = pygame.image.load(str(path)).convert()
                
            if scale:
                surface = pygame.transform.scale(surface, scale)
        
        self.images[key] = surface
        return surface
    
    def _create_placeholder(self, size: tuple) -> pygame.Surface:
        """Create a placeholder image.
        
        Args:
            size: (width, height) of placeholder
            
        Returns:
            Pygame Surface with placeholder pattern
        """
        surface = pygame.Surface(size)
        surface.fill((200, 200, 200))
        pygame.draw.line(surface, (255, 0, 255), (0, 0), size, 2)
        pygame.draw.line(surface, (255, 0, 255), (0, size[1]), (size[0], 0), 2)
        return surface
    
    def load_sound(self, filename: str, volume: float = 1.0) -> pygame.mixer.Sound:
        """Load a sound effect.
        
        Args:
            filename: Sound filename in assets/sounds/
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            Pygame Sound object
        """
        if filename in self.sounds:
            return self.sounds[filename]
            
        path = self.base_path / "sounds" / filename
        
        if not path.exists():
            print(f"Warning: Sound not found: {path}")
            # Return a silent sound placeholder
            sound = pygame.mixer.Sound(buffer=bytes(100))
        else:
            sound = pygame.mixer.Sound(str(path))
            
        sound.set_volume(volume)
        self.sounds[filename] = sound
        return sound
    
    def load_font(self, filename: Optional[str], size: int) -> pygame.font.Font:
        """Load a font.
        
        Args:
            filename: Font filename in assets/fonts/ or None for default
            size: Font size
            
        Returns:
            Pygame Font object
        """
        key = f"{filename}_{size}"
        
        if key in self.fonts:
            return self.fonts[key]
            
        if filename is None:
            font = pygame.font.Font(None, size)
        else:
            path = self.base_path / "fonts" / filename
            if path.exists():
                font = pygame.font.Font(str(path), size)
            else:
                print(f"Warning: Font not found: {path}, using default")
                font = pygame.font.Font(None, size)
        
        self.fonts[key] = font
        return font
    
    def play_music(self, filename: str, loops: int = -1, volume: float = 0.7) -> None:
        """Play background music.
        
        Args:
            filename: Music filename in assets/music/
            loops: Number of times to loop (-1 for infinite)
            volume: Volume level (0.0 to 1.0)
        """
        path = self.base_path / "music" / filename
        
        if path.exists():
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
            self.music = filename
        else:
            print(f"Warning: Music not found: {path}")
    
    def stop_music(self) -> None:
        """Stop background music."""
        pygame.mixer.music.stop()
        
    def generate_procedural_texture(self, width: int, height: int, 
                                    pattern: str = "checkerboard") -> pygame.Surface:
        """Generate a procedural texture for AAA-quality graphics.
        
        Args:
            width: Texture width
            height: Texture height
            pattern: Pattern type ('checkerboard', 'gradient', 'noise')
            
        Returns:
            Pygame Surface with generated texture
        """
        surface = pygame.Surface((width, height))
        
        if pattern == "checkerboard":
            tile_size = 32
            for y in range(0, height, tile_size):
                for x in range(0, width, tile_size):
                    color = (255, 255, 255) if (x + y) // tile_size % 2 == 0 else (200, 200, 200)
                    pygame.draw.rect(surface, color, (x, y, tile_size, tile_size))
                    
        elif pattern == "gradient":
            for y in range(height):
                intensity = int(255 * (y / height))
                color = (intensity, intensity, intensity)
                pygame.draw.line(surface, color, (0, y), (width, y))
                
        elif pattern == "noise":
            import random
            for y in range(height):
                for x in range(width):
                    intensity = random.randint(0, 255)
                    surface.set_at((x, y), (intensity, intensity, intensity))
        
        return surface
    
    def create_sprite_sheet(self, image_path: str, sprite_width: int, 
                           sprite_height: int) -> list:
        """Load and split a sprite sheet into individual sprites.
        
        Args:
            image_path: Path to sprite sheet image
            sprite_width: Width of each sprite
            sprite_height: Height of each sprite
            
        Returns:
            List of pygame Surfaces for each sprite
        """
        sheet = self.load_image(image_path)
        sprites = []
        
        sheet_width, sheet_height = sheet.get_size()
        
        for y in range(0, sheet_height, sprite_height):
            for x in range(0, sheet_width, sprite_width):
                sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                sprite.blit(sheet, (0, 0), (x, y, sprite_width, sprite_height))
                sprites.append(sprite)
        
        return sprites
    
    def clear_cache(self) -> None:
        """Clear all cached assets."""
        self.images.clear()
        self.sounds.clear()
        self.fonts.clear()
        self.music = None


# Global asset manager instance
_asset_manager: Optional[AssetManager] = None


def get_asset_manager() -> AssetManager:
    """Get the global asset manager instance.
    
    Returns:
        AssetManager singleton instance
    """
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetManager()
    return _asset_manager
