"""Graphics engine for video game creation using pygame."""
import pygame
import sys
from typing import Optional, Tuple


class GameEngine:
    """Main game engine class for managing game loop and rendering."""
    
    def __init__(self, width: int = 800, height: int = 600, title: str = "CFT Game Engine"):
        """Initialize the game engine.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60
        self.background_color = (0, 0, 0)  # Black
        
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
    def update(self) -> None:
        """Update game state. Override this method in subclasses."""
        pass
    
    def render(self) -> None:
        """Render game graphics. Override this method in subclasses."""
        self.screen.fill(self.background_color)
        
    def run(self) -> None:
        """Main game loop."""
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            pygame.display.flip()
            self.clock.tick(self.fps)
            
        pygame.quit()
        sys.exit()


class Sprite:
    """Basic sprite class for game objects."""
    
    def __init__(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255)):
        """Initialize a sprite.
        
        Args:
            x: X position
            y: Y position
            width: Sprite width
            height: Sprite height
            color: RGB color tuple
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0
        
    def update(self) -> None:
        """Update sprite position based on velocity."""
        self.x += self.velocity_x
        self.y += self.velocity_y
        
    def render(self, screen: pygame.Surface) -> None:
        """Render the sprite.
        
        Args:
            screen: Pygame surface to render to
        """
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
    def get_rect(self) -> pygame.Rect:
        """Get the sprite's bounding rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def collides_with(self, other: 'Sprite') -> bool:
        """Check collision with another sprite.
        
        Args:
            other: Another sprite to check collision with
            
        Returns:
            True if sprites are colliding
        """
        return self.get_rect().colliderect(other.get_rect())


def main() -> None:
    """Run a basic demo of the game engine."""
    engine = GameEngine(title="CFT-ENGINE0 Game Demo")
    print("Game engine initialized. Press ESC or close window to exit.")
    engine.run()


if __name__ == "__main__":
    main()
