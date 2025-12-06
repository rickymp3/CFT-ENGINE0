# CFT-ENGINE0 User Guide

Complete guide to using the CFT-ENGINE0 AAA game engine.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Systems](#core-systems)
3. [Advanced Features](#advanced-features)
4. [Performance Optimization](#performance-optimization)
5. [Troubleshooting](#troubleshooting)
6. [API Reference](#api-reference)

---

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/CFT-ENGINE0.git
cd CFT-ENGINE0

# Install dependencies
pip install -r requirements.txt

# Verify installation
python engine.py
```

### Your First Scene

```python
from direct.showbase.ShowBase import ShowBase
from engine_modules.rendering import PBRRenderer
from engine_modules.physics import PhysicsManager

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Setup rendering
        self.renderer = PBRRenderer(self)
        self.renderer.enable_pbr()
        
        # Setup physics
        self.physics = PhysicsManager()
        
        # Create ground
        ground = self.physics.create_static_plane(
            normal=(0, 0, 1),
            position=(0, 0, 0)
        )
        
        # Create player
        self.player = self.physics.create_rigid_body(
            shape='sphere',
            mass=1.0,
            position=(0, 0, 5)
        )
        
        # Update task
        self.taskMgr.add(self.update, 'update')
    
    def update(self, task):
        dt = globalClock.getDt()
        self.physics.update(dt)
        return task.cont

app = MyGame()
app.run()
```

---

## Core Systems

### 🎨 Rendering (PBR & Deferred)

**Setup:**
```python
from engine_modules.rendering import PBRRenderer

renderer = PBRRenderer(base)
renderer.enable_pbr()
renderer.set_quality('high')
```

**Material Creation:**
```python
material = renderer.create_pbr_material(
    albedo_color=(0.8, 0.2, 0.2, 1.0),
    metallic=0.5,
    roughness=0.3,
    albedo_map='textures/brick_albedo.png',
    normal_map='textures/brick_normal.png',
    roughness_map='textures/brick_roughness.png',
    metallic_map='textures/brick_metallic.png'
)
```

**Lighting:**
```python
# Directional light (sun)
sun = renderer.create_directional_light(
    direction=(-1, -1, -1),
    color=(1.0, 0.95, 0.8, 1.0),
    intensity=1.0
)

# Point light
torch = renderer.create_point_light(
    position=(5, 5, 2),
    color=(1.0, 0.5, 0.2, 1.0),
    radius=10.0
)

# Spot light
flashlight = renderer.create_spot_light(
    position=(0, 0, 2),
    direction=(0, 1, 0),
    color=(1.0, 1.0, 1.0, 1.0),
    angle=30.0,
    radius=15.0
)
```

---

### 🌍 Global Illumination

**Setup:**
```python
from engine_modules.global_illumination import GlobalIllumination

gi = GlobalIllumination(base)
gi.enable_lpv()  # Light Propagation Volumes
gi.enable_ssao() # Screen-Space Ambient Occlusion
gi.enable_ssr()  # Screen-Space Reflections
```

**Quality Settings:**
```python
# High-end (RTX 3080+)
gi.set_lpv_quality(grid_resolution=64, cascades=3)
gi.set_ssao_quality(samples=16, radius=0.5)
gi.set_ssr_quality(max_steps=128, step_size=0.1)

# Mid-range (GTX 1660)
gi.set_lpv_quality(grid_resolution=32, cascades=2)
gi.set_ssao_quality(samples=8, radius=0.5)
gi.set_ssr_quality(max_steps=64, step_size=0.2)

# Low-end (GTX 1050)
gi.disable_lpv()
gi.set_ssao_quality(samples=4, radius=0.3)
gi.disable_ssr()
```

**Baked Lighting:**
```python
gi.bake_static_lighting(
    scene=my_scene,
    resolution=512,
    samples=256,
    output_path='lightmaps/scene_01.png'
)
```

---

### 🌦️ Weather System

**Setup:**
```python
from engine_modules.weather_system import WeatherManager

weather = WeatherManager(base)
```

**Weather Presets:**
```python
# Clear sunny day
weather.set_weather('clear')

# Rainy
weather.set_weather('rain', intensity=0.7)

# Snowy
weather.set_weather('snow', intensity=0.5)

# Stormy
weather.set_weather('storm', intensity=0.9)

# Foggy
weather.set_weather('fog', density=0.6)
```

**Custom Weather:**
```python
weather.configure(
    wind_speed=5.0,
    wind_direction=(1, 0, 0),
    precipitation_type='rain',
    precipitation_intensity=0.5,
    fog_density=0.2,
    cloud_coverage=0.7,
    lightning_frequency=0.1  # Strikes per second
)
```

**Smooth Transitions:**
```python
# Transition from clear to rain over 30 seconds
weather.transition_to('rain', duration=30.0, intensity=0.8)
```

---

### 🔊 Spatial Audio

**Setup:**
```python
from engine_modules.audio_system import SpatialAudioManager

audio = SpatialAudioManager(base)
```

**3D Sounds:**
```python
# Create audio source
fireplace = audio.create_source(
    sound_file='sounds/fireplace.ogg',
    position=(5, 10, 0),
    volume=0.8,
    loop=True
)
fireplace.play()

# Ambient zone
forest_ambient = audio.create_ambient_zone(
    sound_file='sounds/forest.ogg',
    center=(0, 0, 0),
    radius=50.0,
    volume=0.5,
    loop=True
)
```

**Listener (Camera/Player):**
```python
# Update listener position each frame
audio.set_listener_position(camera.getPos())
audio.set_listener_orientation(
    forward=camera.getQuat().getForward(),
    up=camera.getQuat().getUp()
)
```

**Effects:**
```python
# Reverb for cave
cave_reverb = audio.create_reverb(
    preset='cave',
    wet=0.7,
    decay_time=3.0
)
audio.apply_effect(my_sound, cave_reverb)

# Low-pass filter for underwater
underwater_filter = audio.create_lowpass_filter(cutoff=1000)
audio.apply_effect(my_sound, underwater_filter)
```

---

### 🤖 AI System

**Setup:**
```python
from engine_modules.ai_system import AIManager

ai = AIManager()
```

**Navigation Mesh:**
```python
# Create navmesh from terrain
navmesh = ai.create_navmesh(
    vertices=terrain_vertices,
    faces=terrain_faces,
    cell_size=0.5,
    agent_radius=0.5,
    agent_height=2.0
)
```

**Pathfinding:**
```python
# Find path from A to B
path = ai.find_path(
    navmesh=navmesh,
    start=(0, 0, 0),
    goal=(10, 20, 5)
)

if path:
    for waypoint in path:
        print(f"Move to {waypoint}")
```

**Behavior Trees:**
```python
from engine_modules.ai_system import BehaviorTree, Sequence, Selector, Action

# Define behaviors
def patrol_behavior(agent):
    # Patrol logic
    return 'success'

def chase_player_behavior(agent):
    # Chase logic
    return 'running'

# Build tree
enemy_ai = BehaviorTree(
    Selector([
        Sequence([
            Condition(lambda: player_visible),
            Action(chase_player_behavior)
        ]),
        Action(patrol_behavior)
    ])
)

# Update AI
def update(dt):
    enemy_ai.tick(enemy_agent)
```

**Steering Behaviors:**
```python
# Seek target
velocity = ai.seek(
    current_position=agent.pos,
    target_position=target.pos,
    max_speed=5.0
)

# Avoid obstacles
velocity = ai.avoid_obstacles(
    current_position=agent.pos,
    current_velocity=agent.velocity,
    obstacles=nearby_obstacles
)

# Flock with others
velocity = ai.flock(
    agent=agent,
    neighbors=nearby_agents,
    separation_weight=1.5,
    alignment_weight=1.0,
    cohesion_weight=1.0
)
```

---

### ⚙️ Physics

**Setup:**
```python
from engine_modules.physics import PhysicsManager

physics = PhysicsManager()
```

**Rigid Bodies:**
```python
# Box
box = physics.create_rigid_body(
    shape='box',
    size=(1, 1, 1),
    mass=1.0,
    position=(0, 0, 10),
    restitution=0.5,  # Bounciness
    friction=0.8
)

# Sphere
ball = physics.create_rigid_body(
    shape='sphere',
    radius=0.5,
    mass=0.5,
    position=(0, 0, 5)
)

# Capsule (for characters)
player = physics.create_rigid_body(
    shape='capsule',
    radius=0.5,
    height=1.8,
    mass=80.0,
    position=(0, 0, 1)
)
```

**Forces:**
```python
# Apply impulse (instant force)
box.apply_central_impulse((0, 0, 100))

# Apply force (gradual)
box.apply_central_force((0, 0, 10))

# Torque (rotation)
box.apply_torque((1, 0, 0))
```

**Constraints:**
```python
# Hinge (door)
hinge = physics.create_hinge_constraint(
    body_a=door,
    body_b=doorframe,
    pivot_a=(0, 0, 0),
    pivot_b=(1, 0, 0),
    axis=(0, 0, 1)
)
hinge.set_limits(min_angle=0, max_angle=90)

# Spring
spring = physics.create_spring_constraint(
    body_a=platform,
    body_b=weight,
    stiffness=100.0,
    damping=5.0
)
```

**Raycasting:**
```python
# Raycast for line-of-sight
hit = physics.raycast(
    origin=(0, 0, 1),
    direction=(0, 1, 0),
    max_distance=100.0
)

if hit:
    print(f"Hit {hit.node} at {hit.position}")
```

---

### 💾 Save/Load System

**Setup:**
```python
from engine_modules.save_system import SaveLoadManager

save_mgr = SaveLoadManager()
```

**Save Game:**
```python
# Define saveable data
game_state = {
    'player': {
        'position': player.getPos(),
        'health': player.health,
        'inventory': player.inventory
    },
    'world': {
        'time_of_day': world.time,
        'weather': weather.current_state
    },
    'npcs': [
        {'id': npc.id, 'position': npc.getPos(), 'state': npc.state}
        for npc in npcs
    ]
}

# Save to slot
save_mgr.save_game(
    slot=0,
    data=game_state,
    metadata={'level': 'forest_01', 'playtime': 1234}
)
```

**Load Game:**
```python
# Load from slot
loaded = save_mgr.load_game(slot=0)

if loaded:
    # Restore player
    player.setPos(loaded['player']['position'])
    player.health = loaded['player']['health']
    
    # Restore world
    world.set_time(loaded['world']['time_of_day'])
    weather.set_weather(loaded['world']['weather'])
```

**Autosave:**
```python
# Enable autosave every 5 minutes
save_mgr.enable_autosave(interval=300.0)

# Trigger checkpoint
save_mgr.autosave(data=game_state)
```

---

### 🌐 Streaming & LOD

**Setup:**
```python
from engine_modules.streaming_system import StreamingManager

streaming = StreamingManager(base)
```

**Define Zones:**
```python
# Register streaming zones
streaming.register_zone(
    zone_id='forest_01',
    center=(0, 0, 0),
    radius=100.0,
    assets=['models/trees.bam', 'textures/grass.png']
)

streaming.register_zone(
    zone_id='village',
    center=(200, 0, 0),
    radius=80.0,
    assets=['models/buildings.bam', 'textures/brick.png']
)
```

**Auto-Streaming:**
```python
# Update based on camera position
def update(task):
    streaming.update(camera.getPos())
    return task.cont
```

**LOD System:**
```python
# Create LOD node
tree_lod = streaming.create_lod_node(
    high_detail='models/tree_high.bam',
    medium_detail='models/tree_medium.bam',
    low_detail='models/tree_low.bam',
    distances=[0, 50, 150]  # Switch distances
)
```

---

## Advanced Features

### 🎬 Cinematic Tools

```python
from engine_modules.advanced_effects import CinematicCamera

camera_system = CinematicCamera(base)

# Dolly shot
camera_system.create_path(
    waypoints=[(0, 0, 5), (10, 0, 5), (10, 10, 5)],
    duration=10.0,
    ease='smooth'
)

# Camera shake
camera_system.shake(intensity=0.5, duration=2.0)

# Depth of field
camera_system.set_dof(
    focal_distance=10.0,
    blur_amount=0.5
)
```

### 💧 Advanced Effects

**Water:**
```python
from engine_modules.advanced_effects import WaterSystem

water = WaterSystem(base)
ocean = water.create_water_plane(
    size=(1000, 1000),
    wave_height=0.5,
    wave_speed=0.2,
    reflections=True,
    refractions=True
)
```

**Particles:**
```python
from engine_modules.advanced_effects import ParticleSystem

particles = ParticleSystem(base)

# Fire
fire = particles.create_emitter(
    type='fire',
    position=(0, 0, 0),
    rate=100,
    lifetime=2.0,
    size_range=(0.1, 0.5)
)

# Smoke
smoke = particles.create_emitter(
    type='smoke',
    position=(0, 0, 2),
    rate=50,
    lifetime=5.0,
    velocity=(0, 0, 1)
)
```

### 🎮 Visual Scripting

```python
from engine_modules.visual_scripting import VisualScriptingSystem

vs = VisualScriptingSystem(base)

# Create script
script = vs.create_script('door_opener')

# Add nodes
trigger = script.add_node('OnTriggerEnter')
open_door = script.add_node('PlayAnimation', animation='door_open')
sound = script.add_node('PlaySound', sound='door_creak.wav')

# Connect nodes
script.connect(trigger.output, open_door.input)
script.connect(trigger.output, sound.input)

# Execute
script.run()
```

---

## Performance Optimization

### 🔍 Profiling

```python
from engine_modules.profiler import create_profiler

profiler = create_profiler(base)

# Profile code sections
def update(task):
    with profiler.zone("physics"):
        physics.update(dt)
    
    with profiler.zone("ai"):
        ai.update(dt)
    
    with profiler.zone("rendering"):
        renderer.update(dt)
    
    profiler.update(dt)
    return task.cont

# View overlay (press F3)
profiler.toggle_overlay()

# Save report
profiler.save_report("session_profile.json")
```

### 📊 Performance Tips

**Rendering:**
- Use LOD for distant objects
- Enable frustum culling
- Batch similar materials
- Use texture atlases
- Limit shadow resolution

**Physics:**
- Use compound shapes for complex objects
- Enable sleeping for static objects
- Reduce physics substeps if possible
- Use simplified collision shapes

**AI:**
- Throttle perception updates
- Cache pathfinding results
- Use spatial hashing for neighbor queries
- Limit behavior tree depth

**Memory:**
- Unload unused assets
- Use object pooling for particles
- Compress textures
- Stream large worlds

---

## Troubleshooting

### Common Issues

**Q: Low FPS on high-end hardware**
```python
# Check if VSync is limiting framerate
base.win.set_vsync(False)

# Verify GPU usage
profiler.print_gpu_stats()

# Check for CPU bottlenecks
profiler.print_zone_stats()
```

**Q: Memory growing over time**
```python
# Enable leak detection
from engine_modules.profiler import MemoryProfiler

mem_prof = MemoryProfiler()
mem_prof.take_snapshot()

# ... run game for a while ...

mem_prof.take_snapshot()
leaks = mem_prof.detect_leaks()
if leaks:
    print(f"Leak detected: {leaks}")
```

**Q: Physics objects falling through floor**
```python
# Increase simulation quality
physics.set_substeps(10)

# Reduce velocities
body.set_max_velocity(100.0)

# Use continuous collision detection
body.set_ccd_motion_threshold(0.1)
```

**Q: Audio crackling**
```python
# Increase buffer size
audio.set_buffer_size(2048)

# Check for CPU spikes
profiler.print_cpu_stats()
```

---

## API Reference

### Quick Reference

**Rendering:**
- `PBRRenderer.create_pbr_material()` - Create PBR material
- `PBRRenderer.create_directional_light()` - Create sun light
- `PBRRenderer.set_quality()` - Set rendering quality

**Physics:**
- `PhysicsManager.create_rigid_body()` - Create physics object
- `PhysicsManager.raycast()` - Cast ray for collision
- `PhysicsManager.update(dt)` - Step simulation

**AI:**
- `AIManager.create_navmesh()` - Generate navigation mesh
- `AIManager.find_path()` - A* pathfinding
- `BehaviorTree.tick()` - Execute AI logic

**Audio:**
- `SpatialAudioManager.create_source()` - 3D sound
- `SpatialAudioManager.set_listener_position()` - Update camera
- `SpatialAudioManager.create_reverb()` - Apply effect

**Save/Load:**
- `SaveLoadManager.save_game()` - Save to slot
- `SaveLoadManager.load_game()` - Load from slot
- `SaveLoadManager.enable_autosave()` - Auto-save feature

See `AAA_SYSTEMS_COMPLETE_GUIDE.md` for complete API documentation.

---

**Happy game development with CFT-ENGINE0!** 🎮
