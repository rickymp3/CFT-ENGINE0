"""
CFT-ENGINE0 - Core engine entry point.

A minimal computational engine for processing configurations and running tasks.
"""

from typing import Dict, Any
from engine_modules.config import Config, load_config


class Engine:
    """
    Core engine that manages configuration and execution state.
    
    Attributes:
        config: Engine configuration object
        running: Whether the engine is currently active
    """
    
    def __init__(self, config: Dict[str, Any] | Config | None = None):
        """
        Initialize the engine with optional configuration.
        
        Args:
            config: Configuration dictionary or Config object (uses defaults if None)
        """
        if config is None:
            # Default minimal config
            self.config = load_config({"environment": "dev"})
        elif isinstance(config, dict):
            self.config = load_config(config)
        else:
            self.config = config
        
        self.running = False
    
    def start(self) -> None:
        """Start the engine."""
        self.running = True
    
    def stop(self) -> None:
        """Stop the engine."""
        self.running = False
    
    def status(self) -> str:
        """
        Get the current engine status.
        
        Returns:
            Status message string
        """
        state = "running" if self.running else "stopped"
        env = self.config.environment
        return f"CFT-ENGINE0 engine is {state} (env: {env})."


def run() -> str:
    """
    Create and return status of a default engine instance.
    
    Returns:
        Status message string
    """
    engine = Engine()
    engine.start()
    return engine.status()


def main() -> None:
    """Print the engine status to stdout."""
    print(run())


if __name__ == "__main__":
    main()
