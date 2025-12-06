"""
CFT-ENGINE0 Profiling and Performance Analysis System
Real-time CPU/GPU profiling, memory tracking, draw call counting, and performance overlays
"""

import time
import psutil
import gc
from collections import deque
from typing import Dict, List, Optional, Callable, Tuple
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
import threading
import json
from pathlib import Path


# ==================== Performance Metrics ====================

class PerformanceMetrics:
    """Stores performance metrics"""
    
    def __init__(self, history_size: int = 300):
        self.history_size = history_size
        
        # Frame timing
        self.frame_times = deque(maxlen=history_size)
        self.fps_history = deque(maxlen=history_size)
        
        # CPU metrics
        self.cpu_usage = deque(maxlen=history_size)
        self.cpu_per_core = []
        
        # Memory metrics
        self.memory_usage_mb = deque(maxlen=history_size)
        self.memory_percent = deque(maxlen=history_size)
        
        # GPU metrics (approximated)
        self.draw_calls = deque(maxlen=history_size)
        self.vertices_rendered = deque(maxlen=history_size)
        self.textures_loaded = deque(maxlen=history_size)
        
        # System metrics
        self.active_tasks = deque(maxlen=history_size)
        self.nodes_in_scene = deque(maxlen=history_size)
        
        # Timing zones
        self.zone_times: Dict[str, deque] = {}
    
    def add_frame_time(self, dt: float):
        """Record frame time"""
        self.frame_times.append(dt)
        fps = 1.0 / dt if dt > 0 else 0
        self.fps_history.append(fps)
    
    def add_zone_time(self, zone_name: str, duration: float):
        """Record timing for specific zone"""
        if zone_name not in self.zone_times:
            self.zone_times[zone_name] = deque(maxlen=self.history_size)
        self.zone_times[zone_name].append(duration)
    
    def get_average_fps(self) -> float:
        """Get average FPS"""
        if not self.fps_history:
            return 0.0
        return sum(self.fps_history) / len(self.fps_history)
    
    def get_min_max_fps(self) -> Tuple[float, float]:
        """Get min and max FPS"""
        if not self.fps_history:
            return 0.0, 0.0
        return min(self.fps_history), max(self.fps_history)
    
    def get_frame_time_percentiles(self) -> Dict[str, float]:
        """Get frame time percentiles"""
        if not self.frame_times:
            return {}
        
        sorted_times = sorted(self.frame_times)
        n = len(sorted_times)
        
        return {
            'p50': sorted_times[n // 2],
            'p95': sorted_times[int(n * 0.95)],
            'p99': sorted_times[int(n * 0.99)]
        }


# ==================== Profiler Zones ====================

class ProfilerZone:
    """Context manager for profiling code sections"""
    
    def __init__(self, profiler: 'EngineProfiler', zone_name: str):
        self.profiler = profiler
        self.zone_name = zone_name
        self.start_time = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.profiler.record_zone(self.zone_name, duration)


# ==================== Memory Profiler ====================

class MemoryProfiler:
    """Tracks memory usage and detects leaks"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.snapshots: List[Dict] = []
        self.leak_threshold_mb = 10.0  # Alert if growth exceeds this
        self.baseline_memory = 0.0
    
    def take_snapshot(self, label: str = ""):
        """Take memory snapshot"""
        mem_info = self.process.memory_info()
        snapshot = {
            'label': label,
            'timestamp': time.time(),
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': self.process.memory_percent()
        }
        self.snapshots.append(snapshot)
        
        if not self.baseline_memory:
            self.baseline_memory = snapshot['rss_mb']
        
        return snapshot
    
    def detect_leaks(self) -> List[Dict]:
        """Detect potential memory leaks"""
        if len(self.snapshots) < 2:
            return []
        
        leaks = []
        for i in range(1, len(self.snapshots)):
            prev = self.snapshots[i-1]
            curr = self.snapshots[i]
            growth = curr['rss_mb'] - prev['rss_mb']
            
            if growth > self.leak_threshold_mb:
                leaks.append({
                    'from': prev['label'],
                    'to': curr['label'],
                    'growth_mb': growth,
                    'time_delta': curr['timestamp'] - prev['timestamp']
                })
        
        return leaks
    
    def get_current_usage(self) -> Dict:
        """Get current memory usage"""
        mem_info = self.process.memory_info()
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': self.process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / (1024 * 1024)
        }
    
    def force_gc(self):
        """Force garbage collection and return collected objects"""
        collected = gc.collect()
        return collected


# ==================== GPU Profiler ====================

class GPUProfiler:
    """GPU performance metrics (Panda3D specific)"""
    
    def __init__(self, base: ShowBase):
        self.base = base
        self.render_stats = {}
    
    def get_draw_calls(self) -> int:
        """Estimate draw calls from scene graph"""
        # Walk scene graph and count renderable nodes
        count = 0
        for node in self.base.render.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            count += geom_node.get_num_geoms()
        return count
    
    def get_vertex_count(self) -> int:
        """Count total vertices in scene"""
        total = 0
        for node in self.base.render.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            for i in range(geom_node.get_num_geoms()):
                geom = geom_node.get_geom(i)
                vdata = geom.get_vertex_data()
                total += vdata.get_num_rows()
        return total
    
    def get_texture_memory(self) -> float:
        """Estimate texture memory usage (MB)"""
        total_bytes = 0
        texture_pool = TexturePool.get_global_ptr()
        
        # This is an approximation - would need engine support for exact values
        for i in range(texture_pool.get_num_textures()):
            tex = texture_pool.get_texture(i)
            if tex:
                # Estimate: width * height * bytes_per_pixel * num_mips
                x, y = tex.get_x_size(), tex.get_y_size()
                bpp = 4  # Assume RGBA
                total_bytes += x * y * bpp
        
        return total_bytes / (1024 * 1024)
    
    def get_stats(self) -> Dict:
        """Get all GPU stats"""
        return {
            'draw_calls': self.get_draw_calls(),
            'vertices': self.get_vertex_count(),
            'texture_memory_mb': self.get_texture_memory(),
            'nodes_in_scene': len(self.base.render.find_all_matches("**"))
        }


# ==================== Performance Overlay ====================

class PerformanceOverlay:
    """On-screen performance display"""
    
    def __init__(self, base: ShowBase):
        self.base = base
        self.enabled = True
        
        # Background panel
        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-0.35, 0.35, -0.3, 0.3),
            pos=(0.85, 0, -0.7)
        )
        
        # Text elements
        self.texts: Dict[str, OnscreenText] = {}
        self._create_text_elements()
        
        # Graph
        self.graph_node: Optional[NodePath] = None
        self._create_graph()
    
    def _create_text_elements(self):
        """Create text displays"""
        y_offset = 0.25
        line_height = 0.04
        
        labels = [
            'fps', 'frame_time', 'cpu', 'memory',
            'draw_calls', 'vertices', 'nodes'
        ]
        
        for i, label in enumerate(labels):
            text = OnscreenText(
                text=f"{label}: --",
                pos=(-0.3, y_offset - i * line_height),
                scale=0.035,
                fg=(1, 1, 1, 1),
                align=TextNode.ALeft,
                parent=self.frame
            )
            self.texts[label] = text
    
    def _create_graph(self):
        """Create FPS graph"""
        # Would create line graph using GeomLines
        pass
    
    def update(self, metrics: PerformanceMetrics, gpu_stats: Dict, mem_stats: Dict):
        """Update overlay display"""
        if not self.enabled:
            self.frame.hide()
            return
        
        self.frame.show()
        
        # Update text
        avg_fps = metrics.get_average_fps()
        min_fps, max_fps = metrics.get_min_max_fps()
        
        if metrics.frame_times:
            avg_frame_time = sum(metrics.frame_times) / len(metrics.frame_times) * 1000
        else:
            avg_frame_time = 0
        
        self.texts['fps'].setText(f"FPS: {avg_fps:.1f} (min: {min_fps:.1f}, max: {max_fps:.1f})")
        self.texts['frame_time'].setText(f"Frame: {avg_frame_time:.2f}ms")
        
        if metrics.cpu_usage:
            self.texts['cpu'].setText(f"CPU: {metrics.cpu_usage[-1]:.1f}%")
        
        self.texts['memory'].setText(f"Memory: {mem_stats['rss_mb']:.1f}MB ({mem_stats['percent']:.1f}%)")
        self.texts['draw_calls'].setText(f"Draw Calls: {gpu_stats['draw_calls']}")
        self.texts['vertices'].setText(f"Vertices: {gpu_stats['vertices']:,}")
        self.texts['nodes'].setText(f"Scene Nodes: {gpu_stats['nodes_in_scene']}")
    
    def toggle(self):
        """Toggle visibility"""
        self.enabled = not self.enabled


# ==================== Main Engine Profiler ====================

class EngineProfiler:
    """Complete engine profiling system"""
    
    def __init__(self, base: ShowBase):
        self.base = base
        
        # Sub-profilers
        self.metrics = PerformanceMetrics()
        self.memory_profiler = MemoryProfiler()
        self.gpu_profiler = GPUProfiler(base)
        
        # Overlay
        self.overlay = PerformanceOverlay(base)
        
        # Profiling state
        self.enabled = True
        self.detailed_profiling = False
        
        # CPU monitoring
        self.cpu_monitor = psutil.Process()
        
        # Session data
        self.session_start = time.time()
        self.total_frames = 0
        
        # Benchmarking
        self.benchmark_results: List[Dict] = []
    
    def zone(self, zone_name: str) -> ProfilerZone:
        """Create profiling zone context manager"""
        return ProfilerZone(self, zone_name)
    
    def record_zone(self, zone_name: str, duration: float):
        """Record zone timing"""
        self.metrics.add_zone_time(zone_name, duration)
    
    def update(self, dt: float):
        """Update profiler (call every frame)"""
        if not self.enabled:
            return
        
        self.total_frames += 1
        
        # Record frame time
        self.metrics.add_frame_time(dt)
        
        # CPU usage
        cpu_percent = self.cpu_monitor.cpu_percent()
        self.metrics.cpu_usage.append(cpu_percent)
        
        # Memory usage
        mem_info = self.memory_profiler.get_current_usage()
        self.metrics.memory_usage_mb.append(mem_info['rss_mb'])
        self.metrics.memory_percent.append(mem_info['percent'])
        
        # GPU stats (expensive, do less frequently)
        if self.total_frames % 30 == 0:  # Every 30 frames
            gpu_stats = self.gpu_profiler.get_stats()
            self.metrics.draw_calls.append(gpu_stats['draw_calls'])
            self.metrics.vertices_rendered.append(gpu_stats['vertices'])
            self.metrics.nodes_in_scene.append(gpu_stats['nodes_in_scene'])
        
        # Update overlay
        if self.total_frames % 5 == 0:  # Every 5 frames
            gpu_stats = self.gpu_profiler.get_stats()
            self.overlay.update(self.metrics, gpu_stats, mem_info)
    
    def take_memory_snapshot(self, label: str = ""):
        """Take memory snapshot"""
        return self.memory_profiler.take_snapshot(label)
    
    def detect_memory_leaks(self) -> List[Dict]:
        """Detect memory leaks"""
        return self.memory_profiler.detect_leaks()
    
    def run_benchmark(self, test_name: str, test_func: Callable, duration: float = 5.0):
        """Run performance benchmark"""
        print(f"\n🔬 Running benchmark: {test_name}")
        
        # Clear metrics
        self.metrics = PerformanceMetrics()
        
        # Take initial snapshot
        self.memory_profiler.take_snapshot(f"{test_name}_start")
        
        # Run test
        start_time = time.time()
        frames = 0
        
        while time.time() - start_time < duration:
            dt = globalClock.get_dt()
            test_func(dt)
            self.update(dt)
            frames += 1
        
        # Take final snapshot
        self.memory_profiler.take_snapshot(f"{test_name}_end")
        
        # Compile results
        result = {
            'name': test_name,
            'duration': duration,
            'frames': frames,
            'avg_fps': self.metrics.get_average_fps(),
            'min_fps': self.metrics.get_min_max_fps()[0],
            'max_fps': self.metrics.get_min_max_fps()[1],
            'percentiles': self.metrics.get_frame_time_percentiles(),
            'avg_cpu': sum(self.metrics.cpu_usage) / len(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0,
            'avg_memory_mb': sum(self.metrics.memory_usage_mb) / len(self.metrics.memory_usage_mb) if self.metrics.memory_usage_mb else 0,
            'gpu_stats': self.gpu_profiler.get_stats()
        }
        
        self.benchmark_results.append(result)
        
        print(f"✅ Benchmark complete:")
        print(f"   Avg FPS: {result['avg_fps']:.1f}")
        print(f"   Min/Max FPS: {result['min_fps']:.1f} / {result['max_fps']:.1f}")
        print(f"   Frame time (p95): {result['percentiles'].get('p95', 0)*1000:.2f}ms")
        
        return result
    
    def save_report(self, filename: str):
        """Save profiling report to file"""
        report = {
            'session_duration': time.time() - self.session_start,
            'total_frames': self.total_frames,
            'metrics': {
                'avg_fps': self.metrics.get_average_fps(),
                'min_max_fps': self.metrics.get_min_max_fps(),
                'frame_time_percentiles': self.metrics.get_frame_time_percentiles(),
                'avg_cpu': sum(self.metrics.cpu_usage) / len(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0,
                'peak_memory_mb': max(self.metrics.memory_usage_mb) if self.metrics.memory_usage_mb else 0
            },
            'memory_leaks': self.detect_memory_leaks(),
            'benchmarks': self.benchmark_results,
            'gpu_final': self.gpu_profiler.get_stats()
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Profiling report saved to {filename}")
    
    def toggle_overlay(self):
        """Toggle performance overlay"""
        self.overlay.toggle()


# ==================== Stress Tests ====================

class StressTest:
    """Automated stress testing"""
    
    @staticmethod
    def spawn_objects_test(base: ShowBase, count: int = 1000):
        """Spawn many objects"""
        for i in range(count):
            node = base.render.attach_new_node(f"stress_object_{i}")
            node.set_pos(
                (i % 100) * 2,
                (i // 100) * 2,
                0
            )
    
    @staticmethod
    def physics_stress_test(physics_world, count: int = 500):
        """Stress test physics"""
        from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
        
        for i in range(count):
            shape = BulletSphereShape(0.5)
            node = BulletRigidBodyNode(f"sphere_{i}")
            node.add_shape(shape)
            node.set_mass(1.0)
            physics_world.attach(node)
    
    @staticmethod
    def particle_stress_test(particle_system, count: int = 10000):
        """Stress test particles"""
        from panda3d.core import Point3
        for i in range(count):
            particle_system.spawn_burst(10, Point3(0, 0, 10))


def create_profiler(base: ShowBase) -> EngineProfiler:
    """Factory function"""
    return EngineProfiler(base)
