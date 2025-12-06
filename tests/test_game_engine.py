"""Tests for the game engine."""
import pygame
from game_engine import GameEngine, Sprite


def test_game_engine_initialization():
    """Test that the game engine initializes correctly."""
    engine = GameEngine(640, 480, "Test Game")
    assert engine.width == 640
    assert engine.height == 480
    assert engine.fps == 60
    assert engine.running is False
    pygame.quit()


def test_sprite_creation():
    """Test sprite initialization."""
    sprite = Sprite(100, 200, 50, 60, (255, 0, 0))
    assert sprite.x == 100
    assert sprite.y == 200
    assert sprite.width == 50
    assert sprite.height == 60
    assert sprite.color == (255, 0, 0)
    assert sprite.velocity_x == 0
    assert sprite.velocity_y == 0


def test_sprite_update():
    """Test sprite movement."""
    sprite = Sprite(0, 0, 10, 10)
    sprite.velocity_x = 5
    sprite.velocity_y = 3
    sprite.update()
    assert sprite.x == 5
    assert sprite.y == 3


def test_sprite_collision():
    """Test sprite collision detection."""
    sprite1 = Sprite(0, 0, 50, 50)
    sprite2 = Sprite(25, 25, 50, 50)
    sprite3 = Sprite(100, 100, 50, 50)
    
    assert sprite1.collides_with(sprite2) is True
    assert sprite1.collides_with(sprite3) is False
    assert sprite2.collides_with(sprite3) is False
