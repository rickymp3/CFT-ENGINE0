# CFT-ENGINE0 Visual Scene Editor

## 🎨 Overview

The CFT-ENGINE0 Visual Scene Editor is a comprehensive, user-friendly tool for creating 3D and 2D game scenes without writing code. It features a modern interface with drag-and-drop functionality, real-time preview, and powerful tools for scene composition, animation, and asset management.

## 🚀 Getting Started

### Launch the Editor

```bash
cd /workspaces/CFT-ENGINE0
python editor.py
```

The editor window will open with a complete IDE-style interface.

### Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                        Toolbar                              │
├──────────┬──────────────────────────────────┬───────────────┤
│  Scene   │                                  │               │
│ Hierarchy│         Viewport                 │   Inspector   │
│          │      (3D Preview)                │  Properties   │
│          │                                  │               │
├──────────┼──────────────────────────────────┤               │
│  Asset   │     Animation Timeline           │               │
│ Library  │                                  │               │
├──────────┴──────────────────────────────────┴───────────────┤
│                      Status Bar                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Main Panels

### 1. Viewport (Center)

The **large central area** where you see your 3D/2D scene in real-time.

**Camera Controls:**
- **Left Mouse Drag**: Orbit camera around scene
- **Middle Mouse Drag**: Pan camera (move view)
- **Mouse Wheel**: Zoom in/out
- **Camera Target**: Focus point at (0, 0, 0) by default

**Visual Aids:**
- **Grid**: 20x20 unit grid on the ground plane
- **Axes**: Red (X), Green (Y), Blue (Z) indicators at origin
- **Lighting**: Ambient + directional sun light

### 2. Scene Hierarchy (Left Panel)

**Tree view** of all objects in your scene.

**Features:**
- **Parent-Child Relationships**: Objects indented under parents
- **Selection**: Click to select object (highlights in blue)
- **Expand/Collapse**: Show/hide child objects
- **Context Menu** (planned): Right-click for options

**Object Types:**
- Cubes, spheres, lights, cameras
- Custom models from asset library
- Groups and empties

### 3. Inspector / Properties Panel (Right Panel)

**Edit properties** of the selected object.

**Sections:**

#### Transform
- **Position**: X, Y, Z coordinates
- **Rotation**: Heading, Pitch, Roll (degrees)
- **Scale**: X, Y, Z scale factors

#### Material
- **Metallic**: 0.0 (plastic) to 1.0 (metal)
- **Roughness**: 0.0 (shiny) to 1.0 (matte)
- **Color**: RGBA values (planned)

#### Physics
- **Rigid Body**: Enable physics simulation
- **Mass**: Object weight in kg
- **Collision Shape**: Auto-detected from geometry

#### Animation (when track is selected)
- **Animation Clips**: Dropdown of available animations
- **Playback Speed**: Animation speed multiplier

### 4. Asset Library (Bottom Left)

**Browse and add assets** to your scene.

**Categories:**
- **Models**: Cube, Sphere, Cylinder, Plane, Capsule, Torus
- **Textures**: Brick, Wood, Metal, Fabric, Stone, Glass
- **Materials**: PBR presets (metallic, plastic, wood, glass, emissive)
- **Sounds**: Jump, Footstep, Explosion, Music, Ambient
- **Prefabs**: Player, Enemy, Light Rigs, Camera Rigs, Doors

**Usage:**
1. Click category tab to switch
2. Click asset thumbnail to add to scene
3. Object appears at origin (0, 0, 0)

**Dropbox/Box Integration** (planned):
- Connect cloud storage
- Browse remote assets
- Drag directly into scene

### 5. Animation Timeline (Bottom Center)

**Create keyframe animations** without code.

**Playback Controls:**
- **▶ Play/Pause**: Start/stop animation playback
- **⏹ Stop**: Reset to frame 0
- **⏮ Prev Key**: Jump to previous keyframe
- **⏭ Next Key**: Jump to next keyframe
- **+ Key**: Add keyframe at current frame

**Timeline Scrubber:**
- Drag to scrub through animation
- Frame markers show timing
- Keyframes appear as diamonds on tracks

**Property Tracks:**
- Position.X, Position.Y, Position.Z (RGB colors)
- Rotation (yellow)
- Scale (magenta)

**FPS Control:**
- Default: 30 FPS
- Editable via text input

### 6. Toolbar (Top)

**Quick-access tools** for common actions.

**Primitive Tools:**
- **📦 Cube**: Add box primitive
- **⚫ Sphere**: Add sphere primitive
- **💡 Light**: Add point light
- **📷 Camera**: Add camera object

**Playback:**
- **▶️ Play**: Run scene simulation
- **⏸️ Pause**: Pause simulation

**Toggles:**
- **Physics**: Enable/disable Bullet physics
- **PBR**: Enable/disable PBR rendering

**Settings:**
- **Language**: English / Español / Français

### 7. Status Bar (Bottom)

**Real-time information** about your scene.

**Displays:**
- **FPS**: Frames per second (green when good)
- **Objects**: Total object count in scene
- **Physics Bodies**: Active rigid bodies
- **Mode**: Edit or Play

## 🎮 Workflow Guide

### Creating a Simple Scene

1. **Add Ground Plane**
   - Click **📦 Cube** in toolbar
   - Select object in hierarchy
   - In inspector, set Scale: X=10, Y=10, Z=0.1
   - Set Position: Z=0

2. **Add a Sphere**
   - Click **⚫ Sphere** in toolbar
   - Set Position: Z=3 (above ground)

3. **Add a Light**
   - Click **💡 Light** in toolbar
   - Set Position: X=5, Y=-5, Z=8
   - Adjust color/intensity (inspector)

4. **Arrange Camera**
   - Use mouse controls to frame your scene
   - Current view is what users will see

### Adding Physics

1. **Select Object** in hierarchy
2. **Inspector → Physics**
3. **Check "Rigid Body"**
4. **Set Mass**: e.g., 1.0 kg
5. **Enable Physics** toggle in toolbar
6. **Press F5** to run simulation
7. Object falls with gravity!

### Creating an Animation

1. **Select Object** in hierarchy
2. **Position** object at starting location
3. **Press K** (or click "+ Key") to add keyframe at frame 0
4. **Drag timeline scrubber** to frame 30
5. **Move object** to new position
6. **Press K** again to add second keyframe
7. **Press Space** to preview animation
8. Object smoothly moves between positions!

### Using Materials

1. **Select Object**
2. **Inspector → Material**
3. **Metallic Slider**: 0 for plastic, 1 for metal
4. **Roughness Slider**: 0 for mirror-like, 1 for matte
5. **Enable PBR** toggle in toolbar to see realistic lighting
6. Adjust sliders to see real-time changes

### Organizing the Hierarchy

1. **Drag object** in hierarchy (planned)
2. **Drop onto another object** to parent it
3. **Child objects** move with parent
4. **Example**: Parent lights to camera for headlamp effect

## ⌨️ Keyboard Shortcuts

### Navigation
- **Mouse Drag**: Orbit camera
- **Middle Mouse**: Pan camera
- **Mouse Wheel**: Zoom

### General
- **F1**: Toggle help overlay (planned)
- **F5**: Play/Stop simulation (physics runs)
- **ESC**: Exit editor

### Editing
- **Ctrl+S**: Save scene
- **Ctrl+Z**: Undo last action
- **Ctrl+Y**: Redo action
- **Delete**: Delete selected object

### Animation
- **K**: Add keyframe at current frame
- **Space**: Play/Pause animation timeline

## 🛠️ Advanced Features

### Multilingual Support

**Change UI Language:**
1. Click **Language** dropdown in toolbar
2. Select: English / Español / Français
3. All UI text updates instantly
4. In-game content uses translation files

**For Game Content:**
- Translations stored in `cft_panda3d_engine.py`
- Extend dictionary for custom content

### Physics & Shaders

**Simple Toggles:**
- **Physics Toggle**: Enables Bullet physics simulation
  - Objects with Rigid Body fall, collide, bounce
  - No code required!
  
- **PBR Toggle**: Enables physically based rendering
  - Realistic metal and plastic surfaces
  - Dynamic lighting calculations
  - Material sliders become active

**Inspector Shows Only Relevant Settings:**
- Physics toggle → Mass, friction, restitution visible
- PBR toggle → Metallic, roughness sliders visible

### Animation Timeline

**Keyframe Workflow:**
1. Position object where you want it
2. Press K to "capture" that pose
3. Move timeline scrubber forward
4. Reposition object
5. Press K again
6. Timeline interpolates smoothly between frames

**Advanced** (double-click keyframe, planned):
- **Curve Editor**: Bezier curves for smooth motion
- **Easing**: Ease-in, ease-out, bounce effects
- **Multi-property**: Animate position + rotation + scale together

### Networking & Scripting

**Network Component** (planned):
1. Select object in hierarchy
2. Inspector → Add Component → Network
3. Choose: Client, Server, or Peer
4. Set sync properties (position, rotation)
5. Configure tick rate, interpolation

**Script Component** (planned):
1. Select object
2. Inspector → Add Component → Script
3. Opens code editor with template
4. Auto-completion for engine API
5. Hot-reload on save

### Transform Gizmos (planned)

**Visual Manipulation:**
- **Translate Gizmo**: Drag arrows to move object
- **Rotate Gizmo**: Drag circles to rotate
- **Scale Gizmo**: Drag boxes to scale
- **Snapping**: Hold Shift for grid snapping

## 📊 Status Bar Details

### FPS Counter
- **Green (>50 FPS)**: Performance is good
- **Yellow (30-50 FPS)**: Acceptable
- **Red (<30 FPS)**: Scene too complex

### Objects Count
- Total number of objects in scene
- Includes lights, cameras, primitives

### Physics Bodies
- Number of rigid bodies being simulated
- Higher count = more CPU usage

### Mode Indicator
- **Edit**: Scene editing, physics paused
- **Play**: Simulation running, test your scene

## 💡 Tips & Best Practices

### Performance
- Keep object count reasonable (<500 for smooth FPS)
- Use low-poly models for distant objects
- Limit physics bodies to ~50 active at once
- Bake lighting for static scenes (planned)

### Organization
- **Name objects clearly**: "Player", "Enemy_1", "Platform_Main"
- **Group related objects**: Parent lights to camera rigs
- **Use empties as groups**: Invisible objects that just hold children
- **Prefab reusable groups**: Save to asset library

### Animation
- **Start simple**: Position only, then add rotation
- **Use 30 FPS** for games (smoother than 24, lighter than 60)
- **Preview often**: Press Space to check timing
- **Keyframe sparingly**: Too many keys = harder to edit

### Workflow Efficiency
- **Keyboard shortcuts**: Learn Ctrl+S, K, Space, Delete
- **Duplicate objects**: Ctrl+D (planned) instead of re-creating
- **Lock camera**: Freeze viewport while editing (planned)
- **Layers**: Hide/show groups of objects (planned)

## 🐛 Troubleshooting

### "No models available" Warning
- Some built-in Panda3D models may be missing
- Objects still create but are invisible
- Add custom models via asset library

### Objects Fall Through Floor
- Check physics is enabled (toolbar toggle)
- Ensure floor has "Rigid Body" unchecked (static)
- Or give floor mass of 0

### Animation Not Playing
- Check timeline is not paused (▶ not ⏸)
- Verify keyframes exist (should see diamonds on tracks)
- Select correct object in hierarchy

### Viewport Black/No Lighting
- Check PBR toggle is on
- Verify lights exist in scene (💡)
- Reset camera view (zoom out)

### Slow Performance
- Reduce object count
- Disable PBR if not needed
- Lower physics simulation frequency (config.yaml)
- Close inspector when not editing

## 🚀 Next Steps

### Learn by Example
1. **Try Basic Scene**: Add primitives, move camera
2. **Test Physics**: Enable physics, watch objects fall
3. **Animate Object**: Create 2-keyframe animation
4. **Adjust Materials**: Toggle PBR, adjust sliders

### Extend the Editor
- **Custom Assets**: Add your own models to asset library
- **Script Components**: Attach custom behavior
- **Network Your Scene**: Add multiplayer support
- **Export Scene**: Save and load projects

### Explore Documentation
- **examples/**: Sample projects
- **README.md**: Engine overview
- **IMPLEMENTATION_SUMMARY.md**: Feature list
- **architecture_test_plan.md**: Roadmap

## 📞 Support

For help:
- Check console output for error messages
- Review `config.yaml` for engine settings
- Read `.github/copilot-instructions.md` for dev guidelines
- Examine example scripts in `examples/`

---

**Built for ease of use without sacrificing power.**
**Have fun creating! 🎮✨**
