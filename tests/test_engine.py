"""Tests for CFT-ENGINE0 core engine."""

from engine import Engine, run, main
from engine_modules.config import Config


class TestEngine:
    """Test suite for Engine class."""
    
    def test_engine_initialization_default(self):
        """Engine initializes with default config and stopped state."""
        engine = Engine()
        assert isinstance(engine.config, Config)
        assert engine.config.environment == "dev"
        assert engine.running is False
    
    def test_engine_initialization_with_dict_config(self):
        """Engine initializes with provided dict config."""
        config = {"environment": "test", "timeout": 60}
        engine = Engine(config)
        assert engine.config.environment == "test"
        assert engine.config.timeout == 60
        assert engine.running is False
    
    def test_engine_initialization_with_config_object(self):
        """Engine initializes with Config object."""
        config = Config({"environment": "prod"})
        engine = Engine(config)
        assert engine.config.environment == "prod"
    
    def test_engine_start(self):
        """Starting the engine sets running to True."""
        engine = Engine()
        engine.start()
        assert engine.running is True
    
    def test_engine_stop(self):
        """Stopping the engine sets running to False."""
        engine = Engine()
        engine.start()
        engine.stop()
        assert engine.running is False
    
    def test_engine_status_stopped(self):
        """Status reflects stopped state."""
        engine = Engine()
        assert "stopped" in engine.status()
        assert "dev" in engine.status()
    
    def test_engine_status_running(self):
        """Status reflects running state."""
        engine = Engine()
        engine.start()
        assert "running" in engine.status()


def test_run_returns_status_message():
    """run() creates engine, starts it, and returns running status."""
    result = run()
    assert "running" in result
    assert "dev" in result


def test_main_prints_status_message(capsys):
    """main() prints the status to stdout."""
    main()
    captured = capsys.readouterr()
    assert "running" in captured.out
    assert "dev" in captured.out
