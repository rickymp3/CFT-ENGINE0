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


def generate_story(prompt: str, output: str = None, genre: str = "fantasy", 
                  tone: str = "dramatic", branches: int = 3) -> None:
    """Generate a story from a prompt.
    
    Args:
        prompt: Story prompt
        output: Output file path (optional)
        genre: Story genre
        tone: Story tone
        branches: Number of branching decision points
    """
    print(f"\nGenerating story from prompt: '{prompt}'")
    print(f"Genre: {genre} | Tone: {tone} | Branches: {branches}")
    print("-" * 60)
    
    try:
        from engine_modules.story_generator import generate_story_from_llm
        
        constraints = {
            'genre': genre,
            'tone': tone,
            'branches': branches,
            'beats': max(5, branches * 2)
        }
        
        story = generate_story_from_llm(prompt, constraints)
        
        # Display summary
        print("\nGenerated Story Summary:")
        print("-" * 60)
        print(story.get_story_summary())
        
        # Save if output specified
        if output:
            story.save_to_file(output)
            print(f"\nStory saved to: {output}")
        else:
            # Save with default name
            default_output = f"story_{story.title.replace(' ', '_').lower()}.json"
            story.save_to_file(default_output)
            print(f"\nStory saved to: {default_output}")
        
        # Show asset requirements
        from engine_modules.story_integration import StoryToAssets
        reqs = StoryToAssets.extract_asset_requirements(story)
        print("\nAsset Requirements:")
        for asset_type, assets in reqs.items():
            if assets:
                print(f"  {asset_type}: {', '.join(assets)}")
        
    except Exception as e:
        print(f"Error generating story: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_texture(prompt: str = None, image_path: str = None,
                    description: str = None, resolution: str = "2K",
                    maps: list = None, batch_size: int = 1,
                    language: str = "en", threshold: float = 0.7,
                    max_retries: int = 3, output_dir: str = None,
                    material_name: str = None, enforce_quality: bool = True,
                    style_image: str = None) -> None:
    """Generate PBR textures from text or image.
    
    Args:
        prompt: Text description of texture
        image_path: Reference image path
        description: Additional description for reference image
        resolution: Output resolution
        maps: List of map types to generate
        batch_size: Number of variations
        language: Prompt language
        threshold: Quality threshold
        max_retries: Max generation attempts
        output_dir: Output directory
        material_name: Name for material
        enforce_quality: Whether to enforce quality threshold
        style_image: Style transfer reference image
    """
    try:
        from engine_modules.texture_generator import TextureGenerator
    except ImportError:
        print("Error: Could not import TextureGenerator")
        return
    
    # Validate inputs
    if not prompt and not image_path:
        print("Error: Please provide either --prompt or --image")
        return
    
    if image_path and not Path(image_path).exists():
        print(f"Error: Reference image not found: {image_path}")
        return
    
    if style_image and not Path(style_image).exists():
        print(f"Error: Style image not found: {style_image}")
        return
    
    # Setup configuration
    config = {
        "realism_threshold": threshold,
        "max_retries": max_retries,
        "output_dir": output_dir or "generated_textures"
    }
    
    print("🎨 Texture Generator CLI")
    print(f"Resolution: {resolution}")
    print(f"Quality Threshold: {threshold:.2f}")
    print(f"Max Retries: {max_retries}")
    
    # Initialize generator
    generator = TextureGenerator(config)
    
    # Progress callback
    def on_progress(stage, pct, message):
        bar_length = 30
        filled = int(bar_length * pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}] {pct:3.0f}% {stage}: {message}")
    
    generator.set_progress_callback(on_progress)
    
    # Generate textures
    if batch_size > 1:
        print(f"\nGenerating {batch_size} texture variations...")
        results = generator.generate_batch(
            prompt=prompt,
            batch_size=batch_size,
            resolution=resolution,
            map_types=maps or ["albedo", "normal", "roughness", "metallic"],
            language=language,
            enforce_quality=enforce_quality
        )
        
        if results:
            print(f"✅ Successfully generated {len(results)}/{batch_size} textures")
            for i, texture_set in enumerate(results, 1):
                print(f"  {i}. Realism Score: {texture_set.realism_score:.2f}")
                material_json = generator.create_material_json(
                    material_name or f"{material_name}_variation_{i}",
                    texture_set
                )
                if material_json:
                    print(f"     Material: {material_json}")
        else:
            print("❌ Failed to generate texture variations")
        
    elif style_image:
        print(f"\nGenerating texture with style transfer...")
        texture_set = generator.generate_stylized(
            content_prompt=prompt,
            style_image_path=style_image,
            resolution=resolution,
            map_types=maps or ["albedo", "normal", "roughness", "metallic"],
            language=language,
            enforce_quality=enforce_quality
        )
        
        if texture_set:
            print(f"✅ Texture generated successfully!")
            print(f"   Realism Score: {texture_set.realism_score:.2f}")
            material_json = generator.create_material_json(
                material_name or "generated_material",
                texture_set
            )
            if material_json:
                print(f"   Material: {material_json}")
        else:
            print("❌ Texture generation failed")
    
    elif image_path:
        print(f"\nGenerating texture from reference image...")
        texture_set = generator.generate_from_image(
            image_path=image_path,
            description=description or "generate texture from reference image",
            resolution=resolution,
            map_types=maps or ["albedo", "normal", "roughness", "metallic"],
            language=language,
            enforce_quality=enforce_quality
        )
        
        if texture_set:
            print(f"✅ Texture generated successfully!")
            print(f"   Realism Score: {texture_set.realism_score:.2f}")
            material_json = generator.create_material_json(
                material_name or "generated_material",
                texture_set
            )
            if material_json:
                print(f"   Material: {material_json}")
        else:
            print("❌ Texture generation failed")
    
    else:
        print(f"\nGenerating texture from prompt...")
        texture_set = generator.generate_from_prompt(
            prompt=prompt,
            resolution=resolution,
            map_types=maps or ["albedo", "normal", "roughness", "metallic"],
            language=language,
            enforce_quality=enforce_quality
        )
        
        if texture_set:
            print(f"✅ Texture generated successfully!")
            print(f"   Realism Score: {texture_set.realism_score:.2f}")
            material_json = generator.create_material_json(
                material_name or "generated_material",
                texture_set
            )
            if material_json:
                print(f"   Material: {material_json}")
        else:
            print("❌ Texture generation failed")


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
    
    # story command
    story_parser = subparsers.add_parser('story', help='Generate a story')
    story_parser.add_argument('--prompt', required=True,
                             help='Story prompt')
    story_parser.add_argument('--output', '-o', 
                             help='Output file path (optional)')
    story_parser.add_argument('--genre', default='fantasy',
                             choices=['fantasy', 'scifi', 'mystery', 'romance', 'horror', 'general'],
                             help='Story genre')
    story_parser.add_argument('--tone', default='dramatic',
                             choices=['dramatic', 'comedic', 'dark', 'epic', 'neutral'],
                             help='Story tone')
    story_parser.add_argument('--branches', type=int, default=3,
                             help='Number of decision branches')
    
    # texture command
    texture_parser = subparsers.add_parser('texture', help='Generate PBR textures')
    texture_parser.add_argument('--prompt', 
                               help='Texture description (text-to-texture)')
    texture_parser.add_argument('--image',
                               help='Reference image path (image-to-texture)')
    texture_parser.add_argument('--description',
                               help='Description for reference image')
    texture_parser.add_argument('--resolution', default='2K',
                               choices=['512', '1K', '2K', '4K', '8K'],
                               help='Output resolution')
    texture_parser.add_argument('--maps', nargs='+',
                               default=['albedo', 'normal', 'roughness', 'metallic'],
                               choices=['albedo', 'normal', 'roughness', 'metallic', 'height', 'ao', 'emission'],
                               help='Maps to generate')
    texture_parser.add_argument('--batch', type=int, default=1,
                               help='Number of variations to generate')
    texture_parser.add_argument('--language', default='en',
                               help='Prompt language code')
    texture_parser.add_argument('--threshold', type=float, default=0.7,
                               help='Quality threshold (0.0-1.0)')
    texture_parser.add_argument('--max-retries', type=int, default=3,
                               help='Max generation attempts')
    texture_parser.add_argument('--output', '-o',
                               help='Output directory')
    texture_parser.add_argument('--material-name',
                               help='Name for generated material')
    texture_parser.add_argument('--no-quality-check', action='store_true',
                               help='Skip quality evaluation')
    texture_parser.add_argument('--style',
                               help='Style transfer reference image')
    
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
    elif args.command == 'story':
        generate_story(args.prompt, args.output, args.genre, args.tone, args.branches)
    elif args.command == 'texture':
        generate_texture(
            prompt=args.prompt,
            image_path=args.image,
            description=args.description,
            resolution=args.resolution,
            maps=args.maps,
            batch_size=args.batch,
            language=args.language,
            threshold=args.threshold,
            max_retries=args.max_retries,
            output_dir=args.output,
            material_name=args.material_name,
            enforce_quality=not args.no_quality_check,
            style_image=args.style
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
