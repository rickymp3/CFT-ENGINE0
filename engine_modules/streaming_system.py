"""
CFT-ENGINE0 World Streaming and LOD System
Manages loading/unloading of world chunks, level-of-detail transitions, and memory budgets
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Set
from panda3d.core import Point3, Vec3, NodePath, LODNode, BoundingSphere, PandaNode
from panda3d.core import ModelNode, TextureStage, Texture
from enum import Enum
import json


# ==================== LOD Management ====================

class LODLevel(Enum):
    """Level of detail quality levels"""
    ULTRA = 0  # Highest quality
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    IMPOSTOR = 4  # Billboard/card


class LODModelNode:
    """Model with multiple LOD levels"""
    
    def __init__(self, name: str):
        self.name = name
        self.lod_node = LODNode(name)
        self.node_path: Optional[NodePath] = None
        self.levels: Dict[LODLevel, Tuple[NodePath, float]] = {}  # level -> (model, distance)
    
    def add_lod(self, level: LODLevel, model: NodePath, switch_distance: float):
        """Add LOD level"""
        self.levels[level] = (model, switch_distance)
        
        # Add to LOD node
        if level == LODLevel.ULTRA:
            self.lod_node.add_switch(0, switch_distance)
        else:
            self.lod_node.add_switch(switch_distance, float('inf'))
    
    def attach_to(self, parent: NodePath) -> NodePath:
        """Attach LOD node to scene"""
        self.node_path = parent.attach_new_node(self.lod_node)
        
        # Attach all LOD models
        for level, (model, distance) in sorted(self.levels.items(), key=lambda x: x[0].value):
            model.reparent_to(self.node_path)
        
        return self.node_path


# ==================== Streaming Zones ====================

class StreamingZone:
    """Represents a streamable world region"""
    
    def __init__(self, zone_id: str, center: Point3, radius: float):
        self.zone_id = zone_id
        self.center = center
        self.radius = radius
        self.bounds = BoundingSphere(center, radius)
        
        # Assets to load in this zone
        self.asset_paths: List[str] = []
        self.loaded_assets: Dict[str, NodePath] = {}
        
        # State
        self.is_loaded = False
        self.is_loading = False
        self.load_task: Optional[asyncio.Task] = None
        
        # Scene node
        self.zone_node: Optional[NodePath] = None
        
        # Priority
        self.priority = 0
    
    def add_asset(self, asset_path: str):
        """Add asset to be loaded with this zone"""
        if asset_path not in self.asset_paths:
            self.asset_paths.append(asset_path)
    
    def contains_point(self, point: Point3) -> bool:
        """Check if point is within zone"""
        return (self.center - point).length() <= self.radius
    
    def distance_to(self, point: Point3) -> float:
        """Distance from point to zone center"""
        return (self.center - point).length()


class StreamingPriority(Enum):
    """Priority levels for streaming"""
    CRITICAL = 0  # Player is in zone
    HIGH = 1      # Adjacent to player zone
    MEDIUM = 2    # Nearby
    LOW = 3       # Far away
    UNLOAD = 4    # Should be unloaded


# ==================== Streaming Manager ====================

class StreamingManager:
    """Manages world streaming and asset loading"""
    
    def __init__(self, base, asset_pipeline=None):
        self.base = base
        self.asset_pipeline = asset_pipeline
        
        # Zones
        self.zones: Dict[str, StreamingZone] = {}
        self.loaded_zones: Set[str] = set()
        self.loading_zones: Set[str] = set()
        
        # Player tracking
        self.player_position = Point3(0, 0, 0)
        self.view_distance = 100.0  # Max distance for loading
        self.unload_distance = 150.0  # Distance to unload zones
        self.camera_mask = None  # Optional culling mask hook
        
        # Memory management
        self.max_loaded_zones = 9  # 3x3 grid around player
        self.memory_budget_mb = 512.0
        self.current_memory_usage_mb = 0.0
        
        # Streaming control
        self.streaming_enabled = True
        self.max_concurrent_loads = 2
        self.allow_sync_load = True  # fallback when no loop present
        
        # Root node for streamed content
        self.streaming_root = base.render.attach_new_node("streaming_root")

    def set_budgets(self, max_loaded_zones: int = 9, memory_budget_mb: float = 512.0, view_distance: float = 100.0) -> None:
        """Update streaming budgets and view distances."""
        self.max_loaded_zones = max_loaded_zones
        self.memory_budget_mb = memory_budget_mb
        self.view_distance = view_distance
    
    def create_zone(self, zone_id: str, center: Point3, radius: float) -> StreamingZone:
        """Create new streaming zone"""
        zone = StreamingZone(zone_id, center, radius)
        self.zones[zone_id] = zone
        return zone
    
    def create_grid_zones(self, grid_size: Tuple[int, int], zone_size: float, height: float = 0.0):
        """Create grid of zones for an open world"""
        for x in range(grid_size[0]):
            for y in range(grid_size[1]):
                center = Point3(
                    x * zone_size - (grid_size[0] * zone_size) / 2,
                    y * zone_size - (grid_size[1] * zone_size) / 2,
                    height
                )
                zone_id = f"zone_{x}_{y}"
                self.create_zone(zone_id, center, zone_size / 2)
    
    def _calculate_priority(self, zone: StreamingZone) -> StreamingPriority:
        """Calculate loading priority for zone"""
        distance = zone.distance_to(self.player_position)
        
        if zone.contains_point(self.player_position):
            return StreamingPriority.CRITICAL
        elif distance < self.view_distance * 0.3:
            return StreamingPriority.HIGH
        elif distance < self.view_distance * 0.7:
            return StreamingPriority.MEDIUM
        elif distance < self.view_distance:
            return StreamingPriority.LOW
        else:
            return StreamingPriority.UNLOAD
    
    async def _load_zone_async(self, zone: StreamingZone):
        """Load zone assets asynchronously"""
        if zone.is_loaded or zone.is_loading:
            return
        
        zone.is_loading = True
        self.loading_zones.add(zone.zone_id)
        
        try:
            # Create zone node
            zone.zone_node = self.streaming_root.attach_new_node(zone.zone_id)
            
            # Load each asset
            for asset_path in zone.asset_paths:
                try:
                    loader = getattr(self.base, "loader", None)
                    if loader is None:
                        continue
                    # If we have asset pipeline, use it
                    if self.asset_pipeline:
                        await asyncio.sleep(0.01)  # Yield control
                        model = loader.load_model(asset_path)
                    else:
                        model = loader.load_model(asset_path)
                    
                    if model:
                        if self.camera_mask is not None and hasattr(model, "set_camera_mask"):
                            model.set_camera_mask(self.camera_mask)
                        model.reparent_to(zone.zone_node)
                        zone.loaded_assets[asset_path] = model
                
                except Exception as e:
                    print(f"Failed to load asset {asset_path}: {e}")
            
            zone.is_loaded = True
            self.loaded_zones.add(zone.zone_id)
            print(f"Loaded zone: {zone.zone_id}")
        
        finally:
            zone.is_loading = False
            self.loading_zones.discard(zone.zone_id)
    
    def _unload_zone(self, zone: StreamingZone):
        """Unload zone and free memory"""
        if not zone.is_loaded:
            return
        
        # Remove all loaded assets
        for asset_path, model in zone.loaded_assets.items():
            model.remove_node()
        
        zone.loaded_assets.clear()
        
        # Remove zone node
        if zone.zone_node:
            zone.zone_node.remove_node()
            zone.zone_node = None
        
        zone.is_loaded = False
        self.loaded_zones.discard(zone.zone_id)
        print(f"Unloaded zone: {zone.zone_id}")
    
    def update_player_position(self, position: Point3):
        """Update player position for streaming calculations"""
        self.player_position = position
    
    def update(self, dt: float):
        """Update streaming system"""
        if not self.streaming_enabled:
            return
        
        # Calculate priorities
        zone_priorities: List[Tuple[StreamingZone, StreamingPriority]] = []
        for zone in self.zones.values():
            priority = self._calculate_priority(zone)
            zone.priority = priority.value
            zone_priorities.append((zone, priority))
        
        # Sort by priority
        zone_priorities.sort(key=lambda x: x[1].value)
        
        # Unload far zones
        for zone, priority in zone_priorities:
            if priority == StreamingPriority.UNLOAD and zone.is_loaded:
                self._unload_zone(zone)
        
        # Load nearby zones
        loading_count = len(self.loading_zones)
        
        for zone, priority in zone_priorities:
            if loading_count >= self.max_concurrent_loads:
                break
            
            if priority != StreamingPriority.UNLOAD and not zone.is_loaded and not zone.is_loading:
                # Check zone limit
                if len(self.loaded_zones) + len(self.loading_zones) >= self.max_loaded_zones:
                    break
                
                # Start async load
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = asyncio.create_task(self._load_zone_async(zone))
                    zone.load_task = task
                    loading_count += 1
                elif self.allow_sync_load:
                    # Synchronous fallback
                    loop.run_until_complete(self._load_zone_async(zone))
                    loading_count += 1
    
    def save_streaming_config(self, filename: str):
        """Save zone configuration to file"""
        config = {
            'zones': []
        }
        
        for zone in self.zones.values():
            zone_data = {
                'id': zone.zone_id,
                'center': [zone.center.x, zone.center.y, zone.center.z],
                'radius': zone.radius,
                'assets': zone.asset_paths
            }
            config['zones'].append(zone_data)
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_streaming_config(self, filename: str):
        """Load zone configuration from file"""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        for zone_data in config['zones']:
            center = Point3(*zone_data['center'])
            zone = self.create_zone(zone_data['id'], center, zone_data['radius'])
            for asset in zone_data['assets']:
                zone.add_asset(asset)

    def get_status(self) -> Dict:
        """Expose streaming telemetry for dashboards."""
        return {
            "zones": len(self.zones),
            "loaded": len(self.loaded_zones),
            "loading": len(self.loading_zones),
            "budget_zones": self.max_loaded_zones,
            "memory_budget_mb": self.memory_budget_mb,
            "view_distance": self.view_distance,
            "streaming_enabled": self.streaming_enabled,
        }


# ==================== Texture Streaming ====================

class TextureStreaming:
    """Manages texture LOD and streaming"""
    
    def __init__(self):
        self.texture_lods: Dict[str, List[Texture]] = {}  # texture_name -> [high, med, low]
        self.active_textures: Dict[str, int] = {}  # texture_name -> current_lod_index
    
    def add_texture_lods(self, name: str, textures: List[Texture]):
        """Add texture with multiple mipmap levels"""
        self.texture_lods[name] = textures
        self.active_textures[name] = 0  # Start with highest quality
    
    def set_texture_lod(self, name: str, lod_index: int, model: NodePath):
        """Switch texture LOD on model"""
        if name not in self.texture_lods:
            return
        
        lod_index = max(0, min(lod_index, len(self.texture_lods[name]) - 1))
        texture = self.texture_lods[name][lod_index]
        
        # Apply to model
        model.set_texture(texture)
        self.active_textures[name] = lod_index
    
    def update_based_on_distance(self, texture_name: str, distance: float, model: NodePath):
        """Automatically select LOD based on distance"""
        if distance < 20:
            self.set_texture_lod(texture_name, 0, model)  # High
        elif distance < 50:
            self.set_texture_lod(texture_name, 1, model)  # Medium
        else:
            self.set_texture_lod(texture_name, 2, model)  # Low


# ==================== World Origin Shifting ====================

class OriginShifter:
    """Handles world origin shifting for large worlds"""
    
    def __init__(self, base):
        self.base = base
        self.shift_threshold = 10000.0  # Shift when player exceeds this distance
        self.total_offset = Vec3(0, 0, 0)
    
    def check_and_shift(self, player_position: Point3) -> bool:
        """Check if origin shift is needed and perform it"""
        distance_from_origin = player_position.length()
        
        if distance_from_origin > self.shift_threshold:
            self.shift_origin(player_position)
            return True
        
        return False
    
    def shift_origin(self, shift_amount: Point3):
        """Shift world origin by moving everything except player"""
        shift_vec = Vec3(-shift_amount.x, -shift_amount.y, -shift_amount.z)
        
        # Move all scene nodes
        for child in self.base.render.get_children():
            current_pos = child.get_pos()
            child.set_pos(current_pos + shift_vec)
        
        # Track total offset for physics/networking
        self.total_offset += shift_vec
        
        print(f"Origin shifted by {shift_amount}, total offset: {self.total_offset}")
    
    def get_world_position(self, local_position: Point3) -> Point3:
        """Convert local position to world position"""
        return Point3(
            local_position.x - self.total_offset.x,
            local_position.y - self.total_offset.y,
            local_position.z - self.total_offset.z
        )


# ==================== Streaming System ====================

class StreamingSystem:
    """Complete streaming system with LOD and origin shifting"""
    
    def __init__(self, base, asset_pipeline=None):
        self.base = base
        self.streaming_manager = StreamingManager(base, asset_pipeline)
        self.texture_streaming = TextureStreaming()
        self.origin_shifter = OriginShifter(base)
        
        # LOD models
        self.lod_models: Dict[str, LODModelNode] = {}
        self.enabled = True
    
    def create_zone(self, zone_id: str, center: Point3, radius: float) -> StreamingZone:
        """Create streaming zone"""
        return self.streaming_manager.create_zone(zone_id, center, radius)
    
    def create_grid_zones(self, grid_size: Tuple[int, int], zone_size: float):
        """Create zone grid"""
        self.streaming_manager.create_grid_zones(grid_size, zone_size)
    
    def create_lod_model(self, name: str) -> LODModelNode:
        """Create LOD model"""
        lod_model = LODModelNode(name)
        self.lod_models[name] = lod_model
        return lod_model
    
    def update(self, player_position: Point3, dt: float):
        """Update all streaming systems"""
        if not self.enabled:
            return
        self.streaming_manager.update_player_position(player_position)
        self.streaming_manager.update(dt)
        self.origin_shifter.check_and_shift(player_position)

    def set_enabled(self, enabled: bool) -> None:
        """Toggle streaming without clearing state."""
        self.enabled = enabled


def create_streaming_system(base, asset_pipeline=None) -> StreamingSystem:
    """Factory function"""
    return StreamingSystem(base, asset_pipeline)
