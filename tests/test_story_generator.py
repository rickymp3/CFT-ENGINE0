"""Tests for story generation system."""

import pytest
import json
import tempfile
from pathlib import Path

from engine_modules.story_generator import (
    StoryGraph, StoryBeat, Character, BeatType, CharacterRole,
    generate_story_from_llm, _generate_stub_story
)
from engine_modules.story_integration import (
    StoryToVisualScript, StoryToAnimation, StoryToAssets,
    StoryRenderer, InteractiveStoryPlayer
)


class TestStoryGraph:
    """Test StoryGraph core functionality."""
    
    def test_create_story(self):
        """Test story creation."""
        story = StoryGraph("Test Story")
        assert story.title == "Test Story"
        assert len(story.beats) == 0
        assert len(story.characters) == 0
    
    def test_add_character(self):
        """Test adding characters."""
        story = StoryGraph("Test")
        char = story.add_character("Hero", CharacterRole.PROTAGONIST, "Main hero")
        
        assert char.name == "Hero"
        assert char.role == CharacterRole.PROTAGONIST
        assert char.id in story.characters
    
    def test_add_beat(self):
        """Test adding beats."""
        story = StoryGraph("Test")
        beat = story.add_beat(BeatType.EXPOSITION, "Setup", "Story setup")
        
        assert beat.title == "Setup"
        assert beat.beat_type == BeatType.EXPOSITION
        assert beat.id in story.beats
    
    def test_connect_beats(self):
        """Test connecting beats."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Setup", "Setup")
        beat2 = story.add_beat(BeatType.CLIMAX, "Final", "Final battle")
        
        story.connect_beats(beat1.id, beat2.id)
        
        assert (beat1.id, beat2.id) in story.edges
    
    def test_add_choice(self):
        """Test adding choices."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.DECISION_POINT, "Choice", "Choose path")
        beat2 = story.add_beat(BeatType.RESOLUTION, "End", "Ending")
        
        choice = story.add_choice(beat1.id, "Go left", beat2.id, "Consequence")
        
        assert beat1.id in story.choices
        assert choice.id in [c.id for c in story.choices[beat1.id]]
    
    def test_save_and_load(self):
        """Test saving and loading story."""
        # Create story
        story = StoryGraph("Test Story")
        story.description = "A test story"
        story.genre = "fantasy"
        story.tone = "dramatic"
        
        char = story.add_character("Hero", CharacterRole.PROTAGONIST, "The hero")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Beginning")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "Ending")
        story.connect_beats(beat1.id, beat2.id)
        
        # Save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            story.save_to_file(temp_path)
            
            # Load
            loaded = StoryGraph.load_from_file(temp_path)
            
            assert loaded.title == "Test Story"
            assert loaded.description == "A test story"
            assert loaded.genre == "fantasy"
            assert len(loaded.characters) == 1
            assert len(loaded.beats) == 2
            assert len(loaded.edges) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_story_summary(self):
        """Test story summary generation."""
        story = StoryGraph("Test")
        story.add_character("Hero", CharacterRole.PROTAGONIST, "Hero")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Start")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "End")
        story.connect_beats(beat1.id, beat2.id)
        
        summary = story.get_story_summary()
        
        assert "Test" in summary
        assert "1" in summary  # 1 character


class TestStubStoryGeneration:
    """Test stub story generation."""
    
    def test_generate_stub_story(self):
        """Test stub story creation."""
        constraints = {'genre': 'fantasy', 'tone': 'dramatic'}
        story = _generate_stub_story("A hero's journey", constraints)
        
        assert story.title.startswith("Generated Story")
        assert len(story.characters) >= 2
        assert len(story.beats) == 4
        assert story.genre == 'fantasy'
    
    def test_story_from_llm_without_api_key(self):
        """Test LLM story generation without API key."""
        import os
        old_key = os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            story = generate_story_from_llm(
                "A hero's quest",
                {'genre': 'fantasy', 'tone': 'epic'}
            )
            
            assert story is not None
            assert len(story.beats) > 0
        finally:
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key


class TestStoryToVisualScript:
    """Test story to visual script conversion."""
    
    def test_create_stub_script(self):
        """Test stub script creation."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Start")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "End")
        story.connect_beats(beat1.id, beat2.id)
        
        script = StoryToVisualScript._create_stub_script(story)
        
        assert 'nodes' in script
        assert 'edges' in script
        assert len(script['nodes']) == 2
        assert len(script['edges']) == 1
    
    def test_beat_to_node_conversion(self):
        """Test beat to node mapping."""
        story = StoryGraph("Test")
        beat = story.add_beat(BeatType.DIALOGUE, "Talk", "Character speaks", duration=10.0)
        beat.dialogue = "Hello world"
        
        script = StoryToVisualScript._create_stub_script(story)
        node = script['nodes'][0]
        
        assert node['beat_title'] == "Talk"
        assert node['beat_type'] == "dialogue"
        assert node['dialogue'] == "Hello world"
        assert node['duration'] == 10.0


class TestStoryToAnimation:
    """Test animation cue generation."""
    
    def test_generate_dialogue_animations(self):
        """Test animation generation for dialogue."""
        beat = StoryBeat("id", BeatType.DIALOGUE, "Talk", "Speak", [], dialogue="Hello")
        
        anims = StoryToAnimation.generate_animation_cues(beat, "char1")
        
        assert any('talk' in a for a in anims)
        assert any('listen' in a for a in anims)
    
    def test_generate_action_animations(self):
        """Test animation generation for action."""
        beat = StoryBeat("id", BeatType.ACTION, "Fight", "Combat sequence", [])
        
        anims = StoryToAnimation.generate_animation_cues(beat, "char1")
        
        assert any('walk' in a or 'run' in a or 'attack' in a for a in anims)
    
    def test_generate_climax_animations(self):
        """Test animation generation for climax."""
        beat = StoryBeat("id", BeatType.CLIMAX, "Battle", "Final showdown", [])
        
        anims = StoryToAnimation.generate_animation_cues(beat, "char1")
        
        assert any('attack' in a or 'power' in a for a in anims)


class TestStoryToAssets:
    """Test asset requirement extraction."""
    
    def test_extract_character_assets(self):
        """Test extracting character asset requirements."""
        story = StoryGraph("Test")
        story.add_character("Hero", CharacterRole.PROTAGONIST, "The hero")
        story.add_character("Villain", CharacterRole.ANTAGONIST, "The villain")
        
        reqs = StoryToAssets.extract_asset_requirements(story)
        
        assert 'hero' in reqs['characters']
        assert 'villain' in reqs['characters']
    
    def test_extract_environment_assets(self):
        """Test extracting environment assets from descriptions."""
        story = StoryGraph("Test")
        beat = story.add_beat(
            BeatType.EXPOSITION,
            "Forest",
            "A dark forest with tall trees and leaves"
        )
        
        reqs = StoryToAssets.extract_asset_requirements(story)
        
        # Should detect forest/nature/leaves
        assert len(reqs['materials']) > 0 or len(reqs['skyboxes']) > 0
    
    def test_get_import_commands(self):
        """Test generating import commands."""
        reqs = {
            'characters': ['hero', 'villain'],
            'animations': ['walk', 'run'],
            'materials': ['wood', 'stone']
        }
        
        commands = StoryToAssets.get_asset_import_commands(reqs)
        
        assert len(commands) > 0
        assert any(c['asset_type'] == 'characters' for c in commands)
        assert any(c['asset_type'] == 'materials' for c in commands)


class TestStoryRenderer:
    """Test story rendering."""
    
    def test_create_renderer(self):
        """Test renderer creation."""
        renderer = StoryRenderer()
        assert renderer.current_beat is None
    
    def test_setup_beat_scene(self):
        """Test scene setup for a beat."""
        renderer = StoryRenderer()
        beat = StoryBeat("id", BeatType.EXPOSITION, "Setup", "Begin", [])
        beat.visual_settings = {'lighting': {'intensity': 0.8}}
        
        renderer.setup_beat_scene(beat)
        
        assert renderer.current_beat == beat
    
    def test_play_beat(self):
        """Test playing a beat."""
        renderer = StoryRenderer()
        beat = StoryBeat("id", BeatType.ACTION, "Fight", "Combat", [], duration=5.0)
        
        duration = renderer.play_beat(beat)
        
        assert duration == 5.0
    
    def test_transition_between_beats(self):
        """Test transitioning between beats."""
        renderer = StoryRenderer()
        beat1 = StoryBeat("1", BeatType.EXPOSITION, "Start", "Start", [])
        beat2 = StoryBeat("2", BeatType.CLIMAX, "End", "End", [])
        
        # Should not raise
        renderer.transition_to_beat(beat1, beat2)


class TestInteractiveStoryPlayer:
    """Test interactive story playback."""
    
    def test_start_story(self):
        """Test starting story playback."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Beginning")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "Ending")
        story.set_start_beats([beat1.id])
        story.set_end_beats([beat2.id])
        
        player = InteractiveStoryPlayer(story)
        start_beat = player.start()
        
        assert start_beat == beat1.id
        assert beat1.id in player.visited_beats
    
    def test_advance_automatically(self):
        """Test automatic advancement."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Start")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "End")
        story.connect_beats(beat1.id, beat2.id)
        story.set_start_beats([beat1.id])
        
        player = InteractiveStoryPlayer(story)
        player.start()
        next_beat = player.advance_to_next()
        
        assert next_beat == beat2.id
        assert beat2.id in player.visited_beats
    
    def test_make_choice(self):
        """Test player choice making."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.DECISION_POINT, "Choice", "Choose")
        beat2 = story.add_beat(BeatType.RESOLUTION, "Path1", "Path 1")
        beat3 = story.add_beat(BeatType.RESOLUTION, "Path2", "Path 2")
        
        choice = story.add_choice(beat1.id, "Go left", beat2.id)
        story.set_start_beats([beat1.id])
        
        player = InteractiveStoryPlayer(story)
        player.start()
        result = player.make_choice(choice.id)
        
        assert result == beat2.id
        assert beat2.id in player.visited_beats
    
    def test_get_available_choices(self):
        """Test getting available choices."""
        story = StoryGraph("Test")
        beat = story.add_beat(BeatType.DECISION_POINT, "Choice", "Choose")
        beat2 = story.add_beat(BeatType.RESOLUTION, "End", "End")
        
        story.add_choice(beat.id, "Option A", beat2.id)
        story.add_choice(beat.id, "Option B", beat2.id)
        story.set_start_beats([beat.id])
        
        player = InteractiveStoryPlayer(story)
        player.start()
        choices = player.get_available_choices()
        
        assert len(choices) == 2
        assert any(c['text'] == "Option A" for c in choices)
    
    def test_story_progress(self):
        """Test progress tracking."""
        story = StoryGraph("Test")
        beat1 = story.add_beat(BeatType.EXPOSITION, "Start", "Start")
        beat2 = story.add_beat(BeatType.CLIMAX, "End", "End")
        story.connect_beats(beat1.id, beat2.id)
        story.set_start_beats([beat1.id])
        
        player = InteractiveStoryPlayer(story)
        player.start()
        
        progress = player.get_story_progress()
        
        assert progress['current_beat_id'] == beat1.id
        assert progress['visited_beat_count'] == 1
        assert progress['total_beat_count'] == 2
