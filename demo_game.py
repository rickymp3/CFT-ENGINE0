"""Example game demo using the CFT game engine."""
import pygame
from game_engine import GameEngine, Sprite


class Player(Sprite):
    """Player character sprite."""
    
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 50, 50, (0, 255, 0))  # Green player
        self.speed = 5
        
    def handle_input(self) -> None:
        """Handle keyboard input for player movement."""
        keys = pygame.key.get_pressed()
        self.velocity_x = 0
        self.velocity_y = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity_y = self.speed


class Enemy(Sprite):
    """Enemy sprite that moves back and forth."""
    
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 40, 40, (255, 0, 0))  # Red enemy
        self.velocity_x = 2
        
    def update(self) -> None:
        """Update enemy position and bounce off edges."""
        super().update()
        # Bounce off screen edges
        if self.x <= 0 or self.x + self.width >= 800:
            self.velocity_x *= -1


class DemoGame(GameEngine):
    """Demo game showcasing the engine features."""
    
    def __init__(self):
        super().__init__(800, 600, "CFT-ENGINE0 - Demo Game")
        self.background_color = (20, 20, 40)  # Dark blue
        
        # Create game objects
        self.player = Player(375, 275)
        self.enemies = [
            Enemy(100, 100),
            Enemy(600, 400),
            Enemy(300, 200)
        ]
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        
    def update(self) -> None:
        """Update game state."""
        self.player.handle_input()
        self.player.update()
        
        # Keep player on screen
        self.player.x = max(0, min(self.player.x, self.width - self.player.width))
        self.player.y = max(0, min(self.player.y, self.height - self.player.height))
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update()
            
            # Check collision with player
            if self.player.collides_with(enemy):
                # Reset enemy position when hit
                enemy.x = 0 if enemy.velocity_x > 0 else self.width - enemy.width
                self.score += 10
        
    def render(self) -> None:
        """Render game graphics."""
        super().render()
        
        # Render all sprites
        self.player.render(self.screen)
        for enemy in self.enemies:
            enemy.render(self.screen)
            
        # Render score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # Render instructions
        instructions_font = pygame.font.Font(None, 24)
        instructions = [
            "Arrow Keys or WASD to move",
            "Touch red enemies to score",
            "ESC to quit"
        ]
        for i, text in enumerate(instructions):
            inst_text = instructions_font.render(text, True, (200, 200, 200))
            self.screen.blit(inst_text, (10, self.height - 80 + i * 25))


def main() -> None:
    """Run the demo game."""
    game = DemoGame()
    print("Starting CFT-ENGINE0 Demo Game...")
    print("Controls: Arrow Keys or WASD to move, ESC to quit")
    game.run()


if __name__ == "__main__":
    main()
