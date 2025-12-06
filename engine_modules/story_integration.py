"""Story to Engine Integration - Convert StoryGraphs to executable engine systems."""

import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class StoryToVisualScript:
    """Convert StoryGraph to VisualScript node graphs."""
    
    @staticmethod
    def convert(story_graph, visual_script_class=None) -> Optional[Dict]:
        """Convert story beats to visual script nodes.
        
        Args:
            story_graph: StoryGraph instance
            visual_script_class: VisualScript class (for dependency injection)
            
        Returns:
            Dict of visual script data or None
        """
        try:
            # If no visual_script_class provided, use stub
            if visual_script_class is None:
                return StoryToVisualScript._create_stub_script(story_graph)
            
            # Create visual script
            vs = visual_script_class(f"story_{story_graph.title.replace(' ', '_')}")
            
            # Create a node for each beat
            node_map = {}
            for beat_id, beat in story_graph.beats.items():
                # Create node with beat properties
                node = vs.add_node(
                    "BeatNode",
                    x=len(node_map) * 300,
                    y=0,
                    beat_title=beat.title,
                    beat_type=beat.beat_type.value,
                    dialogue=beat.dialogue or "",
                    duration=beat.duration
                )
                node_map[beat_id] = node
            
            # Connect nodes based on story edges
            for from_id, to_id in story_graph.edges:
                from_node = node_map.get(from_id)
                to_node = node_map.get(to_id)
                if from_node and to_node:
                    vs.connect(from_node.outputs[0], to_node.inputs[0])
            
            return vs.to_dict()
        
        except Exception as e:
            logger.error(f"Failed to convert story to visual script: {e}")
            return None
    
    @staticmethod
    def _create_stub_script(story_graph) -> Dict:
        """Create a stub visual script representation."""
        return {
            'name': f"story_{story_graph.title.replace(' ', '_')}",
            'nodes': [
                {
                    'id': beat_id,
                    'type': 'BeatNode',
                    'beat_title': beat.title,
                    'beat_type': beat.beat_type.value,
                    'dialogue': beat.dialogue or '',
                    'duration': beat.duration,
                    'characters': beat.characters,
                    'x': i * 300,
                    'y': 0
                }
                for i, (beat_id, beat) in enumerate(story_graph.beats.items())
            ],
            'edges': [
                {'from': from_id, 'to': to_id}
                for from_id, to_id in story_graph.edges
            ]
        }


class StoryToAnimation:
    """Generate animation cues from story beats."""
    
    @staticmethod
    def generate_animation_cues(beat, character_id: str) -> List[str]:
        """Generate animation names for a character in a beat.
        
        Args:
            beat: StoryBeat instance
            character_id: Character ID
            
        Returns:
            List of animation names
        """
        animations = []
        
        beat_type = beat.beat_type.value
        
        # Map beat types to animations
        animation_map = {
            'dialogue': ['talk', 'listen', 'react'],
            'action': ['walk', 'run', 'attack', 'dodge'],
            'climax': ['attack_intense', 'power_up', 'ultimate'],
            'exposition': ['idle', 'gesture', 'look_around'],
            'cinematic': ['walk', 'gesture', 'react_shocked'],
            'decision_point': ['idle_thinking', 'gesture_question'],
        }
        
        if beat_type in animation_map:
            animations.extend(animation_map[beat_type])
        
        # Add dialogue animations if present
        if beat.dialogue:
            animations.extend(['talk_loop', 'listen'])
        
        return animations or ['idle']


class StoryToAssets:
    """Generate asset requirements from story."""
    
    @staticmethod
    def extract_asset_requirements(story_graph) -> Dict[str, List[str]]:
        """Extract required assets from story.
        
        Args:
            story_graph: StoryGraph instance
            
        Returns:
            Dict mapping asset types to required asset tags
        """
        requirements = {
            'characters': [],
            'animations': [],
            'skyboxes': [],
            'sfx': [],
            'music': [],
            'props': [],
            'materials': []
        }
        
        # Characters from story
        for char in story_graph.characters.values():
            requirements['characters'].append(char.name.lower())
            requirements['animations'].extend(char.animations)
        
        # Infer asset needs from beat descriptions
        for beat in story_graph.beats.values():
            desc = beat.description.lower()
            
            # Simple keyword matching
            if any(word in desc for word in ['forest', 'tree', 'nature', 'outdoor']):
                requirements['skyboxes'].append('clear_skies')
                requirements['materials'].extend(['organic_bark', 'organic_leaf'])
            
            if any(word in desc for word in ['night', 'dark', 'shadow']):
                requirements['skyboxes'].append('sunset_glow')
            
            if any(word in desc for word in ['fight', 'battle', 'combat']):
                requirements['sfx'].append('combat_hit')
                requirements['sfx'].append('power_up')
            
            if any(word in desc for word in ['dialogue', 'talk', 'speak']):
                requirements['sfx'].append('ui_confirm')
        
        return requirements
    
    @staticmethod
    def get_asset_import_commands(requirements: Dict[str, List[str]]) -> List[Dict]:
        """Generate asset import commands.
        
        Args:
            requirements: Asset requirements dict
            
        Returns:
            List of import command dicts
        """
        commands = []
        
        for asset_type, assets in requirements.items():
            for asset_name in assets:
                commands.append({
                    'asset_type': asset_type,
                    'asset_name': asset_name,
                    'quality_tier': 'hd'
                })
        
        return commands


class StoryRenderer:
    """Render story visually using engine systems."""
    
    def __init__(self, deferred_renderer=None, animation_controller=None, 
                 asset_pipeline=None):
        """Initialize story renderer.
        
        Args:
            deferred_renderer: DeferredRenderer instance
            animation_controller: AnimationController instance
            asset_pipeline: AssetPipeline instance
        """
        self.deferred_renderer = deferred_renderer
        self.animation_controller = animation_controller
        self.asset_pipeline = asset_pipeline
        self.current_beat = None
    
    def setup_beat_scene(self, beat) -> None:
        """Configure scene for a story beat.
        
        Args:
            beat: StoryBeat instance
        """
        self.current_beat = beat
        
        # Apply visual settings
        if beat.visual_settings and self.deferred_renderer:
            lighting = beat.visual_settings.get('lighting', {})
            if lighting:
                logger.info(f"Applying lighting: {lighting}")
        
        # Load animation cues
        if self.animation_controller:
            for char_id in beat.characters:
                animations = StoryToAnimation.generate_animation_cues(beat, char_id)
                for anim_name in animations:
                    try:
                        self.animation_controller.load_animation(anim_name, "")
                    except Exception as e:
                        logger.debug(f"Could not load animation {anim_name}: {e}")
    
    def play_beat(self, beat, duration: Optional[float] = None) -> float:
        """Play a story beat.
        
        Args:
            beat: StoryBeat instance
            duration: Override duration
            
        Returns:
            Actual duration played
        """
        actual_duration = duration or beat.duration
        
        self.setup_beat_scene(beat)
        
        if beat.dialogue and self.animation_controller:
            logger.info(f"Playing dialogue: {beat.dialogue}")
        
        logger.info(f"Playing beat '{beat.title}' for {actual_duration}s")
        
        return actual_duration
    
    def transition_to_beat(self, from_beat, to_beat, 
                          transition_time: float = 1.0) -> None:
        """Transition between beats.
        
        Args:
            from_beat: Current beat
            to_beat: Next beat
            transition_time: Transition duration in seconds
        """
        logger.info(f"Transitioning from '{from_beat.title}' to '{to_beat.title}'")
        self.setup_beat_scene(to_beat)


class InteractiveStoryPlayer:
    """Play interactive story with player choices."""
    
    def __init__(self, story_graph, story_renderer: Optional[StoryRenderer] = None):
        """Initialize story player.
        
        Args:
            story_graph: StoryGraph instance
            story_renderer: StoryRenderer instance
        """
        self.story = story_graph
        self.renderer = story_renderer
        self.current_beat_id = None
        self.visited_beats = []
        self.choices_made = {}
    
    def start(self) -> Optional[str]:
        """Start story playback.
        
        Returns:
            ID of first beat
        """
        if self.story.start_beats:
            self.current_beat_id = self.story.start_beats[0]
            self.visited_beats.append(self.current_beat_id)
            
            beat = self.story.beats.get(self.current_beat_id)
            if beat and self.renderer:
                self.renderer.play_beat(beat)
            
            logger.info(f"Story started at beat: {self.current_beat_id}")
            return self.current_beat_id
        
        return None
    
    def get_available_choices(self) -> List[Dict]:
        """Get player choices at current beat.
        
        Returns:
            List of available choice dicts
        """
        if not self.current_beat_id:
            return []
        
        choices = self.story.choices.get(self.current_beat_id, [])
        return [c.to_dict() for c in choices]
    
    def make_choice(self, choice_id: str) -> Optional[str]:
        """Make a player choice.
        
        Args:
            choice_id: ID of choice to make
            
        Returns:
            ID of next beat
        """
        if not self.current_beat_id:
            return None
        
        choices = self.story.choices.get(self.current_beat_id, [])
        choice = next((c for c in choices if c.id == choice_id), None)
        
        if not choice:
            logger.warning(f"Choice {choice_id} not found")
            return None
        
        next_beat_id = choice.target_beat_id
        
        # Transition
        current_beat = self.story.beats.get(self.current_beat_id)
        next_beat = self.story.beats.get(next_beat_id)
        
        if current_beat and next_beat and self.renderer:
            self.renderer.transition_to_beat(current_beat, next_beat)
            self.renderer.play_beat(next_beat)
        
        self.current_beat_id = next_beat_id
        self.visited_beats.append(next_beat_id)
        self.choices_made[self.current_beat_id] = choice_id
        
        logger.info(f"Player made choice: {choice.text} -> {next_beat_id}")
        
        return next_beat_id
    
    def advance_to_next(self) -> Optional[str]:
        """Automatically advance to next beat.
        
        Returns:
            ID of next beat or None if story ended
        """
        if not self.current_beat_id:
            return None
        
        # Find connected beats
        next_ids = [to_id for from_id, to_id in self.story.edges 
                   if from_id == self.current_beat_id]
        
        if not next_ids:
            logger.info("Story ended")
            return None
        
        next_beat_id = next_ids[0]
        current_beat = self.story.beats.get(self.current_beat_id)
        next_beat = self.story.beats.get(next_beat_id)
        
        if current_beat and next_beat and self.renderer:
            self.renderer.transition_to_beat(current_beat, next_beat)
            self.renderer.play_beat(next_beat)
        
        self.current_beat_id = next_beat_id
        self.visited_beats.append(next_beat_id)
        
        logger.info(f"Advanced to next beat: {next_beat_id}")
        
        return next_beat_id
    
    def get_story_progress(self) -> Dict:
        """Get current story progress.
        
        Returns:
            Dict with progress info
        """
        return {
            'current_beat_id': self.current_beat_id,
            'visited_beat_count': len(self.visited_beats),
            'total_beat_count': len(self.story.beats),
            'choices_made': self.choices_made,
            'completion_percent': (len(self.visited_beats) / len(self.story.beats) * 100) 
                                  if self.story.beats else 0
        }
