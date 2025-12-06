# CFT-ENGINE0 AAA Features Documentation

This document provides detailed technical information about the AAA-quality features implemented in CFT-ENGINE0.

## Table of Contents
1. [Advanced Physics](#advanced-physics)
2. [Deferred PBR Rendering](#deferred-pbr-rendering)
3. [Skeletal Animation & IK](#skeletal-animation--ik)
4. [Networking & Multiplayer](#networking--multiplayer)
5. [Asset Pipeline](#asset-pipeline)
6. [Visual Scripting](#visual-scripting)
7. [Localization System](#localization-system)

---

## Advanced Physics

**Module:** `engine_modules/physics.py`

### Features

#### 1. Raycast Vehicle System
Creates drivable vehicles with realistic suspension and wheel physics.

```python
from engine_modules.physics import PhysicsManager

physics = PhysicsManager()

# Create chassis
chassis = physics.create_box("car_chassis", Vec3(2, 4, 1), mass=800.0, pos=Point3(0, 0, 2))

# Create vehicle
vehicle = physics.create_vehicle(chassis, "race_car")

# Add wheels
physics.add_wheel(vehicle, 
    connection_point=Vec3(-1, 2, 0.5),  # Front left
    direction=Vec3(0, 0, -1),           # Down
    axle=Vec3(-1, 0, 0),                # Left
    suspension_rest_length=0.5,
    wheel_radius=0.4,
    is_front_wheel=True
)

# Control vehicle
vehicle.setEngineForce(2000, wheel_index)
vehicle.setBrake(100, wheel_index)
vehicle.setSteeringValue(0.5, wheel_index)
```

**Parameters:**
- `connection_point`: Where wheel connects to chassis (local space)
- `direction`: Suspension direction (usually down)
- `axle`: Wheel rotation axis
- `suspension_rest_length`: Suspension travel distance
- `wheel_radius`: Radius for collision and rendering
- `is_front_wheel`: Whether wheel can steer

#### 2. Soft Bodies
Deformable physics objects like cloth and rope.

```python
# Create cloth patch
cloth = physics.create_soft_body_patch(
    name="flag",
    corner1=Point3(-5, 5, 5),
    corner2=Point3(-3, 5, 5),
    corner3=Point3(-5, 5, 3),
    corner4=Point3(-3, 5, 3),
    res_x=10,  # Resolution
    res_y=10,
    fixed_corners=1  # Bitfield: 1=top-left, 2=top-right, 4=bottom-left, 8=bottom-right
)

# Create rope
rope = physics.create_soft_body_rope(
    name="rope",
    start=Point3(0, 0, 10),
    end=Point3(0, 0, 0),
    segments=20,
    fixed_ends=1  # Bitfield: 1=start, 2=end
)
```

#### 3. Character Controller
Capsule-based controller for player movement with step climbing.

```python
character = physics.create_character_controller(
    name="player",
    radius=0.5,
    height=1.8,
    step_height=0.4
)

# Move character
character.setLinearVelocity(Vec3(x, y, z))
```

#### 4. Physics Constraints
Joint systems connecting rigid bodies.

```python
# Hinge (door hinge, wheel axle)
physics.add_hinge_constraint(
    node_a, node_b,
    pivot_a=Point3(0, 0, 0),
    pivot_b=Point3(1, 0, 0),
    axis_a=Vec3(0, 0, 1),
    axis_b=Vec3(0, 0, 1),
    limits=(-90, 90)  # Angle limits in degrees
)

# Slider (piston, drawer)
physics.add_slider_constraint(
    node_a, node_b,
    frame_a=TransformState.makePos(Point3(0, 0, 0)),
    frame_b=TransformState.makePos(Point3(1, 0, 0)),
    limits=(-2, 2)  # Distance limits
)

# Cone-twist (ragdoll joint, ball-socket)
physics.add_cone_twist_constraint(
    node_a, node_b,
    frame_a=TransformState.makePos(Point3(0, 0, 0)),
    frame_b=TransformState.makePos(Point3(1, 0, 0))
)
```

#### 5. Trigger Volumes
Non-colliding volumes that detect overlaps.

```python
def on_player_enter(overlapping_nodes):
    print(f"Player entered trigger! {len(overlapping_nodes)} objects inside")

trigger = physics.create_trigger(
    name="door_trigger",
    shape=physics.create_box_shape(Vec3(2, 2, 3)),
    callback=on_player_enter
)

# Check overlaps each frame
physics.check_trigger_overlaps(trigger)
```

---

## Deferred PBR Rendering

**Module:** `engine_modules/deferred_renderer.py`

### Architecture

Deferred rendering separates geometry and lighting into multiple passes:

1. **G-Buffer Pass**: Render scene geometry to multiple textures
2. **Lighting Pass**: Calculate lighting using G-buffer data
3. **Post-Processing**: Apply effects like bloom, SSAO, HDR

### Usage

```python
from engine_modules.deferred_renderer import DeferredRenderer

renderer = DeferredRenderer(base)

# Set material properties
renderer.set_material(
    node_path,
    albedo=(1.0, 0.8, 0.6),
    metallic=0.8,
    roughness=0.2,
    ao=1.0
)

# Add lights
renderer.add_directional_light(
    direction=Vec3(-1, -1, -1),
    color=(1.0, 0.95, 0.8),
    intensity=1.0
)

renderer.add_point_light(
    position=Point3(0, 0, 5),
    color=(1.0, 0.5, 0.2),
    intensity=10.0,
    radius=15.0
)

renderer.add_spot_light(
    position=Point3(0, 0, 10),
    direction=Vec3(0, 0, -1),
    color=(1.0, 1.0, 1.0),
    intensity=20.0,
    radius=20.0,
    angle=45.0
)

# Enable post-processing
renderer.enable_bloom(threshold=0.8, intensity=0.3, blur_passes=5)
renderer.enable_ssao(radius=0.5, bias=0.025, samples=16)
renderer.enable_hdr(exposure=1.0, gamma=2.2)

# Render
renderer.render()
```

### PBR Material Properties

- **Albedo**: Base color (RGB)
- **Metallic**: 0.0 = dielectric (wood, plastic), 1.0 = metal (iron, gold)
- **Roughness**: 0.0 = smooth (mirror), 1.0 = rough (concrete)
- **AO**: Ambient occlusion (darkens crevices)

### Cook-Torrance BRDF

The shader implements physically-based lighting using:

**Fresnel (Fresnel-Schlick approximation):**
```glsl
vec3 F = F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
```

**Normal Distribution Function (GGX/Trowbridge-Reitz):**
```glsl
float D = (roughness^2) / (π * ((NdotH^2 * (roughness^2 - 1) + 1)^2));
```

**Geometry Function (Smith's Schlick-GGX):**
```glsl
float G = G1(NdotV) * G1(NdotL);
```

---

## Skeletal Animation & IK

**Module:** `engine_modules/animation.py`

### Animation Controller

```python
from engine_modules.animation import AnimationController

controller = AnimationController(actor)

# Load animations
controller.load_animation("walk", "models/character-walk.egg")
controller.load_animation("run", "models/character-run.egg")
controller.load_animation("idle", "models/character-idle.egg")

# Play animation
controller.play("walk", loop=True)

# Blend between animations
controller.set_blend_weight("walk", 0.7)
controller.set_blend_weight("run", 0.3)

# Update each frame
controller.update(dt)
```

### IK Solver (FABRIK)

Forward And Backward Reaching Inverse Kinematics for procedural limb placement.

```python
from engine_modules.animation import IKChain

# Create IK chain (e.g., arm: shoulder -> elbow -> wrist)
ik_chain = IKChain([shoulder_joint, elbow_joint, wrist_joint])

# Solve to reach target
ik_chain.solve(target_position=Point3(5, 2, 1), tolerance=0.01, max_iterations=10)

# Apply to skeleton
ik_chain.apply()
```

**Algorithm:**
1. **Forward reaching**: Start from end effector, move toward target
2. **Backward reaching**: Start from root, restore constraints
3. **Iterate**: Repeat until within tolerance or max iterations

### Animation State Machine

```python
from engine_modules.animation import AnimationState

# Create states
idle_state = AnimationState("idle", "idle", loop=True)
walk_state = AnimationState("walk", "walk", loop=True)
jump_state = AnimationState("jump", "jump", loop=False)

# Add transitions
idle_state.add_transition("to_walk", walk_state, 0.3)  # 0.3s blend time
walk_state.add_transition("to_idle", idle_state, 0.3)
walk_state.add_transition("to_jump", jump_state, 0.1)

# Set as current
controller.set_state(idle_state)

# Transition
controller.transition("to_walk")
```

### Blend Trees

```python
from engine_modules.animation import AnimationBlendTree, LerpBlendNode

# Create blend tree
blend_tree = AnimationBlendTree()

# Lerp between walk and run based on speed
walk_run_blend = LerpBlendNode("walk_run")
walk_run_blend.add_input(controller.get_animation("walk"))
walk_run_blend.add_input(controller.get_animation("run"))

blend_tree.set_root(walk_run_blend)

# Control blend (0.0 = walk, 1.0 = run)
walk_run_blend.set_blend_factor(speed / max_speed)

# Evaluate
result = blend_tree.evaluate(dt)
```

---

## Networking & Multiplayer

**Module:** `engine_modules/networking.py`

### Server Setup

```python
from engine_modules.networking import NetworkServer, MessageType

server = NetworkServer(host="0.0.0.0", port=8765)

# Register handlers
def on_player_input(message):
    client_id = message.client_id
    input_data = message.data.get('input', {})
    # Process input...

server.register_handler(MessageType.INPUT, on_player_input)

# Start server
await server.start()
```

### Client Setup

```python
from engine_modules.networking import NetworkClient, MessageType

client = NetworkClient(client_id="player123")

# Register handlers
def on_state_update(data):
    for player_id, state in data.items():
        update_player_position(player_id, state['position'])

client.register_handler(MessageType.STATE_UPDATE, on_state_update)

# Connect
await client.connect("ws://game-server.com:8765")

# Send input
await client.send_input({'keys': ['W', 'A'], 'mouse': (100, 200)})

# Receive loop
await client.receive_loop()
```

### Message Types

- `CONNECT` / `DISCONNECT`: Player join/leave
- `STATE_UPDATE`: Periodic world state synchronization
- `INPUT`: Player input for server-side processing
- `SPAWN` / `DESPAWN`: Entity creation/destruction
- `PING` / `PONG`: Latency measurement
- `CHAT`: Text messages
- `CUSTOM`: Game-specific messages

### Lag Compensation

```python
# Client-side prediction
await client.send_input(input_data)
local_player.apply_input(input_data)  # Don't wait for server

# Server reconciliation
if server_position != predicted_position:
    local_player.set_position(server_position)  # Snap back
```

---

## Asset Pipeline

**Module:** `engine_modules/asset_pipeline.py`

### Import from Cloud

```python
from engine_modules.asset_pipeline import AssetPipeline

pipeline = AssetPipeline(cache_dir="./asset_cache")

# Register Dropbox
pipeline.register_dropbox(access_token="YOUR_DROPBOX_TOKEN")

# Import asset from Dropbox
asset_id = pipeline.import_asset(
    source_path="/GameAssets/models/character.obj",
    asset_type="model",
    cloud_provider="dropbox",
    name="Main Character",
    tags=["character", "player"]
)

# Load into scene
model = pipeline.load_asset(asset_id)
model.reparentTo(render)
```

### Import from Local

```python
asset_id = pipeline.import_asset(
    source_path="./local_assets/terrain.obj",
    asset_type="model",
    name="Terrain",
    tags=["environment", "terrain"]
)
```

### Search Assets

```python
# Search by name
results = pipeline.search_assets(query="character")

# Search by type
models = pipeline.search_assets(asset_type="model")

# Search by tags
player_assets = pipeline.search_assets(tags=["player"])

# Get metadata
for asset in results:
    print(f"{asset.name}: {asset.file_size} bytes, {asset.format}")
```

### Cache Management

Assets are automatically cached with:
- **MD5 checksums**: Detect changes
- **Metadata**: Name, type, tags, dependencies
- **Format conversion**: .obj/.fbx/.gltf → .bam
- **Dependency tracking**: Textures, materials

---

## Visual Scripting

**Module:** `engine_modules/visual_scripting.py`

### Create Script

```python
from engine_modules.visual_scripting import VisualScript

script = VisualScript(name="PlayerController")

# Add nodes
begin_play = script.add_node("Event_BeginPlay", x=100, y=100)
print_node = script.add_node("Print", x=300, y=100)

# Connect nodes
script.connect(
    from_pin=f"{begin_play.node_id}:Exec",
    to_pin=f"{print_node.node_id}:Exec"
)

# Set parameters
print_node.inputs[1].default_value = "Game started!"

# Generate Python code
python_code = script.generate_python()
print(python_code)

# Save to file
script.save("scripts/player_controller.json")
```

### Available Node Types

**Events:**
- `Event_BeginPlay`: Triggered once at start
- `Event_Tick`: Triggered every frame (provides DeltaTime)
- `Event_KeyPressed`: Triggered on key input (provides Key)

**Math:**
- `Math_Add`: A + B
- `Math_Multiply`: A * B

**Logic:**
- `Logic_Branch`: If/else based on condition
- `Logic_Compare`: Compare two values (equal, greater, less)

**Node Operations:**
- `Node_SetPosition`: Set object position
- `Node_GetPosition`: Get object position

**Utility:**
- `Print`: Debug output

### Visual Editor UI

```python
from engine_modules.visual_scripting import NodeEditorUI
import tkinter as tk

root = tk.Tk()
root.title("Visual Script Editor")

editor = NodeEditorUI(root)

# Editor provides:
# - Toolbar with node palette
# - Canvas for node placement
# - Connection system
# - Code generation
# - Save/load

root.mainloop()
```

---

## Localization System

**Module:** `engine_modules/localization.py`

### Setup

```python
from engine_modules.localization import init_localization, _, set_language

# Initialize (loads all .json/.yaml files from locales/)
loc = init_localization(locale_dir="./locales", default_language="en")

# Check available languages
print(loc.get_available_languages())  # ['en', 'es', 'fr']
```

### Translation Files

**locales/en.json:**
```json
{
  "ui": {
    "menu": {
      "file": "File",
      "edit": "Edit"
    },
    "buttons": {
      "ok": "OK",
      "cancel": "Cancel"
    }
  },
  "game": {
    "score": "Score: {score}",
    "level": "Level {level}"
  }
}
```

**locales/es.json:**
```json
{
  "ui": {
    "menu": {
      "file": "Archivo",
      "edit": "Editar"
    },
    "buttons": {
      "ok": "Aceptar",
      "cancel": "Cancelar"
    }
  },
  "game": {
    "score": "Puntuación: {score}",
    "level": "Nivel {level}"
  }
}
```

### Usage

```python
# Basic translation
file_text = _("ui.menu.file")  # Returns "File" (English)

# Change language
set_language("es")
file_text = _("ui.menu.file")  # Returns "Archivo" (Spanish)

# String formatting
score_text = _("game.score", score=1234)  # "Score: 1234" / "Puntuación: 1234"
level_text = _("game.level", level=5)     # "Level 5" / "Nivel 5"

# Plural forms
loc.plural("ui.item", count=1)   # "1 item"
loc.plural("ui.item", count=5)   # "5 items"
```

### Runtime Translation Updates

```python
# Add translation at runtime
loc.add_translation("en", "ui.new_button", "New")
loc.add_translation("es", "ui.new_button", "Nuevo")

# Save to file
loc.save_language("en", format="json")
loc.save_language("es", format="yaml")
```

### Fallback System

If a translation is missing:
1. Try current language
2. Try default language
3. Return key itself

```python
set_language("fr")
text = _("missing.key")  # Returns "missing.key" (not found in any language)
```

---

## Example Projects

See the `examples/` directory for complete demonstrations:

1. **vehicle_demo.py**: Raycast vehicles, soft bodies, character controller
2. **multiplayer_demo.py**: Client-server networking with WebSockets
3. **localization_demo.py**: Multi-language UI with runtime switching
4. **pbr_shaders_example.py**: PBR materials with different roughness/metallic
5. **physics_example.py**: Basic rigid body physics

Run any example:
```bash
python examples/vehicle_demo.py
python examples/multiplayer_demo.py server  # In one terminal
python examples/multiplayer_demo.py         # In another terminal
python examples/localization_demo.py
```

---

## Performance Tips

### Physics
- Use compound shapes instead of mesh shapes when possible
- Reduce soft body resolution for distant objects
- Disable sleeping for critical objects only
- Use trigger volumes instead of continuous collision checks

### Rendering
- Batch objects with same material
- Use texture atlases to reduce draw calls
- Limit number of dynamic lights (use light baking for static lights)
- Reduce post-processing quality for lower-end hardware

### Networking
- Send state updates at fixed tick rate (20-60 Hz)
- Use delta compression for large state
- Implement interest management (only send nearby entities)
- Compress messages before sending

### Asset Pipeline
- Pre-convert assets to .bam format offline
- Use async loading for large assets
- Implement LOD (Level of Detail) system
- Cache frequently-used assets in memory

---

## API Reference

For detailed API documentation, see:
- `EDITOR_GUIDE.md` - Visual editor usage
- `QUICK_REFERENCE.md` - Common code patterns
- `IMPLEMENTATION_SUMMARY.md` - Architecture overview
- Module docstrings in `engine_modules/*.py`
