"""
CFT-ENGINE0 Save/Load and State Serialization System
Comprehensive save system for scenes, physics, AI, and player data
"""

import json
import pickle
import gzip
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from panda3d.core import Point3, Vec3, Quat, NodePath
from panda3d.bullet import BulletRigidBodyNode, BulletWorld
import hashlib


# ==================== Serializers ====================

class Vector3Serializer:
    """Serialize Panda3D vectors"""
    
    @staticmethod
    def serialize(vec: Vec3) -> List[float]:
        return [vec.x, vec.y, vec.z]
    
    @staticmethod
    def deserialize(data: List[float]) -> Vec3:
        return Vec3(data[0], data[1], data[2])


class Point3Serializer:
    """Serialize Panda3D points"""
    
    @staticmethod
    def serialize(point: Point3) -> List[float]:
        return [point.x, point.y, point.z]
    
    @staticmethod
    def deserialize(data: List[float]) -> Point3:
        return Point3(data[0], data[1], data[2])


class QuatSerializer:
    """Serialize quaternions"""
    
    @staticmethod
    def serialize(quat: Quat) -> List[float]:
        return [quat.get_r(), quat.get_i(), quat.get_j(), quat.get_k()]
    
    @staticmethod
    def deserialize(data: List[float]) -> Quat:
        q = Quat()
        q.set_r(data[0])
        q.set_i(data[1])
        q.set_j(data[2])
        q.set_k(data[3])
        return q


# ==================== Scene Serialization ====================

class SceneObject:
    """Serializable scene object"""
    
    def __init__(self, name: str, model_path: str = ""):
        self.name = name
        self.model_path = model_path
        self.position = Point3(0, 0, 0)
        self.rotation = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)
        self.tags: Dict[str, Any] = {}
        self.components: Dict[str, Dict] = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'model_path': self.model_path,
            'position': Point3Serializer.serialize(self.position),
            'rotation': Vector3Serializer.serialize(self.rotation),
            'scale': Vector3Serializer.serialize(self.scale),
            'tags': self.tags,
            'components': self.components
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'SceneObject':
        """Create from dictionary"""
        obj = SceneObject(data['name'], data.get('model_path', ''))
        obj.position = Point3Serializer.deserialize(data['position'])
        obj.rotation = Vector3Serializer.deserialize(data['rotation'])
        obj.scale = Vector3Serializer.deserialize(data['scale'])
        obj.tags = data.get('tags', {})
        obj.components = data.get('components', {})
        return obj
    
    @staticmethod
    def from_node_path(node_path: NodePath) -> 'SceneObject':
        """Create from Panda3D NodePath"""
        obj = SceneObject(node_path.get_name())
        obj.position = node_path.get_pos()
        obj.rotation = node_path.get_hpr()
        obj.scale = node_path.get_scale()
        
        # Try to get model path from tag
        if node_path.has_tag('model_path'):
            obj.model_path = node_path.get_tag('model_path')
        
        return obj


class SceneSerializer:
    """Serializes entire scenes"""
    
    def __init__(self):
        self.objects: List[SceneObject] = []
        self.metadata: Dict = {}
    
    def add_object(self, obj: SceneObject):
        """Add object to scene"""
        self.objects.append(obj)
    
    def scan_scene(self, root: NodePath, recursive: bool = True):
        """Scan scene graph and add all objects"""
        self.objects.clear()
        
        if recursive:
            for child in root.get_children():
                obj = SceneObject.from_node_path(child)
                self.add_object(obj)
                
                # Recursively scan children
                for subchild in child.get_children():
                    subobj = SceneObject.from_node_path(subchild)
                    self.add_object(subobj)
    
    def to_dict(self) -> Dict:
        """Convert scene to dictionary"""
        return {
            'metadata': self.metadata,
            'objects': [obj.to_dict() for obj in self.objects]
        }
    
    def from_dict(self, data: Dict):
        """Load scene from dictionary"""
        self.metadata = data.get('metadata', {})
        self.objects = [SceneObject.from_dict(obj_data) for obj_data in data.get('objects', [])]
    
    def save_to_file(self, filename: str):
        """Save scene to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filename: str):
        """Load scene from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            self.from_dict(data)


# ==================== Physics Serialization ====================

class PhysicsState:
    """Serializable physics object state"""
    
    def __init__(self):
        self.name = ""
        self.position = Point3(0, 0, 0)
        self.rotation = Quat()
        self.linear_velocity = Vec3(0, 0, 0)
        self.angular_velocity = Vec3(0, 0, 0)
        self.mass = 1.0
        self.active = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'position': Point3Serializer.serialize(self.position),
            'rotation': QuatSerializer.serialize(self.rotation),
            'linear_velocity': Vector3Serializer.serialize(self.linear_velocity),
            'angular_velocity': Vector3Serializer.serialize(self.angular_velocity),
            'mass': self.mass,
            'active': self.active
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'PhysicsState':
        """Create from dictionary"""
        state = PhysicsState()
        state.name = data['name']
        state.position = Point3Serializer.deserialize(data['position'])
        state.rotation = QuatSerializer.deserialize(data['rotation'])
        state.linear_velocity = Vector3Serializer.deserialize(data['linear_velocity'])
        state.angular_velocity = Vector3Serializer.deserialize(data['angular_velocity'])
        state.mass = data.get('mass', 1.0)
        state.active = data.get('active', True)
        return state


class PhysicsSerializer:
    """Serializes physics world state"""
    
    def __init__(self):
        self.states: List[PhysicsState] = []
    
    def capture_world(self, physics_world: BulletWorld):
        """Capture current physics world state"""
        self.states.clear()
        
        for node in physics_world.get_rigid_bodies():
            state = PhysicsState()
            state.name = node.get_name()
            
            # Get transform
            trans = node.get_transform()
            state.position = trans.get_pos()
            state.rotation = trans.get_quat()
            
            # Get velocities
            state.linear_velocity = node.get_linear_velocity()
            state.angular_velocity = node.get_angular_velocity()
            state.mass = node.get_mass()
            state.active = node.is_active()
            
            self.states.append(state)
    
    def restore_world(self, physics_world: BulletWorld, node_lookup: Dict[str, NodePath]):
        """Restore physics world state"""
        for state in self.states:
            if state.name in node_lookup:
                node_path = node_lookup[state.name]
                physics_node = node_path.node()
                
                if isinstance(physics_node, BulletRigidBodyNode):
                    # Restore transform
                    node_path.set_pos(state.position)
                    node_path.set_quat(state.rotation)
                    
                    # Restore velocities
                    physics_node.set_linear_velocity(state.linear_velocity)
                    physics_node.set_angular_velocity(state.angular_velocity)
                    physics_node.set_active(state.active)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'states': [state.to_dict() for state in self.states]
        }
    
    def from_dict(self, data: Dict):
        """Load from dictionary"""
        self.states = [PhysicsState.from_dict(s) for s in data.get('states', [])]


# ==================== AI State Serialization ====================

class AIState:
    """Serializable AI agent state"""
    
    def __init__(self):
        self.name = ""
        self.position = Point3(0, 0, 0)
        self.target_position: Optional[Point3] = None
        self.path: List[Point3] = []
        self.current_path_index = 0
        self.blackboard: Dict = {}
        self.behavior_tree_state: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'position': Point3Serializer.serialize(self.position),
            'target_position': Point3Serializer.serialize(self.target_position) if self.target_position else None,
            'path': [Point3Serializer.serialize(p) for p in self.path],
            'current_path_index': self.current_path_index,
            'blackboard': self.blackboard,
            'behavior_tree_state': self.behavior_tree_state
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'AIState':
        """Create from dictionary"""
        state = AIState()
        state.name = data['name']
        state.position = Point3Serializer.deserialize(data['position'])
        
        if data.get('target_position'):
            state.target_position = Point3Serializer.deserialize(data['target_position'])
        
        state.path = [Point3Serializer.deserialize(p) for p in data.get('path', [])]
        state.current_path_index = data.get('current_path_index', 0)
        state.blackboard = data.get('blackboard', {})
        state.behavior_tree_state = data.get('behavior_tree_state', {})
        
        return state


# ==================== Player Data ====================

class PlayerData:
    """Player-specific save data"""
    
    def __init__(self):
        self.name = "Player"
        self.position = Point3(0, 0, 0)
        self.rotation = Vec3(0, 0, 0)
        self.health = 100.0
        self.inventory: Dict[str, int] = {}
        self.stats: Dict[str, float] = {}
        self.flags: Dict[str, bool] = {}
        self.quest_progress: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'position': Point3Serializer.serialize(self.position),
            'rotation': Vector3Serializer.serialize(self.rotation),
            'health': self.health,
            'inventory': self.inventory,
            'stats': self.stats,
            'flags': self.flags,
            'quest_progress': self.quest_progress
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'PlayerData':
        """Create from dictionary"""
        player = PlayerData()
        player.name = data.get('name', 'Player')
        player.position = Point3Serializer.deserialize(data['position'])
        player.rotation = Vector3Serializer.deserialize(data['rotation'])
        player.health = data.get('health', 100.0)
        player.inventory = data.get('inventory', {})
        player.stats = data.get('stats', {})
        player.flags = data.get('flags', {})
        player.quest_progress = data.get('quest_progress', {})
        return player


# ==================== Complete Save System ====================

class SaveSlot:
    """Represents a save game slot"""
    
    def __init__(self, slot_id: int):
        self.slot_id = slot_id
        self.timestamp = datetime.now()
        self.scene_name = ""
        self.player_name = ""
        self.playtime = 0.0  # seconds
        self.save_version = "1.0"
        
        # Serializers
        self.scene = SceneSerializer()
        self.physics = PhysicsSerializer()
        self.ai_states: List[AIState] = []
        self.player_data = PlayerData()
        
        # Custom data
        self.custom_data: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert save to dictionary"""
        return {
            'slot_id': self.slot_id,
            'timestamp': self.timestamp.isoformat(),
            'scene_name': self.scene_name,
            'player_name': self.player_name,
            'playtime': self.playtime,
            'save_version': self.save_version,
            'scene': self.scene.to_dict(),
            'physics': self.physics.to_dict(),
            'ai_states': [ai.to_dict() for ai in self.ai_states],
            'player_data': self.player_data.to_dict(),
            'custom_data': self.custom_data
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'SaveSlot':
        """Load save from dictionary"""
        slot = SaveSlot(data['slot_id'])
        slot.timestamp = datetime.fromisoformat(data['timestamp'])
        slot.scene_name = data.get('scene_name', '')
        slot.player_name = data.get('player_name', '')
        slot.playtime = data.get('playtime', 0.0)
        slot.save_version = data.get('save_version', '1.0')
        
        slot.scene.from_dict(data['scene'])
        slot.physics.from_dict(data['physics'])
        slot.ai_states = [AIState.from_dict(ai) for ai in data.get('ai_states', [])]
        slot.player_data = PlayerData.from_dict(data['player_data'])
        slot.custom_data = data.get('custom_data', {})
        
        return slot


class SaveSystem:
    """Complete save/load system"""
    
    def __init__(self, save_directory: str = "saves"):
        self.save_dir = Path(save_directory)
        self.save_dir.mkdir(exist_ok=True)
        
        self.current_slot: Optional[SaveSlot] = None
        self.autosave_interval = 300.0  # 5 minutes
        self.autosave_timer = 0.0
        self.autosave_enabled = True
        
        # Compression
        self.use_compression = True
    
    def _get_save_path(self, slot_id: int) -> Path:
        """Get path for save slot"""
        extension = '.sav.gz' if self.use_compression else '.sav'
        return self.save_dir / f"save_{slot_id:03d}{extension}"
    
    def create_save(self, slot_id: int) -> SaveSlot:
        """Create new save slot"""
        self.current_slot = SaveSlot(slot_id)
        return self.current_slot
    
    def save_game(self, slot: SaveSlot, filename: Optional[str] = None):
        """Save game to file"""
        if filename is None:
            filename = str(self._get_save_path(slot.slot_id))
        
        data = slot.to_dict()
        json_data = json.dumps(data, indent=2)
        
        if self.use_compression:
            with gzip.open(filename, 'wt', encoding='utf-8') as f:
                f.write(json_data)
        else:
            with open(filename, 'w') as f:
                f.write(json_data)
        
        print(f"Game saved to slot {slot.slot_id}")
    
    def load_game(self, slot_id: int) -> Optional[SaveSlot]:
        """Load game from file"""
        filename = str(self._get_save_path(slot_id))
        
        if not Path(filename).exists():
            print(f"Save slot {slot_id} not found")
            return None
        
        try:
            if self.use_compression:
                with gzip.open(filename, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(filename, 'r') as f:
                    data = json.load(f)
            
            slot = SaveSlot.from_dict(data)
            self.current_slot = slot
            print(f"Game loaded from slot {slot_id}")
            return slot
        
        except Exception as e:
            print(f"Failed to load save: {e}")
            return None
    
    def list_saves(self) -> List[Dict]:
        """List all available saves"""
        saves = []
        
        for save_file in self.save_dir.glob("save_*.sav*"):
            try:
                if save_file.suffix == '.gz':
                    with gzip.open(save_file, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(save_file, 'r') as f:
                        data = json.load(f)
                
                saves.append({
                    'slot_id': data['slot_id'],
                    'timestamp': data['timestamp'],
                    'scene_name': data.get('scene_name', 'Unknown'),
                    'player_name': data.get('player_name', 'Player'),
                    'playtime': data.get('playtime', 0.0)
                })
            except Exception as e:
                print(f"Failed to read save {save_file}: {e}")
        
        return sorted(saves, key=lambda x: x['timestamp'], reverse=True)
    
    def delete_save(self, slot_id: int):
        """Delete save slot"""
        filename = self._get_save_path(slot_id)
        if filename.exists():
            filename.unlink()
            print(f"Deleted save slot {slot_id}")
    
    def autosave(self):
        """Perform autosave"""
        if self.current_slot:
            autosave_slot = SaveSlot(999)  # Reserved slot for autosaves
            autosave_slot.scene = self.current_slot.scene
            autosave_slot.physics = self.current_slot.physics
            autosave_slot.ai_states = self.current_slot.ai_states
            autosave_slot.player_data = self.current_slot.player_data
            
            self.save_game(autosave_slot)
    
    def update(self, dt: float):
        """Update autosave timer"""
        if not self.autosave_enabled:
            return
        
        self.autosave_timer += dt
        if self.autosave_timer >= self.autosave_interval:
            self.autosave()
            self.autosave_timer = 0.0


def create_save_system(save_directory: str = "saves") -> SaveSystem:
    """Factory function"""
    return SaveSystem(save_directory)
