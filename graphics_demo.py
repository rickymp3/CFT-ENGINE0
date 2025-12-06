"""AAA Graphics Demo showcasing advanced rendering features."""
import pygame
from game_engine import GameEngine, Sprite
from asset_manager import get_asset_manager
from rendering import ParticleSystem, Camera, LightingSystem, PostProcessing
import math
import random


class AdvancedPlayer(Sprite):
    """Player with particle effects."""
    
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 40, 40, (100, 200, 255))
        self.speed = 4
        self.particle_system = ParticleSystem(x + 20, y + 20, 200)
        self.trail_timer = 0
        
    def handle_input(self) -> None:
        """Handle keyboard input."""
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
            
        # Emit particles when moving
        if self.velocity_x != 0 or self.velocity_y != 0:
            self.trail_timer += 1
            if self.trail_timer % 3 == 0:
                self.particle_system.x = self.x + self.width // 2
                self.particle_system.y = self.y + self.height // 2
                self.particle_system.emit(2, (100, 200, 255), (0.5, 1.5), 30)
    
    def update(self) -> None:
        """Update player and particles."""
        super().update()
        self.particle_system.update()
        
    def render(self, screen: pygame.Surface) -> None:
        """Render player with glow effect."""
        # Draw glow
        for i in range(3, 0, -1):
            glow_surface = pygame.Surface((self.width + i*10, self.height + i*10), 
                                         pygame.SRCALPHA)
            alpha = 60 // i
            color_with_alpha = (*self.color, alpha)
            pygame.draw.rect(glow_surface, color_with_alpha, 
                           (0, 0, self.width + i*10, self.height + i*10), 
                           border_radius=5)
            screen.blit(glow_surface, 
                       (self.x - i*5, self.y - i*5))
        
        # Draw main sprite
        super().render(screen)
        
        # Draw particles
        self.particle_system.render(screen)


class Star:
    """Animated star background element."""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, 2 * math.pi)
        
    def update(self) -> None:
        """Update star animation."""
        self.twinkle_offset += self.twinkle_speed
        
    def render(self, screen: pygame.Surface) -> None:
        """Render twinkling star."""
        twinkle = abs(math.sin(self.twinkle_offset))
        brightness = int(self.brightness * twinkle)
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)


class GraphicsDemo(GameEngine):
    """AAA Graphics demonstration game."""
    
    def __init__(self):
        super().__init__(1024, 768, "CFT-ENGINE0 - AAA Graphics Demo")
        self.background_color = (10, 10, 30)
        
        # Initialize systems
        self.asset_manager = get_asset_manager()
        self.camera = Camera(self.width, self.height)
        self.lighting = LightingSystem(self.width, self.height)
        self.lighting.ambient_light = 0.2
        
        # Create player
        self.player = AdvancedPlayer(self.width // 2, self.height // 2)
        
        # Create starfield
        self.stars = [Star(random.randint(0, self.width), 
                          random.randint(0, self.height)) 
                     for _ in range(100)]
        
        # Create particle emitters
        self.emitters = [
            ParticleSystem(200, 200, 150),
            ParticleSystem(self.width - 200, 200, 150),
            ParticleSystem(self.width // 2, self.height - 200, 150)
        ]
        
        # UI
        self.font = self.asset_manager.load_font(None, 24)
        self.title_font = self.asset_manager.load_font(None, 48)
        
        # Effects toggles
        self.show_particles = True
        self.show_lighting = True
        self.show_bloom = False
        self.show_vignette = True
        self.frame_count = 0
        
    def handle_events(self) -> None:
        """Handle events with effect toggles."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1:
                    self.show_particles = not self.show_particles
                elif event.key == pygame.K_2:
                    self.show_lighting = not self.show_lighting
                elif event.key == pygame.K_3:
                    self.show_bloom = not self.show_bloom
                elif event.key == pygame.K_4:
                    self.show_vignette = not self.show_vignette
                elif event.key == pygame.K_SPACE:
                    # Spawn particle burst at player
                    for emitter in self.emitters:
                        emitter.emit(20, 
                                   (random.randint(100, 255), 
                                    random.randint(100, 255), 
                                    random.randint(100, 255)),
                                   (2, 8), 90)
        
    def update(self) -> None:
        """Update game state."""
        self.frame_count += 1
        
        # Update player
        self.player.handle_input()
        self.player.update()
        
        # Keep player on screen
        self.player.x = max(0, min(self.player.x, self.width - self.player.width))
        self.player.y = max(0, min(self.player.y, self.height - self.player.height))
        
        # Update stars
        for star in self.stars:
            star.update()
        
        # Update particle emitters
        if self.show_particles:
            for i, emitter in enumerate(self.emitters):
                if self.frame_count % 5 == 0:
                    colors = [
                        (255, 100, 100),  # Red
                        (100, 255, 100),  # Green
                        (100, 100, 255)   # Blue
                    ]
                    emitter.emit(1, colors[i], (1, 3), 120)
                emitter.update()
        
        # Update lighting
        self.lighting.clear_lights()
        # Add light at player
        self.lighting.add_light(int(self.player.x + self.player.width // 2),
                               int(self.player.y + self.player.height // 2),
                               200, (100, 200, 255))
        # Add lights at emitters
        for emitter in self.emitters:
            self.lighting.add_light(emitter.x, emitter.y, 150, (255, 200, 100))
        
    def render(self) -> None:
        """Render with advanced graphics."""
        # Clear screen
        self.screen.fill(self.background_color)
        
        # Render starfield
        for star in self.stars:
            star.render(self.screen)
        
        # Render particle emitters
        if self.show_particles:
            for emitter in self.emitters:
                emitter.render(self.screen)
        
        # Render player
        self.player.render(self.screen)
        
        # Apply lighting
        if self.show_lighting:
            lighting_overlay = self.lighting.render(self.screen)
            self.screen.blit(lighting_overlay, (0, 0))
        
        # Apply post-processing effects
        if self.show_bloom:
            self.screen = PostProcessing.apply_bloom(self.screen, 0.3)
        
        if self.show_vignette:
            self.screen = PostProcessing.apply_vignette(self.screen, 0.4)
        
        # Render UI
        self._render_ui()
        
    def _render_ui(self) -> None:
        """Render UI elements."""
        # Title
        title = self.title_font.render("AAA Graphics Demo", True, (255, 255, 255))
        title_shadow = self.title_font.render("AAA Graphics Demo", True, (0, 0, 0))
        self.screen.blit(title_shadow, (self.width // 2 - title.get_width() // 2 + 2, 12))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 10))
        
        # Instructions
        instructions = [
            "Arrow Keys / WASD - Move",
            "SPACE - Particle Burst",
            "1 - Toggle Particles",
            "2 - Toggle Lighting",
            "3 - Toggle Bloom",
            "4 - Toggle Vignette",
            "ESC - Quit"
        ]
        
        y_offset = self.height - 200
        for instruction in instructions:
            text = self.font.render(instruction, True, (200, 200, 200))
            shadow = self.font.render(instruction, True, (0, 0, 0))
            self.screen.blit(shadow, (11, y_offset + 1))
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
        
        # Status indicators
        status_y = 70
        statuses = [
            f"Particles: {'ON' if self.show_particles else 'OFF'}",
            f"Lighting: {'ON' if self.show_lighting else 'OFF'}",
            f"Bloom: {'ON' if self.show_bloom else 'OFF'}",
            f"Vignette: {'ON' if self.show_vignette else 'OFF'}",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        
        for status in statuses:
            color = (100, 255, 100) if 'ON' in status else (255, 100, 100)
            if 'FPS' in status:
                color = (255, 255, 100)
            text = self.font.render(status, True, color)
            self.screen.blit(text, (10, status_y))
            status_y += 25


def main() -> None:
    """Run the AAA graphics demo."""
    print("Starting AAA Graphics Demo...")
    print("=" * 50)
    print("Features:")
    print("- Particle systems with physics")
    print("- Dynamic lighting")
    print("- Post-processing effects (bloom, vignette)")
    print("- Animated starfield background")
    print("- Smooth camera system")
    print("=" * 50)
    
    demo = GraphicsDemo()
    demo.run()


if __name__ == "__main__":
    if "DISPLAY" not in os.environ:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    main()
