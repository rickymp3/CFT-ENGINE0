"""
CFT-ENGINE0 Stress Tests and Quality Assurance
Comprehensive testing suite for performance, stability, and edge cases
"""

import pytest
import time
import gc
from panda3d.core import Point3, Vec3, loadPrcFileData
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBase import ShowBase

# Configure headless testing
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")


class TestBase(ShowBase):
    """Test base application"""
    
    def __init__(self):
        ShowBase.__init__(self)
        self.physics_world = BulletWorld()
        self.physics_world.set_gravity(Vec3(0, 0, -9.81))


@pytest.fixture
def base_app():
    """Provide ShowBase instance"""
    app = TestBase()
    yield app
    app.destroy()


# ==================== Performance Tests ====================

class TestPerformance:
    """Performance and stress tests"""
    
    def test_high_object_count(self, base_app):
        """Test with many scene objects"""
        print("\n🔬 Testing high object count...")
        
        # Spawn 1000 objects
        for i in range(1000):
            node = base_app.render.attach_new_node(f"object_{i}")
            node.set_pos(i % 100, i // 100, 0)
        
        # Measure frame time
        start = time.time()
        for _ in range(100):
            base_app.taskMgr.step()
        duration = time.time() - start
        
        avg_frame_time = duration / 100
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        print(f"   1000 objects: {fps:.1f} FPS")
        assert fps > 30, "FPS too low with 1000 objects"
    
    def test_physics_stress(self, base_app):
        """Test physics with many bodies"""
        print("\n🔬 Testing physics stress...")
        
        from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
        
        # Spawn 100 physics objects
        for i in range(100):
            shape = BulletSphereShape(0.5)
            node = BulletRigidBodyNode(f"sphere_{i}")
            node.add_shape(shape)
            node.set_mass(1.0)
            base_app.physics_world.attach(node)
        
        # Run simulation
        start = time.time()
        for _ in range(100):
            base_app.physics_world.do_physics(1.0/60.0)
        duration = time.time() - start
        
        steps_per_second = 100 / duration
        print(f"   100 physics bodies: {steps_per_second:.1f} steps/sec")
        assert steps_per_second > 30, "Physics too slow"
    
    def test_rapid_object_creation_deletion(self, base_app):
        """Test object churn"""
        print("\n🔬 Testing object churn...")
        
        for cycle in range(10):
            # Create 100 objects
            nodes = []
            for i in range(100):
                node = base_app.render.attach_new_node(f"temp_{i}")
                nodes.append(node)
            
            # Delete them
            for node in nodes:
                node.remove_node()
        
        # Force garbage collection
        collected = gc.collect()
        print(f"   Collected {collected} objects after churn test")
        assert collected < 1000, "Excessive garbage after churn"


# ==================== Memory Tests ====================

class TestMemory:
    """Memory leak and usage tests"""
    
    def test_memory_stability(self, base_app):
        """Test for memory leaks"""
        print("\n🔬 Testing memory stability...")
        
        import psutil
        process = psutil.Process()
        
        # Get baseline
        gc.collect()
        baseline = process.memory_info().rss / (1024 * 1024)
        
        # Allocate and deallocate many times
        for cycle in range(10):
            nodes = []
            for i in range(100):
                node = base_app.render.attach_new_node(f"test_{i}")
                nodes.append(node)
            
            for node in nodes:
                node.remove_node()
            
            gc.collect()
        
        # Check final memory
        final = process.memory_info().rss / (1024 * 1024)
        growth = final - baseline
        
        print(f"   Memory growth: {growth:.2f}MB")
        assert growth < 10, f"Memory leak detected: {growth:.2f}MB growth"
    
    def test_texture_memory(self, base_app):
        """Test texture loading and unloading"""
        print("\n🔬 Testing texture memory...")
        
        from panda3d.core import Texture, TexturePool
        
        # Create textures
        textures = []
        for i in range(10):
            tex = Texture(f"test_texture_{i}")
            tex.setup_2d_texture(512, 512, Texture.T_unsigned_byte, Texture.F_rgba)
            textures.append(tex)
        
        # Release them
        textures.clear()
        gc.collect()
        
        print("   Texture memory test passed")


# ==================== System Integration Tests ====================

class TestSystemIntegration:
    """Test system interactions"""
    
    def test_all_systems_together(self, base_app):
        """Test all AAA systems working together"""
        print("\n🔬 Testing system integration...")
        
        try:
            from engine_modules.global_illumination import create_gi_system
            from engine_modules.weather_system import EnvironmentalSystem
            from engine_modules.audio_system import SpatialAudioSystem
            
            # Initialize systems
            gi = create_gi_system(base_app, quality="low")
            weather = EnvironmentalSystem(base_app)
            audio = SpatialAudioSystem(base_app, enable_hrtf=False)
            
            # Update systems
            for _ in range(10):
                dt = 1.0 / 60.0
                weather.update(dt)
                gi.update(dt)
                audio.update(dt)
                base_app.taskMgr.step()
            
            print("   All systems integrated successfully")
        
        except Exception as e:
            pytest.fail(f"System integration failed: {e}")


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_delta_time(self, base_app):
        """Test with zero delta time"""
        print("\n🔬 Testing zero delta time...")
        
        from engine_modules.weather_system import EnvironmentalSystem
        
        weather = EnvironmentalSystem(base_app)
        weather.update(0.0)  # Should not crash
        print("   Zero dt handled correctly")
    
    def test_negative_positions(self, base_app):
        """Test with extreme negative positions"""
        print("\n🔬 Testing negative positions...")
        
        node = base_app.render.attach_new_node("test")
        node.set_pos(-10000, -10000, -10000)
        base_app.taskMgr.step()
        
        pos = node.get_pos()
        assert pos.x == -10000
        print("   Extreme positions handled")
    
    def test_rapid_state_changes(self, base_app):
        """Test rapid state transitions"""
        print("\n🔬 Testing rapid state changes...")
        
        from engine_modules.weather_system import EnvironmentalSystem, WeatherType
        
        weather = EnvironmentalSystem(base_app)
        
        # Rapidly change weather
        weather_types = list(WeatherType)
        for i in range(100):
            weather.set_weather(weather_types[i % len(weather_types)], intensity=0.5, transition_time=0.0)
            weather.update(0.01)
        
        print("   Rapid state changes handled")


# ==================== Benchmark Tests ====================

class TestBenchmarks:
    """Performance benchmarks"""
    
    def test_ai_pathfinding_performance(self, base_app):
        """Benchmark AI pathfinding"""
        print("\n🔬 Benchmarking AI pathfinding...")
        
        from engine_modules.ai_system import create_ai_system
        
        ai_sys = create_ai_system(base_app)
        navmesh = ai_sys.create_navmesh(grid_size=(20, 20, 5))
        navmesh.generate_grid(Point3(-50, -50, 0), Point3(50, 50, 20))
        
        # Benchmark pathfinding
        start = time.time()
        for _ in range(100):
            path = navmesh.find_path(Point3(0, 0, 0), Point3(40, 40, 0))
        duration = time.time() - start
        
        paths_per_second = 100 / duration
        print(f"   Pathfinding: {paths_per_second:.1f} paths/sec")
        assert paths_per_second > 10, "Pathfinding too slow"
    
    def test_save_load_performance(self, base_app):
        """Benchmark save/load speed"""
        print("\n🔬 Benchmarking save/load...")
        
        from engine_modules.save_system import create_save_system
        
        save_sys = create_save_system("test_saves")
        
        # Create save
        slot = save_sys.create_save(999)
        slot.scene.scan_scene(base_app.render)
        
        # Benchmark save
        start = time.time()
        save_sys.save_game(slot)
        save_time = time.time() - start
        
        # Benchmark load
        start = time.time()
        loaded = save_sys.load_game(999)
        load_time = time.time() - start
        
        print(f"   Save time: {save_time*1000:.2f}ms")
        print(f"   Load time: {load_time*1000:.2f}ms")
        
        assert save_time < 1.0, "Save too slow"
        assert load_time < 1.0, "Load too slow"
        
        # Cleanup
        save_sys.delete_save(999)


# ==================== Stability Tests ====================

class TestStability:
    """Long-running stability tests"""
    
    def test_extended_runtime(self, base_app):
        """Test running for extended period"""
        print("\n🔬 Testing extended runtime...")
        
        from engine_modules.weather_system import EnvironmentalSystem
        
        weather = EnvironmentalSystem(base_app)
        
        # Run for 1000 frames
        for frame in range(1000):
            dt = 1.0 / 60.0
            weather.update(dt)
            base_app.taskMgr.step()
            
            if frame % 100 == 0:
                print(f"   Frame {frame}/1000")
        
        print("   Extended runtime test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
