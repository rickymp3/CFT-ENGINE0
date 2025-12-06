# Story Generator Quick Reference

## Installation & Setup

```bash
# Already included - no additional installation needed!
# All story generation features work out of the box

# Optional: For full LLM integration
export OPENAI_API_KEY="your-key-here"
```

## CLI Commands

```bash
# Generate a story from a prompt
python manage.py story --prompt "A hero's journey"

# With all options
python manage.py story \
  --prompt "A detective solving a mystery" \
  --genre mystery \
  --tone dark \
  --branches 5 \
  --output my_story.json
```

## Quick Python API

```python
from engine_modules.story_generator import StoryGraph, BeatType, CharacterRole

# Create a story
story = StoryGraph("My Story")

# Add character
hero = story.add_character("Hero", CharacterRole.PROTAGONIST, "Main character")

# Add beats (narrative scenes)
beat1 = story.add_beat(BeatType.EXPOSITION, "Setup", "Beginning", [hero.id])
beat2 = story.add_beat(BeatType.CLIMAX, "Final", "The confrontation", [hero.id])

# Connect beats
story.connect_beats(beat1.id, beat2.id)

# Save story
story.save_to_file("story.json")

# Load story
loaded = StoryGraph.load_from_file("story.json")

# Get summary
print(story.get_story_summary())
```

## Interactive Playback

```python
from engine_modules.story_integration import InteractiveStoryPlayer

# Create player
player = InteractiveStoryPlayer(story)

# Start story
player.start()

# Play through with choices
while True:
    choices = player.get_available_choices()
    if choices:
        print("Choose:")
        for i, c in enumerate(choices):
            print(f"  {i}: {c['text']}")
        player.make_choice(choices[0]['id'])  # Pick first choice
    else:
        if not player.advance_to_next():  # Auto-advance
            break

# Track progress
progress = player.get_story_progress()
print(f"Story {progress['completion_percent']:.0f}% complete")
```

## Asset Integration

```python
from engine_modules.story_integration import StoryToAssets

# Extract what assets your story needs
requirements = StoryToAssets.extract_asset_requirements(story)

print(f"Characters: {requirements['characters']}")
print(f"Skyboxes: {requirements['skyboxes']}")
print(f"Audio: {requirements['sfx']}")

# Get import commands
commands = StoryToAssets.get_asset_import_commands(requirements)
for cmd in commands:
    print(f"Import: {cmd['asset_name']} ({cmd['asset_type']})")
```

## Animation Generation

```python
from engine_modules.story_integration import StoryToAnimation

# Auto-generate animations for a character in a beat
animations = StoryToAnimation.generate_animation_cues(beat, character_id)
# Returns: ['talk', 'listen', 'react']

# In your animation controller:
for anim in animations:
    controller.load_animation(anim, "")
    controller.play(anim, blend_time=0.5)
```

## Visual Script Conversion

```python
from engine_modules.story_integration import StoryToVisualScript

# Convert story beats to visual script nodes
script = StoryToVisualScript._create_stub_script(story)

print(f"Nodes: {len(script['nodes'])}")
print(f"Edges: {len(script['edges'])}")

# Save as JSON for editor
import json
with open("story_script.json", "w") as f:
    json.dump(script, f, indent=2)
```

## Story Types

```python
from engine_modules.story_generator import BeatType

# Available beat types:
BeatType.EXPOSITION              # Story setup
BeatType.INCITING_INCIDENT       # Event that starts conflict
BeatType.RISING_ACTION           # Building tension
BeatType.CLIMAX                  # Peak/conflict
BeatType.FALLING_ACTION          # Consequences
BeatType.RESOLUTION              # Ending
BeatType.DIALOGUE                # Character talk
BeatType.ACTION                  # Combat/movement
BeatType.CINEMATIC               # Cutscene
BeatType.DECISION_POINT          # Player choice
```

## Character Roles

```python
from engine_modules.story_generator import CharacterRole

CharacterRole.PROTAGONIST        # Main character
CharacterRole.ANTAGONIST         # Opposition
CharacterRole.SUPPORT            # Helper
CharacterRole.NPC                # Non-player
```

## Story Generation Options

```bash
# Genres
--genre fantasy|scifi|mystery|romance|horror|general

# Tones
--tone dramatic|comedic|dark|epic|neutral

# Other options
--branches N          # Number of decision points
--output file.json    # Save location
```

## Testing

```bash
# Run story tests
python -m pytest tests/test_story_generator.py -v

# Run with coverage
python -m pytest tests/test_story_generator.py --cov=engine_modules.story_generator

# Run example
python examples/story_generator_example.py
```

## Troubleshooting

**Q: Stories generated without LLM API key look too simple**
A: Set OPENAI_API_KEY environment variable for better generation

**Q: Need animation names to exist in your system**
A: Animation cue generation is a starting point; customize the mapping in `StoryToAnimation.generate_animation_cues()`

**Q: Want more details in asset extraction**
A: Extend `StoryToAssets` with keyword patterns specific to your asset library

**Q: How do I save story state during playback**
A: Use `player.get_story_progress()` and implement custom serialization

## Files to Know

- `engine_modules/story_generator.py` - Core story system
- `engine_modules/story_integration.py` - Engine integration
- `tests/test_story_generator.py` - Test examples
- `examples/story_generator_example.py` - 5 working examples
- `STORY_GENERATOR_GUIDE.md` - Full documentation

## Resources

- [Story Generator Guide](STORY_GENERATOR_GUIDE.md) - Complete documentation
- [Implementation Details](STORY_GENERATOR_IMPLEMENTATION.md) - Architecture & metrics
- [Example Programs](examples/story_generator_example.py) - 5 working examples
- [Test Suite](tests/test_story_generator.py) - 26 unit tests with examples

---

**Version:** 1.0  
**Last Updated:** December 2024  
**Status:** ✅ Production Ready
