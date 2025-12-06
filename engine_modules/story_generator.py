"""Story Graph Generator for narrative-driven games.

Features:
- Generate branching narrative graphs from text prompts
- Convert story beats into visual scripts
- Integrate with animation and asset systems
- Support for character, dialogue, and cinematic generation
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class BeatType(Enum):
    """Types of narrative beats."""
    EXPOSITION = "exposition"
    INCITING_INCIDENT = "inciting_incident"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"
    DIALOGUE = "dialogue"
    ACTION = "action"
    CINEMATIC = "cinematic"
    DECISION_POINT = "decision_point"


class CharacterRole(Enum):
    """Character roles in narrative."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORT = "support"
    NPC = "npc"


@dataclass
class Character:
    """Story character definition."""
    id: str
    name: str
    role: CharacterRole
    description: str
    animations: List[str] = field(default_factory=list)
    dialogue_style: str = "neutral"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.value,
            'description': self.description,
            'animations': self.animations,
            'dialogue_style': self.dialogue_style
        }


@dataclass
class StoryBeat:
    """Single narrative beat/event in the story."""
    id: str
    beat_type: BeatType
    title: str
    description: str
    characters: List[str]  # Character IDs
    dialogue: Optional[str] = None
    duration: float = 5.0  # Estimated duration in seconds
    animation_cues: List[str] = field(default_factory=list)
    visual_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'beat_type': self.beat_type.value,
            'title': self.title,
            'description': self.description,
            'characters': self.characters,
            'dialogue': self.dialogue,
            'duration': self.duration,
            'animation_cues': self.animation_cues,
            'visual_settings': self.visual_settings
        }


@dataclass
class StoryChoice:
    """Player choice in story."""
    id: str
    text: str
    target_beat_id: str
    consequence: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StoryGraph:
    """Directed acyclic graph representing a branching narrative."""
    
    def __init__(self, title: str = "Untitled Story"):
        """Initialize story graph.
        
        Args:
            title: Story title
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = ""
        self.genre: str = "general"
        self.tone: str = "neutral"
        
        # Graph structure
        self.beats: Dict[str, StoryBeat] = {}
        self.characters: Dict[str, Character] = {}
        self.edges: List[Tuple[str, str]] = []  # (from_beat_id, to_beat_id)
        self.choices: Dict[str, List[StoryChoice]] = {}  # beat_id -> choices
        
        # Entry/exit nodes
        self.start_beats: List[str] = []
        self.end_beats: List[str] = []
        
        logger.info(f"Story graph created: {title}")
    
    def add_character(self, name: str, role: CharacterRole, 
                     description: str) -> Character:
        """Add a character to the story.
        
        Args:
            name: Character name
            role: Character role
            description: Character description
            
        Returns:
            Created Character instance
        """
        char_id = str(uuid.uuid4())
        character = Character(char_id, name, role, description)
        self.characters[char_id] = character
        logger.debug(f"Added character: {name} ({role.value})")
        return character
    
    def add_beat(self, beat_type: BeatType, title: str, description: str,
                character_ids: List[str] = None, duration: float = 5.0) -> StoryBeat:
        """Add a narrative beat.
        
        Args:
            beat_type: Type of beat
            title: Beat title
            description: Beat description
            character_ids: IDs of characters involved
            duration: Estimated duration in seconds
            
        Returns:
            Created StoryBeat instance
        """
        beat_id = str(uuid.uuid4())
        beat = StoryBeat(beat_id, beat_type, title, description, 
                        character_ids or [], duration=duration)
        self.beats[beat_id] = beat
        logger.debug(f"Added beat: {title} ({beat_type.value})")
        return beat
    
    def connect_beats(self, from_id: str, to_id: str) -> None:
        """Connect two beats with an edge.
        
        Args:
            from_id: Source beat ID
            to_id: Target beat ID
        """
        if from_id in self.beats and to_id in self.beats:
            self.edges.append((from_id, to_id))
            logger.debug(f"Connected beats: {from_id} -> {to_id}")
    
    def add_choice(self, beat_id: str, choice_text: str, 
                  target_beat_id: str, consequence: str = "") -> StoryChoice:
        """Add a player choice at a beat.
        
        Args:
            beat_id: Beat with choice
            choice_text: Choice text shown to player
            target_beat_id: Beat to transition to
            consequence: Effect of this choice
            
        Returns:
            Created StoryChoice instance
        """
        choice_id = str(uuid.uuid4())
        choice = StoryChoice(choice_id, choice_text, target_beat_id, consequence)
        
        if beat_id not in self.choices:
            self.choices[beat_id] = []
        
        self.choices[beat_id].append(choice)
        logger.debug(f"Added choice at beat {beat_id}: {choice_text}")
        return choice
    
    def set_start_beats(self, beat_ids: List[str]) -> None:
        """Set starting beats."""
        self.start_beats = beat_ids
    
    def set_end_beats(self, beat_ids: List[str]) -> None:
        """Set ending beats."""
        self.end_beats = beat_ids
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'genre': self.genre,
            'tone': self.tone,
            'beats': {bid: beat.to_dict() for bid, beat in self.beats.items()},
            'characters': {cid: char.to_dict() for cid, char in self.characters.items()},
            'edges': self.edges,
            'choices': {bid: [c.to_dict() for c in choices] 
                       for bid, choices in self.choices.items()},
            'start_beats': self.start_beats,
            'end_beats': self.end_beats
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save story graph to JSON file.
        
        Args:
            filepath: Output file path
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Story graph saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save story graph: {e}")
    
    @staticmethod
    def load_from_file(filepath: str) -> 'StoryGraph':
        """Load story graph from JSON file.
        
        Args:
            filepath: Input file path
            
        Returns:
            Loaded StoryGraph instance
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            graph = StoryGraph(data.get('title', 'Loaded Story'))
            graph.id = data.get('id')
            graph.description = data.get('description', '')
            graph.genre = data.get('genre', 'general')
            graph.tone = data.get('tone', 'neutral')
            
            # Load characters
            for cid, cdata in data.get('characters', {}).items():
                char = Character(
                    cid, cdata['name'], 
                    CharacterRole[cdata['role'].upper()],
                    cdata['description']
                )
                graph.characters[cid] = char
            
            # Load beats
            for bid, bdata in data.get('beats', {}).items():
                beat = StoryBeat(
                    bid,
                    BeatType[bdata['beat_type'].upper()],
                    bdata['title'],
                    bdata['description'],
                    bdata.get('characters', []),
                    bdata.get('dialogue'),
                    bdata.get('duration', 5.0)
                )
                graph.beats[bid] = beat
            
            # Load edges
            graph.edges = data.get('edges', [])
            graph.start_beats = data.get('start_beats', [])
            graph.end_beats = data.get('end_beats', [])
            
            logger.info(f"Story graph loaded from {filepath}")
            return graph
        except Exception as e:
            logger.error(f"Failed to load story graph: {e}")
            return StoryGraph()
    
    def get_story_summary(self) -> str:
        """Generate a text summary of the story."""
        summary = f"Story: {self.title}\n"
        summary += f"Genre: {self.genre} | Tone: {self.tone}\n"
        summary += f"Characters: {len(self.characters)}\n"
        summary += f"Beats: {len(self.beats)}\n"
        summary += f"Branches: {len([e for e in self.edges if any(len(self.choices.get(from_id, [])) > 0 for from_id, _ in [e])])}\n"
        return summary


def generate_story_from_llm(prompt: str, constraints: Dict[str, Any]) -> StoryGraph:
    """Generate a story graph from an LLM response.
    
    This function calls an LLM to generate narrative structure
    and parses the response into a StoryGraph.
    
    Args:
        prompt: User's story prompt
        constraints: Generation constraints (starts, ends, branches, tone, genre)
        
    Returns:
        Generated StoryGraph instance
    """
    try:
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; generating stub story")
            return _generate_stub_story(prompt, constraints)
        
        import openai
        openai.api_key = api_key
        
        genre = constraints.get('genre', 'fantasy')
        tone = constraints.get('tone', 'dramatic')
        num_branches = constraints.get('branches', 3)
        num_beats = constraints.get('beats', 7)
        
        system_prompt = f"""You are a narrative designer. Generate a story outline in JSON format.
        
Create a branching story with:
- {num_beats} narrative beats
- {num_branches} major decision points
- Genre: {genre}
- Tone: {tone}

Return ONLY valid JSON with this structure:
{{
  "title": "story title",
  "description": "brief description",
  "characters": [
    {{"name": "character name", "role": "protagonist|antagonist|support|npc", "description": "..."}}
  ],
  "beats": [
    {{"title": "beat title", "type": "exposition|inciting_incident|rising_action|climax|falling_action|resolution|dialogue|action", "description": "...", "duration": 5.0}}
  ],
  "flow": ["beat1", "beat2", "beat3", ...]
}}"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response['choices'][0]['message']['content']
        data = json.loads(content)
        
        return _build_story_graph_from_data(data, constraints)
    
    except ImportError:
        logger.warning("openai module not installed; using stub story")
        return _generate_stub_story(prompt, constraints)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}; using stub story")
        return _generate_stub_story(prompt, constraints)


def _build_story_graph_from_data(data: Dict, constraints: Dict) -> StoryGraph:
    """Build StoryGraph from LLM JSON response."""
    graph = StoryGraph(data.get('title', 'Generated Story'))
    graph.description = data.get('description', '')
    graph.genre = constraints.get('genre', 'fantasy')
    graph.tone = constraints.get('tone', 'dramatic')
    
    # Add characters
    char_map = {}
    for char_data in data.get('characters', []):
        char = graph.add_character(
            char_data['name'],
            CharacterRole[char_data['role'].upper()] if char_data['role'].upper() in CharacterRole.__members__ else CharacterRole.NPC,
            char_data.get('description', '')
        )
        char_map[char_data['name']] = char.id
    
    # Add beats
    beat_map = {}
    for beat_data in data.get('beats', []):
        beat = graph.add_beat(
            BeatType[beat_data['type'].upper()] if beat_data['type'].upper() in BeatType.__members__ else BeatType.ACTION,
            beat_data['title'],
            beat_data.get('description', ''),
            [],
            beat_data.get('duration', 5.0)
        )
        beat_map[beat_data['title']] = beat.id
    
    # Connect beats
    flow = data.get('flow', [])
    for i in range(len(flow) - 1):
        if flow[i] in beat_map and flow[i+1] in beat_map:
            graph.connect_beats(beat_map[flow[i]], beat_map[flow[i+1]])
    
    # Set start/end
    if flow:
        graph.set_start_beats([beat_map[flow[0]]])
        graph.set_end_beats([beat_map[flow[-1]]])
    
    return graph


def _generate_stub_story(prompt: str, constraints: Dict) -> StoryGraph:
    """Generate a minimal stub story for testing."""
    graph = StoryGraph("Generated Story: " + prompt[:30])
    graph.description = prompt
    graph.genre = constraints.get('genre', 'fantasy')
    graph.tone = constraints.get('tone', 'dramatic')
    
    # Minimal characters
    hero = graph.add_character("Hero", CharacterRole.PROTAGONIST, "Main character")
    villain = graph.add_character("Antagonist", CharacterRole.ANTAGONIST, "Opposition force")
    
    # Minimal beats
    beat1 = graph.add_beat(BeatType.EXPOSITION, "Setup", prompt, [hero.id])
    beat2 = graph.add_beat(BeatType.INCITING_INCIDENT, "Conflict", "Something goes wrong", [hero.id, villain.id])
    beat3 = graph.add_beat(BeatType.CLIMAX, "Confrontation", "Final battle", [hero.id, villain.id])
    beat4 = graph.add_beat(BeatType.RESOLUTION, "Ending", "Resolution", [hero.id])
    
    # Connect
    graph.connect_beats(beat1.id, beat2.id)
    graph.connect_beats(beat2.id, beat3.id)
    graph.connect_beats(beat3.id, beat4.id)
    
    graph.set_start_beats([beat1.id])
    graph.set_end_beats([beat4.id])
    
    return graph
