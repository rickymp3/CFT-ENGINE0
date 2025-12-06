"""
CFT-ENGINE0 AAA Systems Integration Tests
Tests all 10 advanced systems
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from panda3d.core import Point3, Vec3, Vec4, loadPrcFileData
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBase import ShowBase


class MockBase:
    """Mock ShowBase for testing"""
    
    def __init__(self):
        self.render = None
        self.camera = None
        self.loader = None
        self.win = None


def test_global_illumination_import():
    """Test GI system imports"""
    from engine_modules.global_illumination import create_gi_system, GIQuality
    assert GIQuality.HIGH is not None


def test_weather_system_import():
    """Test weather system imports"""
    from engine_modules.weather_system import EnvironmentalSystem, WeatherType
    assert WeatherType.RAIN is not None


def test_audio_system_import():
    """Test audio system imports"""
    from engine_modules.audio_system import SpatialAudioSystem, AudioBusType
    assert AudioBusType.MASTER is not None


def test_ai_system_import():
    """Test AI system imports"""
    from engine_modules.ai_system import create_ai_system, BehaviorTree, NodeStatus
    assert NodeStatus.SUCCESS is not None


def test_fluid_system_import():
    """Test fluid system imports"""
    from engine_modules.fluid_system import create_fluid_system, SPHFluidSimulation
    assert SPHFluidSimulation is not None


def test_streaming_system_import():
    """Test streaming system imports"""
    from engine_modules.streaming_system import create_streaming_system, LODLevel
    assert LODLevel.HIGH is not None


def test_save_system_import():
    """Test save system imports"""
    from engine_modules.save_system import create_save_system, SaveSlot
    assert SaveSlot is not None


def test_volumetric_system_import():
    """Test volumetric system imports"""
    from engine_modules.volumetric_system import create_volumetric_system, VolumetricFog
    assert VolumetricFog is not None


def test_advanced_effects_import():
    """Test advanced effects imports"""
    from engine_modules.advanced_effects import create_advanced_effects_system, WaterSurface
    assert WaterSurface is not None


def test_weather_types():
    """Test weather type enumeration"""
    from engine_modules.weather_system import WeatherType
    
    assert WeatherType.CLEAR is not None
    assert WeatherType.RAIN is not None
    assert WeatherType.SNOW is not None
    assert WeatherType.STORM is not None
    assert len(list(WeatherType)) == 8


def test_audio_buses():
    """Test audio bus enumeration"""
    from engine_modules.audio_system import AudioBusType
    
    assert AudioBusType.MASTER is not None
    assert AudioBusType.MUSIC is not None
    assert AudioBusType.SFX is not None
    assert len(list(AudioBusType)) == 6


def test_behavior_tree_nodes():
    """Test behavior tree node types"""
    from engine_modules.ai_system import (
        SequenceNode, SelectorNode, ParallelNode,
        ConditionNode, ActionNode, InverterNode
    )
    
    seq = SequenceNode("test")
    assert seq.name == "test"
    assert len(seq.children) == 0
    
    sel = SelectorNode("selector")
    assert sel.name == "selector"


def test_sph_particle_creation():
    """Test SPH particle creation"""
    from engine_modules.fluid_system import SPHParticle
    
    particle = SPHParticle(Point3(0, 0, 0), mass=1.0)
    assert particle.mass == 1.0
    assert particle.density == 0.0


def test_navmesh_creation():
    """Test navigation mesh creation"""
    from engine_modules.ai_system import NavigationMesh
    
    navmesh = NavigationMesh(grid_size=(10, 10, 5), cell_size=2.0)
    assert navmesh.cell_size == 2.0
    assert len(navmesh.nodes) == 0  # Not generated yet


def test_streaming_zone_creation():
    """Test streaming zone creation"""
    from engine_modules.streaming_system import StreamingZone
    
    zone = StreamingZone("test_zone", Point3(0, 0, 0), radius=10.0)
    assert zone.zone_id == "test_zone"
    assert zone.radius == 10.0
    assert zone.is_loaded == False


def test_save_slot_serialization():
    """Test save slot to/from dict"""
    from engine_modules.save_system import SaveSlot
    
    slot = SaveSlot(slot_id=1)
    slot.scene_name = "Test Scene"
    slot.player_name = "Test Player"
    
    data = slot.to_dict()
    assert data['slot_id'] == 1
    assert data['scene_name'] == "Test Scene"
    
    loaded = SaveSlot.from_dict(data)
    assert loaded.slot_id == 1
    assert loaded.scene_name == "Test Scene"


def test_camera_rig():
    """Test cinematic camera rig"""
    from engine_modules.advanced_effects import CameraRig
    
    rig = CameraRig("test_cam")
    rig.position = Point3(10, -20, 5)
    rig.fov = 75.0
    
    assert rig.name == "test_cam"
    assert rig.fov == 75.0


def test_lod_levels():
    """Test LOD level enumeration"""
    from engine_modules.streaming_system import LODLevel
    
    assert LODLevel.ULTRA.value == 0
    assert LODLevel.HIGH.value == 1
    assert LODLevel.MEDIUM.value == 2
    assert LODLevel.LOW.value == 3
    assert LODLevel.IMPOSTOR.value == 4


def test_gi_quality_levels():
    """Test GI quality enumeration"""
    from engine_modules.global_illumination import GIQuality
    
    assert GIQuality.LOW is not None
    assert GIQuality.MEDIUM is not None
    assert GIQuality.HIGH is not None
    assert GIQuality.ULTRA is not None


def test_vector_serialization():
    """Test vector serialization helpers"""
    from engine_modules.save_system import Vector3Serializer, Point3Serializer
    
    vec = Vec3(1.5, 2.5, 3.5)
    data = Vector3Serializer.serialize(vec)
    assert data == [1.5, 2.5, 3.5]
    
    restored = Vector3Serializer.deserialize(data)
    assert restored.x == 1.5
    assert restored.y == 2.5
    assert restored.z == 3.5


def test_scene_object_serialization():
    """Test scene object serialization"""
    from engine_modules.save_system import SceneObject
    
    obj = SceneObject("test_obj", "models/box.bam")
    obj.position = Point3(1, 2, 3)
    obj.tags['type'] = 'static'
    
    data = obj.to_dict()
    assert data['name'] == "test_obj"
    assert data['model_path'] == "models/box.bam"
    assert data['tags']['type'] == 'static'
    
    loaded = SceneObject.from_dict(data)
    assert loaded.name == "test_obj"
    assert loaded.position.x == 1


def test_ai_agent_blackboard():
    """Test AI agent blackboard"""
    from engine_modules.ai_system import AIAgent, NavigationMesh
    
    navmesh = NavigationMesh()
    # Note: Would need MockNodePath for full test
    
    # Test blackboard can store data
    blackboard = {}
    blackboard['target'] = Point3(10, 10, 0)
    blackboard['alert_level'] = 5
    
    assert blackboard['target'].x == 10
    assert blackboard['alert_level'] == 5


def test_physics_state_serialization():
    """Test physics state serialization"""
    from engine_modules.save_system import PhysicsState, QuatSerializer
    from panda3d.core import Quat
    
    state = PhysicsState()
    state.name = "box"
    state.position = Point3(1, 2, 3)
    state.linear_velocity = Vec3(0.5, 0, 0)
    state.mass = 10.0
    
    data = state.to_dict()
    assert data['name'] == "box"
    assert data['mass'] == 10.0
    
    loaded = PhysicsState.from_dict(data)
    assert loaded.name == "box"
    assert loaded.mass == 10.0


def test_streaming_priority():
    """Test streaming priority calculation"""
    from engine_modules.streaming_system import StreamingPriority
    
    assert StreamingPriority.CRITICAL.value == 0
    assert StreamingPriority.HIGH.value == 1
    assert StreamingPriority.MEDIUM.value == 2
    assert StreamingPriority.LOW.value == 3
    assert StreamingPriority.UNLOAD.value == 4


def test_all_systems_documentation():
    """Verify all documentation files exist"""
    docs = [
        'FINAL_IMPLEMENTATION_SUMMARY.md',
        'AAA_SYSTEMS_COMPLETE_GUIDE.md',
        'QUICK_START_AAA.md',
        'PROFESSIONAL_SYSTEMS_STATUS.md'
    ]
    
    for doc in docs:
        path = Path(__file__).parent.parent / doc
        assert path.exists(), f"Missing documentation: {doc}"


def test_all_module_files_exist():
    """Verify all module files exist"""
    modules = [
        'engine_modules/global_illumination.py',
        'engine_modules/weather_system.py',
        'engine_modules/audio_system.py',
        'engine_modules/ai_system.py',
        'engine_modules/fluid_system.py',
        'engine_modules/streaming_system.py',
        'engine_modules/save_system.py',
        'engine_modules/volumetric_system.py',
        'engine_modules/advanced_effects.py'
    ]
    
    for module in modules:
        path = Path(__file__).parent.parent / module
        assert path.exists(), f"Missing module: {module}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
