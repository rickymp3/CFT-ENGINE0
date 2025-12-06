# CFT-ENGINE0 Quick Reference - AAA Systems

## 🚀 Instant Usage Guide

### Global Illumination
```python
from engine_modules.global_illumination import create_gi_system

gi = create_gi_system(base, quality="high")
probe = gi.add_light_probe(Point3(0, 0, 5), radius=10.0)
gi.bake_light_probe(probe)
gi.apply_gi_to_model(my_model)
gi.update(dt)  # Call every frame
```

### Weather & Day-Night
```python
from engine_modules.weather_system import EnvironmentalSystem, WeatherType

env = EnvironmentalSystem(base)
env.set_time(18.5)  # 6:30 PM
env.set_weather(WeatherType.RAIN, intensity=0.7, transition_time=30.0)
env.update(dt)

# Get state
state = env.get_state()
print(f"Time: {state['time']}, Weather: {state['weather']}")
```

### 3D Spatial Audio
```python
from engine_modules.audio_system import SpatialAudioSystem, AudioBusType

audio = SpatialAudioSystem(base, enable_hrtf=True)
audio.load_sound("engine", "sounds/car.wav", bus=AudioBusType.SFX)
audio.set_source_position("engine", Point3(10, 0, 0))
audio.set_source_velocity("engine", Vec3(20, 0, 0))  # For Doppler
audio.play("engine", loop=True)
audio.set_reverb('large_hall')
audio.update(dt)
```

### AI & Navigation
```python
from engine_modules.ai_system import create_ai_system, create_patrol_behavior

ai_sys = create_ai_system(base)
navmesh = ai_sys.create_navmesh(grid_size=(20, 20, 5), cell_size=2.0)
navmesh.generate_grid(Point3(-50, -50, 0), Point3(50, 50, 20))

agent = ai_sys.create_agent("guard", npc_node_path)
waypoints = [Point3(10, 10, 0), Point3(-10, 10, 0)]
agent.set_behavior_tree(create_patrol_behavior(waypoints))

ai_sys.update(dt)
```

### Fluid Simulation
```python
from engine_modules.fluid_system import create_fluid_system

fluid_sys = create_fluid_system(base, physics_world)
sim = fluid_sys.create_fluid_simulation(particle_count=5000)
sim.spawn_cube(Point3(0, 0, 10), size=5.0, spacing=0.2)
sim.create_visual(base.render)

fluid_sys.update(dt)
```

### World Streaming
```python
from engine_modules.streaming_system import create_streaming_system

streaming = create_streaming_system(base, asset_pipeline)
streaming.create_grid_zones(grid_size=(10, 10), zone_size=100.0)

# Add assets to zones
zone = streaming.streaming_manager.zones["zone_0_0"]
zone.add_asset("models/building.bam")

streaming.update(player_position, dt)
```

### Save/Load
```python
from engine_modules.save_system import create_save_system

save_sys = create_save_system(save_directory="saves")

# Save
slot = save_sys.create_save(slot_id=1)
slot.scene_name = "My Level"
slot.scene.scan_scene(base.render)
slot.physics.capture_world(physics_world)
slot.player_data.position = player_pos
save_sys.save_game(slot)

# Load
loaded = save_sys.load_game(1)
if loaded:
    # Restore scene from loaded.scene
    pass
```

### Volumetric Effects
```python
from engine_modules.volumetric_system import create_volumetric_system

volumetric = create_volumetric_system(base)
volumetric.set_fog_density(0.03)
volumetric.set_cloud_coverage(0.5)

emitter = volumetric.create_smoke_emitter(Point3(0, 0, 5), max_particles=1000)
emitter.emission_rate = 100.0

volumetric.update(dt)
```

### Water & Cinematics
```python
from engine_modules.advanced_effects import create_advanced_effects_system
from engine_modules.advanced_effects import CameraRig

effects = create_advanced_effects_system(base)

# Water
water = effects.create_water(size=(200, 200))
water.add_disturbance(x=10, y=20, strength=2.0)

# Particles
particles = effects.create_particle_system(max_particles=10000)
particles.spawn_burst(1000, Point3(0, 0, 5))

# Cinematics
seq = effects.cinematic_system.create_sequence("intro", duration=15.0)
cam = CameraRig("shot1")
cam.position = Point3(20, -40, 15)
cam.look_at = Point3(0, 0, 0)
seq.add_camera_keyframe(0.0, cam)
effects.cinematic_system.play_sequence("intro")

effects.update(dt)
```

---

## 🎨 Common Patterns

### Complete Scene Setup
```python
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3
from engine_modules.global_illumination import create_gi_system
from engine_modules.weather_system import EnvironmentalSystem
from engine_modules.audio_system import SpatialAudioSystem

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Initialize systems
        self.gi = create_gi_system(self, quality="high")
        self.weather = EnvironmentalSystem(self)
        self.audio = SpatialAudioSystem(self)
        
        # Setup scene
        self.weather.set_time(14.0)
        self.weather.set_weather(WeatherType.CLEAR)
        
        # Update task
        self.taskMgr.add(self.update, "update")
    
    def update(self, task):
        dt = globalClock.get_dt()
        self.gi.update(dt)
        self.weather.update(dt)
        self.audio.update(dt)
        return task.cont

if __name__ == "__main__":
    app = MyGame()
    app.run()
```

### AI Patrol with Custom Behavior
```python
from engine_modules.ai_system import *

# Create custom behavior tree
def create_guard_behavior():
    # Conditions
    def see_player(agent):
        return len(agent.visible_agents) > 0
    
    def at_waypoint(agent):
        return not agent.path or agent.current_path_index >= len(agent.path)
    
    # Actions
    def chase_player(agent, dt):
        if agent.visible_agents:
            agent.set_target(agent.visible_agents[0].position)
            return agent.move_to_next_waypoint(dt)
        return NodeStatus.FAILURE
    
    def patrol(agent, dt):
        return agent.move_to_next_waypoint(dt)
    
    # Build tree
    root = SelectorNode("Guard", [
        SequenceNode("Chase", [
            ConditionNode("SeePlayer", see_player),
            ActionNode("ChaseTarget", chase_player)
        ]),
        SequenceNode("Patrol", [
            ConditionNode("AtWaypoint", at_waypoint),
            ActionNode("ContinuePatrol", patrol)
        ])
    ])
    
    return BehaviorTree(root)
```

### Multi-System Integration
```python
# Weather affects audio
weather_state = weather.get_state()
if weather_state['weather'] == WeatherType.RAIN:
    audio.set_bus_volume(AudioBusType.AMBIENT, 0.5)  # Dampen ambient
    audio.play("rain_loop", loop=True)

# Weather affects physics
friction = weather.weather.get_surface_friction_multiplier()
vehicle.set_surface_friction(friction)

# AI reacts to weather
if weather_state['weather'] in [WeatherType.STORM, WeatherType.HEAVY_RAIN]:
    agent.blackboard['seek_shelter'] = True
```

---

## ⚙️ Configuration

### Quality Presets
```python
# Low-end hardware
gi = create_gi_system(base, quality="low")  # Baked only
volumetric.set_fog_density(0.0)  # Disable
particles.max_particles = 1000

# High-end hardware
gi = create_gi_system(base, quality="ultra")  # Full RT
volumetric.set_fog_density(0.05)  # High density
particles.max_particles = 100000
```

### Memory Budgets
```python
streaming.streaming_manager.memory_budget_mb = 2048.0
streaming.streaming_manager.max_loaded_zones = 9
```

### Performance Tuning
```python
# Reduce update frequency for distant agents
for agent in ai_sys.agents:
    dist = (agent.position - player_pos).length()
    if dist > 50:
        agent.update_interval = 0.5  # Update every 0.5s
    else:
        agent.update_interval = 0.0  # Every frame
```

---

## 🔧 Debugging

### Visualization
```python
# Show navigation mesh
navmesh.create_debug_visual(base.render)

# Show audio sources
for source in audio.sources.values():
    marker = base.loader.loadModel("models/sphere")
    marker.setPos(source.position)
    marker.setScale(0.2)
    marker.reparentTo(base.render)

# Show streaming zones
for zone in streaming.streaming_manager.zones.values():
    sphere = base.loader.loadModel("models/sphere")
    sphere.setPos(zone.center)
    sphere.setScale(zone.radius)
    sphere.setTransparency(True)
    sphere.setAlphaScale(0.2)
```

### Performance Monitoring
```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.frame_times = []
    
    def update(self, dt):
        self.frame_times.append(dt)
        if len(self.frame_times) > 60:
            avg_fps = 1.0 / (sum(self.frame_times) / len(self.frame_times))
            print(f"FPS: {avg_fps:.1f}")
            self.frame_times.clear()
```

---

## 📋 Checklist for New Project

- [ ] Initialize base systems
- [ ] Configure quality settings
- [ ] Set up navigation mesh
- [ ] Configure audio buses
- [ ] Create streaming zones
- [ ] Set up save system
- [ ] Configure weather/time
- [ ] Add global illumination
- [ ] Test save/load
- [ ] Performance profile

---

## 🐛 Troubleshooting

**Issue:** Low FPS with volumetrics  
**Solution:** Reduce fog density or disable: `volumetric.enabled = False`

**Issue:** AI agents stuck  
**Solution:** Regenerate navmesh or check obstacle marking

**Issue:** Audio not 3D  
**Solution:** Ensure `update_listener(camera)` is called every frame

**Issue:** Save file too large  
**Solution:** Enable compression: `save_sys.use_compression = True`

**Issue:** Streaming not loading  
**Solution:** Check `max_concurrent_loads` and zone priorities

---

## 📚 Full Documentation

- `FINAL_IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `AAA_SYSTEMS_COMPLETE_GUIDE.md` - Architecture for 35 systems
- `examples/complete_aaa_demo.py` - Full working example

**Happy Game Development! 🎮**
