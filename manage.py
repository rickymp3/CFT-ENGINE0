#!/usr/bin/env python3
"""CFT Engine Management CLI Tool.

Usage:
    python manage.py new-project <name>  - Create a new project
    python manage.py run [--lang LANG]   - Run the engine
    python manage.py editor              - Launch visual scene editor
    python manage.py test                 - Run tests
    python manage.py config [--show]      - Manage configuration
"""
import sys
import argparse
import subprocess
from pathlib import Path
import shutil


def create_new_project(name: str) -> None:
    """Scaffold a new CFT Engine project.
    
    Args:
        name: Project name
    """
    project_path = Path(name)
    
    if project_path.exists():
        print(f"Error: Directory '{name}' already exists!")
        return
    
    print(f"Creating new project: {name}")
    
    # Create directory structure
    project_path.mkdir()
    (project_path / "assets").mkdir()
    (project_path / "assets" / "models").mkdir()
    (project_path / "assets" / "textures").mkdir()
    (project_path / "assets" / "sounds").mkdir()
    (project_path / "scripts").mkdir()
    
    # Create main.py
    main_content = '''"""Main entry point for your CFT Engine game."""
from direct.showbase.ShowBase import ShowBase


class MyGame(ShowBase):
    """Your game class."""
    
    def __init__(self):
        super().__init__()
        print("Welcome to your CFT Engine game!")
        # Add your initialization code here


if __name__ == "__main__":
    game = MyGame()
    game.run()
'''
    (project_path / "main.py").write_text(main_content)
    
    # Copy config.yaml
    config_source = Path("config.yaml")
    if config_source.exists():
        shutil.copy(config_source, project_path / "config.yaml")
    
    # Create README
    readme_content = f'''# {name}

A CFT Engine game project.

## Running

```bash
python main.py
```

## Configuration

Edit `config.yaml` to customize engine settings.
'''
    (project_path / "README.md").write_text(readme_content)
    
    print(f"✓ Project '{name}' created successfully!")
    print(f"  cd {name}")
    print(f"  python main.py")


def run_engine(language: str = "en") -> None:
    """Run the CFT Engine.
    
    Args:
        language: Language code (en, es, fr)
    """
    print(f"Starting CFT Engine (language: {language})")
    import os
    os.environ['CFT_LANG'] = language
    
    try:
        from cft_panda3d_engine import CFTGame
        game = CFTGame(language=language)
        game.run()
    except ImportError as e:
        print(f"Error: Failed to import engine: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")


def run_tests() -> None:
    """Run the test suite."""
    print("Running tests...")
    result = subprocess.run(["python", "-m", "pytest", "-v"], cwd=".")
    sys.exit(result.returncode)


def show_config() -> None:
    """Display current configuration."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("No config.yaml found.")
        return
    
    print("Current configuration:")
    print("=" * 60)
    print(config_path.read_text())


def launch_editor() -> None:
    """Launch the visual scene editor."""
    print("\n" + "="*60)
    print("Launching CFT-ENGINE0 Visual Scene Editor...")
    print("="*60 + "\n")
    
    try:
        result = subprocess.run([sys.executable, 'editor.py'])
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error launching editor: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CFT Engine Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # new-project command
    new_parser = subparsers.add_parser('new-project', help='Create a new project')
    new_parser.add_argument('name', help='Project name')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run the engine')
    run_parser.add_argument('--lang', default='en', 
                           choices=['en', 'es', 'fr'],
                           help='Language (en/es/fr)')
    
    # editor command
    subparsers.add_parser('editor', help='Launch visual scene editor')
    
    # test command
    subparsers.add_parser('test', help='Run tests')
    
    # config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true',
                              help='Show current configuration')
    
    args = parser.parse_args()
    
    if args.command == 'new-project':
        create_new_project(args.name)
    elif args.command == 'run':
        run_engine(args.lang)
    elif args.command == 'editor':
        launch_editor()
    elif args.command == 'test':
        run_tests()
    elif args.command == 'config':
        if args.show:
            show_config()
        else:
            print("Use --show to display configuration")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
