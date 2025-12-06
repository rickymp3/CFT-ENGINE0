"""Story Generator Example - Interactive Narrative Creation.

This example demonstrates:
1. Creating a story graph programmatically
2. Adding characters, beats, and choices
3. Playing the story interactively
4. Saving/loading stories
5. Extracting asset requirements
"""

import json
from engine_modules.story_generator import (
    StoryGraph, BeatType, CharacterRole, generate_story_from_llm
)
from engine_modules.story_integration import (
    StoryToAssets, InteractiveStoryPlayer, StoryToVisualScript
)


def example_1_create_manual_story():
    """Create a story manually."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Manual Story Creation")
    print("="*60)
    
    # Create story
    story = StoryGraph("The Lost Artifact")
    story.description = "An explorer discovers a cursed artifact in a forgotten temple"
    story.genre = "adventure"
    story.tone = "dramatic"
    
    # Add characters
    explorer = story.add_character(
        "Elena",
        CharacterRole.PROTAGONIST,
        "Brave explorer seeking lost artifacts"
    )
    guardian = story.add_character(
        "Ancient Guardian",
        CharacterRole.ANTAGONIST,
        "Spirit protecting the temple"
    )
    guide = story.add_character(
        "Marcus",
        CharacterRole.SUPPORT,
        "Local guide with forbidden knowledge"
    )
    
    # Create beats
    beat1 = story.add_beat(
        BeatType.EXPOSITION,
        "Arrival at the Temple",
        "Elena arrives at the entrance with Marcus",
        [explorer.id, guide.id],
        duration=10.0
    )
    beat1.visual_settings = {
        'lighting': {'intensity': 0.4, 'color': (1.0, 0.7, 0.3)},
        'skybox': 'sunset_glow'
    }
    
    beat2_safe = story.add_beat(
        BeatType.RISING_ACTION,
        "The Safe Path",
        "Elena finds a secret passage avoiding danger",
        [explorer.id, guide.id],
        duration=15.0
    )
    
    beat2_danger = story.add_beat(
        BeatType.RISING_ACTION,
        "The Direct Approach",
        "Elena charges straight through the temple corridors",
        [explorer.id],
        duration=15.0
    )
    
    beat3_safe = story.add_beat(
        BeatType.CLIMAX,
        "Peaceful Offering",
        "Elena makes peace with the guardian spirit",
        [explorer.id, guardian.id],
        duration=12.0
    )
    
    beat3_danger = story.add_beat(
        BeatType.CLIMAX,
        "Epic Confrontation",
        "Elena battles the guardian",
        [explorer.id, guardian.id],
        duration=20.0
    )
    beat3_danger.animation_cues = ['attack_intense', 'dodge', 'power_up', 'ultimate']
    
    beat4_peace = story.add_beat(
        BeatType.RESOLUTION,
        "The Peaceful Ending",
        "The artifact is safely secured, the guardian finds peace",
        [explorer.id, guardian.id],
        duration=8.0
    )
    
    beat4_victory = story.add_beat(
        BeatType.RESOLUTION,
        "The Pyrrhic Victory",
        "Elena escapes with the artifact, but the temple collapses",
        [explorer.id],
        duration=10.0
    )
    
    # Create story flow with branches
    story.connect_beats(beat1.id, beat2_safe.id)
    story.connect_beats(beat1.id, beat2_danger.id)
    story.connect_beats(beat2_safe.id, beat3_safe.id)
    story.connect_beats(beat2_danger.id, beat3_danger.id)
    story.connect_beats(beat3_safe.id, beat4_peace.id)
    story.connect_beats(beat3_danger.id, beat4_victory.id)
    
    # Add player choices
    story.add_choice(
        beat1.id,
        "Take the secret passage with Marcus",
        beat2_safe.id,
        "A safer, more careful approach"
    )
    story.add_choice(
        beat1.id,
        "Charge in to confront the threat",
        beat2_danger.id,
        "Direct but risky"
    )
    
    # Set entry/exit
    story.set_start_beats([beat1.id])
    story.set_end_beats([beat4_peace.id, beat4_victory.id])
    
    # Show story info
    print(f"\n✓ Created: {story.title}")
    print(story.get_story_summary())
    print(f"  ID: {story.id}")
    
    # Save story
    story.save_to_file("example_story.json")
    print(f"\n✓ Saved to: example_story.json")
    
    return story


def example_2_play_interactive_story(story):
    """Play the story interactively with choices."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Interactive Story Playback")
    print("="*60)
    
    player = InteractiveStoryPlayer(story)
    
    # Start story
    print("\n--- Story Start ---")
    current_beat_id = player.start()
    current_beat = story.beats[current_beat_id]
    print(f"\n📖 {current_beat.title}")
    print(f"   {current_beat.description}")
    
    # Play through with choices
    while True:
        choices = player.get_available_choices()
        
        if not choices:
            # No choices, auto-advance
            next_beat = player.advance_to_next()
            if not next_beat:
                break
            current_beat = story.beats[next_beat]
            print(f"\n📖 {current_beat.title}")
            print(f"   {current_beat.description}")
        else:
            # Show choices
            print("\nAvailable choices:")
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice['text']}")
            
            # Make first choice (in real game, player would select)
            choice_idx = 0
            selected_choice = choices[choice_idx]
            print(f"\n→ You chose: {selected_choice['text']}")
            
            next_beat_id = player.make_choice(selected_choice['id'])
            if not next_beat_id:
                break
            
            current_beat = story.beats[next_beat_id]
            print(f"\n📖 {current_beat.title}")
            print(f"   {current_beat.description}")
    
    # Show progress
    progress = player.get_story_progress()
    print("\n--- Story Progress ---")
    print(f"Completion: {progress['completion_percent']:.1f}%")
    print(f"Beats visited: {progress['visited_beat_count']}/{progress['total_beat_count']}")
    print(f"Choices made: {len(progress['choices_made'])}")


def example_3_extract_assets(story):
    """Extract asset requirements from story."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Asset Extraction")
    print("="*60)
    
    requirements = StoryToAssets.extract_asset_requirements(story)
    
    print("\nAsset Requirements:")
    for asset_type, assets in requirements.items():
        if assets:
            print(f"  {asset_type.upper()}:")
            for asset in assets:
                print(f"    - {asset}")
    
    # Generate import commands
    commands = StoryToAssets.get_asset_import_commands(requirements)
    print(f"\nWould import {len(commands)} asset(s)")


def example_4_convert_to_visual_script(story):
    """Convert story to visual script representation."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Story as Visual Script")
    print("="*60)
    
    script = StoryToVisualScript._create_stub_script(story)
    
    print(f"\nVisual Script: {script['name']}")
    print(f"  Nodes: {len(script['nodes'])}")
    print(f"  Edges: {len(script['edges'])}")
    
    # Show first node
    if script['nodes']:
        node = script['nodes'][0]
        print(f"\nFirst Node:")
        print(f"  Type: {node['type']}")
        print(f"  Title: {node['beat_title']}")
        print(f"  Beat Type: {node['beat_type']}")
    
    # Save as JSON
    with open("example_story_script.json", "w") as f:
        json.dump(script, f, indent=2)
    print(f"\n✓ Saved script to: example_story_script.json")


def example_5_generate_from_prompt():
    """Generate a story from an LLM prompt (stub mode)."""
    print("\n" + "="*60)
    print("EXAMPLE 5: LLM Story Generation")
    print("="*60)
    
    print("\nGenerating story from prompt...")
    print("  Prompt: 'A space explorer discovers an alien civilization'")
    print("  Genre: scifi")
    print("  Tone: epic")
    print("  Branches: 3")
    
    story = generate_story_from_llm(
        "A space explorer discovers an alien civilization",
        {
            'genre': 'scifi',
            'tone': 'epic',
            'branches': 3,
            'beats': 8
        }
    )
    
    print(f"\n✓ Generated: {story.title}")
    print(story.get_story_summary())
    
    # Save
    story.save_to_file("generated_story.json")
    print(f"\n✓ Saved to: generated_story.json")
    
    return story


def main():
    """Run all examples."""
    print("\n" + "╔" + "="*58 + "╗")
    print("║  Story Generator Examples                                  ║")
    print("╚" + "="*58 + "╝")
    
    # Example 1: Create a story manually
    story = example_1_create_manual_story()
    
    # Example 2: Play interactively
    example_2_play_interactive_story(story)
    
    # Example 3: Extract assets
    example_3_extract_assets(story)
    
    # Example 4: Convert to visual script
    example_4_convert_to_visual_script(story)
    
    # Example 5: Generate from LLM
    generated = example_5_generate_from_prompt()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("Generated files:")
    print("  - example_story.json (manually created story)")
    print("  - example_story_script.json (visual script representation)")
    print("  - generated_story.json (LLM-generated story)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
