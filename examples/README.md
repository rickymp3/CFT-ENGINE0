# CFT-ENGINE0 Examples

This directory contains example scripts demonstrating various features of the CFT-ENGINE0 game engine.

## Available Examples

### 1. Basic Scene (`basic_scene_example.py`)
**What it demonstrates:**
- Simple 3D scene setup
- Camera positioning and controls
- Basic lighting (ambient + directional)
- Ground plane and grid
- Loading 3D models

**How to run:**
```bash
python examples/basic_scene_example.py
```

**Controls:**
- Arrow Keys: Move camera position
- W/S: Zoom in/out
- A/D: Rotate camera left/right
- ESC: Quit

**What you'll see:**
- Green ground plane with grid
- Three colored boxes (red, green, blue) if models are available
- Sun lighting from above

---

### 2. Physics Simulation (`physics_example.py`)
**What it demonstrates:**
- Bullet physics integration
- Rigid body dynamics
- Collision detection
- Gravity simulation
- Different shapes (boxes, spheres, planes)

**How to run:**
```bash
python examples/physics_example.py
```

**Controls:**
- ESC: Quit

**What you'll see:**
- Boxes and spheres falling under gravity

---

### 3. Vehicle Physics Demo (`vehicle_demo.py`)
**What it demonstrates:**
- Advanced Bullet physics features
- Raycast vehicle with suspension
- Wheel physics and steering
- Soft body cloth and rope simulation
- Character controller with jump
- Physics constraints

**How to run:**
```bash
python examples/vehicle_demo.py
```

**Controls:**
- Arrow Up/Down: Accelerate/brake
- Arrow Left/Right: Steer
- Space: Jump (character controller)
- ESC: Quit

**What you'll see:**
- Drivable vehicle with 4-wheel suspension
- Cloth flag waving in the wind
- Rope swinging under gravity
- Character controller capsule

---

### 4. Multiplayer Networking Demo (`multiplayer_demo.py`)
**What it demonstrates:**
- Client-server architecture with asyncio
- Real-time state synchronization
- Player spawning and despawning
- Input handling and prediction
- WebSocket communication
- Lag compensation (ping/pong)

**How to run server:**
```bash
python examples/multiplayer_demo.py server
```

**How to run client (in separate terminal):**
```bash
python examples/multiplayer_demo.py
# or specify server URL:
python examples/multiplayer_demo.py ws://localhost:8765
```

**Controls:**
- W/A/S/D: Move player
- ESC: Quit

**What you'll see:**
- Green box for local player
- Red boxes for remote players
- Real-time position synchronization

**Requirements:**
```bash
pip install websockets
```

---

### 5. Localization Demo (`localization_demo.py`)
**What it demonstrates:**
- Multi-language support (English, Spanish, French)
- Runtime language switching
- Translation loading from JSON files
- String formatting with variables
- Fallback to default language

**How to run:**
```bash
python examples/localization_demo.py
```

**Controls:**
- Click language buttons (EN/ES/FR) to switch
- Click action buttons to see translated messages
- ESC: Quit

**What you'll see:**
- UI with menus, buttons, and labels
- Game info with formatted strings (score, lives, level)
- Real-time language switching

**Translation files:**
- `locales/en.json` - English
- `locales/es.json` - Spanish (Español)
- `locales/fr.json` - French (Français)

---

### 6. PBR Shaders (`pbr_shaders_example.py`)
- Objects colliding with ground plane
- Realistic physics simulation at 60Hz

**Technical details:**
- Uses `BulletWorld` for physics simulation
- Gravity set to -9.81 m/s² (Earth gravity)
- Fixed timestep: 1/180s (physics accuracy)
- Boxes have mass 1.0 kg
- Spheres have mass 0.5 kg

---

### 3. PBR Shaders (`pbr_shaders_example.py`)
**What it demonstrates:**
- Physically Based Rendering (PBR)
- Material properties (metallic, roughness)
- Multiple light sources
- Different surface types

**How to run:**
```bash
python examples/pbr_shaders_example.py
```

**Controls:**
- ESC: Quit

**What you'll see:**
- Row of spheres with different materials:
  - **Smooth Plastic** (red, low roughness)
  - **Semi-Metal** (green, medium metallic)
  - **Polished Metal** (blue, high metallic, low roughness)
  - **Rough Plastic** (yellow, high roughness)
  - **Brushed Metal** (gray, metallic with medium roughness)
- Objects slowly rotating to show reflections
- Multiple colored lights (sun, key light, fill light)

**Technical details:**
- Uses `RenderingManager` from `engine_modules.rendering`
- PBR shader inputs: `metallic`, `roughness`
- Four light sources:
  - Ambient: Soft blue-gray base lighting
  - Directional: Warm sun light
  - Point Light 1: Warm key light
  - Point Light 2: Cool fill light

---

## Prerequisites

All examples require:
- Python 3.12+
- Panda3D 1.10.15
- PyYAML (for configuration)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running from Project Root

All examples should be run from the project root directory:

```bash
# Good (from /workspaces/CFT-ENGINE0)
python examples/basic_scene_example.py

# Bad (don't cd into examples/)
cd examples
python basic_scene_example.py  # This may fail with import errors
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'engine_modules'"
Make sure you're running from the project root directory, not from inside `examples/`.

### "Could not load models/box"
Some examples require Panda3D's built-in models. If models aren't available:
- Physics example: Objects will still simulate but may be invisible
- PBR example: Will show warning and skip material creation
- Basic scene: Will show ground and grid only

### Window doesn't appear
- Check that you're running in an environment with display support
- For headless environments, these examples won't work (they need graphics)
- Try running in GitHub Codespaces with desktop preview

### Performance issues
- Reduce physics simulation accuracy in `physics_example.py`
- Disable PBR in `pbr_shaders_example.py`
- Lower number of objects in examples

## Learning Path

Recommended order for learning:

1. **Start with `basic_scene_example.py`**
   - Understand scene setup, camera, lighting
   - Practice camera controls
   
2. **Try `physics_example.py`**
   - See how physics simulation works
   - Understand rigid bodies and collision
   
3. **Explore `pbr_shaders_example.py`**
   - Learn about advanced rendering
   - Understand material properties

## Next Steps

After exploring these examples:

1. **Modify the examples**
   - Change colors, positions, sizes
   - Add more objects
   - Experiment with different materials

2. **Combine features**
   - Create a scene with physics AND PBR
   - Add user interaction
   - Build a simple game prototype

3. **Read the engine modules**
   - `engine_modules/physics.py` - Physics system
   - `engine_modules/rendering.py` - Rendering pipeline
   - `engine_modules/config.py` - Configuration management

4. **Build your own project**
   - Use `manage.py new-project <name>` to scaffold
   - Reference these examples for patterns
   - Check `config.yaml` for available settings

## Contributing Examples

To add a new example:

1. Create `examples/your_feature_example.py`
2. Follow the naming convention: `<feature>_example.py`
3. Include docstring at top explaining what it demonstrates
4. Add usage instructions and controls
5. Update this README with a new section
6. Test that it runs from project root

Example template:
```python
"""Example: Your feature description.

This example demonstrates:
- Feature 1
- Feature 2
- Feature 3

Run: python examples/your_feature_example.py
"""
from direct.showbase.ShowBase import ShowBase
import sys
sys.path.insert(0, '..')

class YourDemo(ShowBase):
    def __init__(self):
        super().__init__()
        # Your code here
        
if __name__ == '__main__':
    app = YourDemo()
    app.run()
```

## Support

For issues or questions:
- Check the main project README
- Review `architecture_test_plan.md` for design decisions
- Examine `config.yaml` for configuration options
- Read `.github/copilot-instructions.md` for development guidelines
