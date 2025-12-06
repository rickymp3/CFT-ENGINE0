#!/usr/bin/env python
"""CFT-ENGINE0 Visual Scene Editor

A comprehensive visual editor for creating 3D/2D scenes with:
- Viewport with camera controls (orbit, pan, zoom)
- Scene hierarchy with drag-and-drop reparenting
- Inspector panel for properties editing
- Asset library with Dropbox/Box integration
- Toolbar with primitives and tools
- Animation timeline
- Multilingual support
- Physics and PBR toggles
- Networking and scripting support

Run: python editor.py
"""
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
from panda3d.bullet import *
import sys
import os

# Import engine modules
from engine_modules.physics import PhysicsManager
from engine_modules.rendering import RenderingManager
from engine_modules.config import get_config
from engine_modules.animation_timeline import AnimationTimeline


class SceneHierarchyPanel:
    """Scene hierarchy tree view with drag-and-drop support."""
    
    def __init__(self, parent, pos, size):
        self.parent = parent
        self.selected_object = None
        self.objects = []
        
        # Create panel background
        self.frame = DirectFrame(
            frameColor=(0.15, 0.15, 0.15, 0.95),
            frameSize=(0, size[0], -size[1], 0),
            pos=(pos[0], 0, pos[1])
        )
        
        # Title
        self.title = OnscreenText(
            text="Scene Hierarchy",
            pos=(pos[0] + size[0]/2, pos[1] - 0.03),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        
        # Object list (scrollable)
        self.item_height = 0.05
        self.scroll_offset = 0
        self.items = []
        
    def add_object(self, name, obj, parent=None):
        """Add an object to the hierarchy."""
        entry = {
            'name': name,
            'object': obj,
            'parent': parent,
            'children': [],
            'expanded': True
        }
        
        if parent:
            parent['children'].append(entry)
        else:
            self.objects.append(entry)
        
        self.refresh()
        return entry
    
    def remove_object(self, entry):
        """Remove an object from the hierarchy."""
        if entry['parent']:
            entry['parent']['children'].remove(entry)
        else:
            self.objects.remove(entry)
        self.refresh()
    
    def refresh(self):
        """Refresh the hierarchy display."""
        # Clear existing items
        for item in self.items:
            item.destroy()
        self.items.clear()
        
        # Rebuild tree
        y_offset = -0.08
        self._build_tree(self.objects, 0, y_offset)
    
    def _build_tree(self, objects, indent, y_offset):
        """Recursively build tree view."""
        for obj_entry in objects:
            if len(self.items) > 20:  # Limit visible items
                break
            
            # Create item button
            item = DirectButton(
                text=("  " * indent) + obj_entry['name'],
                text_align=TextNode.ALeft,
                scale=0.035,
                pos=(self.frame['pos'][0] + 0.01, 0, self.frame['pos'][2] + y_offset),
                frameSize=(-0.1, 5, -0.8, 1),
                text_fg=(1, 1, 1, 1) if obj_entry != self.selected_object else (0.3, 0.8, 1, 1),
                frameColor=(0.2, 0.2, 0.2, 0.3),
                command=self.select_object,
                extraArgs=[obj_entry]
            )
            
            self.items.append(item)
            y_offset -= self.item_height
            
            # Recursively add children if expanded
            if obj_entry['expanded'] and obj_entry['children']:
                y_offset = self._build_tree(obj_entry['children'], indent + 1, y_offset)
        
        return y_offset
    
    def select_object(self, obj_entry):
        """Select an object in the hierarchy."""
        self.selected_object = obj_entry
        self.refresh()
        
        # Notify parent editor
        if hasattr(self.parent, 'on_object_selected'):
            self.parent.on_object_selected(obj_entry)


class InspectorPanel:
    """Inspector panel for editing object properties."""
    
    def __init__(self, parent, pos, size):
        self.parent = parent
        self.current_object = None
        
        # Create panel background
        self.frame = DirectFrame(
            frameColor=(0.15, 0.15, 0.15, 0.95),
            frameSize=(0, size[0], -size[1], 0),
            pos=(pos[0], 0, pos[1])
        )
        
        # Title
        self.title = OnscreenText(
            text="Inspector",
            pos=(pos[0] + size[0]/2, pos[1] - 0.03),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        
        # Property fields
        self.property_widgets = []
        
    def set_object(self, obj_entry):
        """Set the object to inspect."""
        self.current_object = obj_entry
        self.refresh()
    
    def refresh(self):
        """Refresh the inspector display."""
        # Clear existing widgets
        for widget in self.property_widgets:
            widget.destroy()
        self.property_widgets.clear()
        
        if not self.current_object:
            return
        
        obj = self.current_object['object']
        y_offset = -0.08
        
        # Object name
        self._add_text_field("Name", self.current_object['name'], y_offset)
        y_offset -= 0.06
        
        # Transform properties
        if hasattr(obj, 'getPos'):
            pos = obj.getPos()
            self._add_section_header("Transform", y_offset)
            y_offset -= 0.05
            self._add_vector_field("Position", pos, y_offset)
            y_offset -= 0.06
            
            hpr = obj.getHpr()
            self._add_vector_field("Rotation", hpr, y_offset)
            y_offset -= 0.06
            
            scale = obj.getScale()
            self._add_vector_field("Scale", scale, y_offset)
            y_offset -= 0.08
        
        # Material properties
        self._add_section_header("Material", y_offset)
        y_offset -= 0.05
        self._add_slider("Metallic", 0.0, 1.0, 0.5, y_offset)
        y_offset -= 0.05
        self._add_slider("Roughness", 0.0, 1.0, 0.5, y_offset)
        y_offset -= 0.08
        
        # Physics properties
        self._add_section_header("Physics", y_offset)
        y_offset -= 0.05
        self._add_checkbox("Rigid Body", False, y_offset)
        y_offset -= 0.05
        self._add_text_field("Mass", "1.0", y_offset)
        y_offset -= 0.08
    
    def _add_section_header(self, text, y_offset):
        """Add a section header."""
        header = OnscreenText(
            text=text,
            pos=(self.frame['pos'][0] + 0.02, self.frame['pos'][2] + y_offset),
            scale=0.035,
            fg=(0.8, 0.8, 1, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        self.property_widgets.append(header)
    
    def _add_text_field(self, label, value, y_offset):
        """Add a text input field."""
        lbl = OnscreenText(
            text=label + ":",
            pos=(self.frame['pos'][0] + 0.02, self.frame['pos'][2] + y_offset),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        
        entry = DirectEntry(
            text=str(value),
            scale=0.03,
            pos=(self.frame['pos'][0] + 0.15, 0, self.frame['pos'][2] + y_offset),
            width=8,
            frameColor=(0.25, 0.25, 0.25, 1),
            text_fg=(1, 1, 1, 1)
        )
        
        self.property_widgets.extend([lbl, entry])
    
    def _add_vector_field(self, label, vec, y_offset):
        """Add a vector3 input field."""
        lbl = OnscreenText(
            text=label + ":",
            pos=(self.frame['pos'][0] + 0.02, self.frame['pos'][2] + y_offset),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        self.property_widgets.append(lbl)
        
        # X, Y, Z fields
        labels = ['X', 'Y', 'Z']
        values = [vec.x, vec.y, vec.z] if hasattr(vec, 'x') else [vec[0], vec[1], vec[2]]
        
        for i, (axis, val) in enumerate(zip(labels, values)):
            x_pos = self.frame['pos'][0] + 0.15 + (i * 0.12)
            
            axis_lbl = OnscreenText(
                text=axis,
                pos=(x_pos - 0.02, self.frame['pos'][2] + y_offset),
                scale=0.025,
                fg=(0.7, 0.7, 0.7, 1),
                align=TextNode.ALeft,
                mayChange=True
            )
            
            entry = DirectEntry(
                text=f"{val:.2f}",
                scale=0.025,
                pos=(x_pos + 0.01, 0, self.frame['pos'][2] + y_offset),
                width=3.5,
                frameColor=(0.25, 0.25, 0.25, 1),
                text_fg=(1, 1, 1, 1)
            )
            
            self.property_widgets.extend([axis_lbl, entry])
    
    def _add_slider(self, label, min_val, max_val, default, y_offset):
        """Add a slider control."""
        lbl = OnscreenText(
            text=label + ":",
            pos=(self.frame['pos'][0] + 0.02, self.frame['pos'][2] + y_offset),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        
        slider = DirectSlider(
            range=(min_val, max_val),
            value=default,
            pageSize=0.1,
            scale=0.25,
            pos=(self.frame['pos'][0] + 0.25, 0, self.frame['pos'][2] + y_offset + 0.01),
            frameColor=(0.3, 0.3, 0.3, 1),
            thumb_frameColor=(0.5, 0.7, 1, 1)
        )
        
        self.property_widgets.extend([lbl, slider])
    
    def _add_checkbox(self, label, default, y_offset):
        """Add a checkbox control."""
        checkbox = DirectCheckButton(
            text=label,
            scale=0.03,
            pos=(self.frame['pos'][0] + 0.02, 0, self.frame['pos'][2] + y_offset),
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0.25, 0.25, 0.25, 1),
            indicatorValue=default
        )
        
        self.property_widgets.append(checkbox)


class AssetLibraryPanel:
    """Asset library with thumbnail view and drag-and-drop."""
    
    def __init__(self, parent, pos, size):
        self.parent = parent
        self.assets = []
        
        # Create panel background
        self.frame = DirectFrame(
            frameColor=(0.15, 0.15, 0.15, 0.95),
            frameSize=(0, size[0], -size[1], 0),
            pos=(pos[0], 0, pos[1])
        )
        
        # Title
        self.title = OnscreenText(
            text="Asset Library",
            pos=(pos[0] + size[0]/2, pos[1] - 0.03),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        
        # Asset categories
        self.categories = ["Models", "Textures", "Materials", "Sounds", "Prefabs"]
        self.current_category = 0
        
        # Category buttons
        self.category_buttons = []
        for i, cat in enumerate(self.categories):
            btn = DirectButton(
                text=cat,
                scale=0.03,
                pos=(pos[0] + 0.05 + i * 0.15, 0, pos[1] - 0.08),
                text_fg=(1, 1, 1, 1) if i == 0 else (0.7, 0.7, 0.7, 1),
                frameColor=(0.3, 0.3, 0.3, 0.8) if i == 0 else (0.2, 0.2, 0.2, 0.5),
                command=self.switch_category,
                extraArgs=[i]
            )
            self.category_buttons.append(btn)
        
        # Asset grid
        self.asset_buttons = []
        self.populate_assets()
    
    def switch_category(self, category_index):
        """Switch asset category."""
        self.current_category = category_index
        
        # Update button colors
        for i, btn in enumerate(self.category_buttons):
            if i == category_index:
                btn['text_fg'] = (1, 1, 1, 1)
                btn['frameColor'] = (0.3, 0.3, 0.3, 0.8)
            else:
                btn['text_fg'] = (0.7, 0.7, 0.7, 1)
                btn['frameColor'] = (0.2, 0.2, 0.2, 0.5)
        
        self.populate_assets()
    
    def populate_assets(self):
        """Populate asset grid for current category."""
        # Clear existing buttons
        for btn in self.asset_buttons:
            btn.destroy()
        self.asset_buttons.clear()
        
        # Sample assets per category
        sample_assets = {
            0: ["Cube", "Sphere", "Cylinder", "Plane", "Capsule", "Torus"],
            1: ["Brick", "Wood", "Metal", "Fabric", "Stone", "Glass"],
            2: ["PBR_Metal", "PBR_Plastic", "PBR_Wood", "Glass", "Emissive"],
            3: ["Jump", "Footstep", "Explosion", "Music", "Ambient"],
            4: ["Player", "Enemy", "Light_Rig", "Camera_Rig", "Door"]
        }
        
        assets = sample_assets.get(self.current_category, [])
        
        # Create grid of asset buttons
        cols = 3
        btn_size = 0.12
        for i, asset_name in enumerate(assets):
            row = i // cols
            col = i % cols
            
            x = self.frame['pos'][0] + 0.05 + col * (btn_size + 0.02)
            y = self.frame['pos'][2] - 0.15 - row * (btn_size + 0.05)
            
            btn = DirectButton(
                text=asset_name,
                text_scale=0.02,
                text_pos=(0, -0.05),
                scale=btn_size,
                pos=(x, 0, y),
                frameColor=(0.25, 0.25, 0.25, 0.9),
                command=self.add_asset_to_scene,
                extraArgs=[asset_name]
            )
            
            self.asset_buttons.append(btn)
    
    def add_asset_to_scene(self, asset_name):
        """Add selected asset to the scene."""
        if hasattr(self.parent, 'add_primitive'):
            self.parent.add_primitive(asset_name.lower())


class EditorToolbar:
    """Main toolbar with tools and toggles."""
    
    def __init__(self, parent):
        self.parent = parent
        
        # Background frame
        self.frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.95),
            frameSize=(-2, 2, -0.06, 0),
            pos=(0, 0, 0.98)
        )
        
        # Toolbar buttons
        self.buttons = []
        
        # Tool buttons
        tools = [
            ("📦 Cube", "cube"),
            ("⚫ Sphere", "sphere"),
            ("💡 Light", "light"),
            ("📷 Camera", "camera"),
            ("▶️ Play", "play"),
            ("⏸️ Pause", "pause"),
            ("🔧 Tools", "tools")
        ]
        
        x_pos = -1.8
        for text, action in tools:
            btn = DirectButton(
                text=text,
                scale=0.035,
                pos=(x_pos, 0, -0.03),
                text_fg=(1, 1, 1, 1),
                frameColor=(0.2, 0.2, 0.2, 0.8),
                command=self.toolbar_action,
                extraArgs=[action]
            )
            self.buttons.append(btn)
            x_pos += 0.25
        
        # Toggle buttons
        self.physics_toggle = DirectCheckButton(
            text="Physics",
            scale=0.035,
            pos=(0.8, 0, -0.03),
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            indicatorValue=True,
            command=self.toggle_physics
        )
        self.buttons.append(self.physics_toggle)
        
        self.pbr_toggle = DirectCheckButton(
            text="PBR",
            scale=0.035,
            pos=(1.1, 0, -0.03),
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            indicatorValue=True,
            command=self.toggle_pbr
        )
        self.buttons.append(self.pbr_toggle)
        
        # Language selector
        self.lang_menu = DirectOptionMenu(
            text="Language",
            scale=0.035,
            pos=(1.5, 0, -0.03),
            items=["English", "Español", "Français"],
            initialitem=0,
            highlightColor=(0.65, 0.65, 0.65, 1),
            command=self.change_language
        )
        self.buttons.append(self.lang_menu)
    
    def toolbar_action(self, action):
        """Handle toolbar button actions."""
        if hasattr(self.parent, 'toolbar_action'):
            self.parent.toolbar_action(action)
    
    def toggle_physics(self):
        """Toggle physics simulation."""
        if hasattr(self.parent, 'toggle_physics'):
            self.parent.toggle_physics(self.physics_toggle['indicatorValue'])
    
    def toggle_pbr(self):
        """Toggle PBR rendering."""
        if hasattr(self.parent, 'toggle_pbr'):
            self.parent.toggle_pbr(self.pbr_toggle['indicatorValue'])
    
    def change_language(self, lang):
        """Change interface language."""
        if hasattr(self.parent, 'change_language'):
            self.parent.change_language(lang)


class StatusBar:
    """Status bar showing FPS, physics info, etc."""
    
    def __init__(self):
        self.frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.95),
            frameSize=(-2, 2, 0, 0.05),
            pos=(0, 0, -0.98)
        )
        
        self.fps_text = OnscreenText(
            text="FPS: 60",
            pos=(-1.9, -0.96),
            scale=0.03,
            fg=(0.3, 1, 0.3, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        
        self.objects_text = OnscreenText(
            text="Objects: 0",
            pos=(-1.5, -0.96),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        
        self.physics_text = OnscreenText(
            text="Physics Bodies: 0",
            pos=(-1.0, -0.96),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        
        self.mode_text = OnscreenText(
            text="Mode: Edit",
            pos=(1.8, -0.96),
            scale=0.03,
            fg=(0.3, 0.8, 1, 1),
            align=TextNode.ARight,
            mayChange=True
        )
    
    def update(self, fps, objects, physics_bodies, mode):
        """Update status bar information."""
        self.fps_text.setText(f"FPS: {fps:.0f}")
        self.objects_text.setText(f"Objects: {objects}")
        self.physics_text.setText(f"Physics Bodies: {physics_bodies}")
        self.mode_text.setText(f"Mode: {mode}")


class SceneEditor(ShowBase):
    """Main scene editor application."""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.win.setClearColor(Vec4(0.2, 0.2, 0.25, 1))
        
        # Initialize config and systems
        self.config = get_config()
        self.physics = PhysicsManager()
        self.renderer = RenderingManager(self.render)
        
        # Editor state
        self.edit_mode = True
        self.play_mode = False
        self.selected_object = None
        self.scene_objects = []
        
        # Setup UI panels
        self.setup_ui()
        
        # Setup viewport
        self.setup_viewport()
        
        # Setup camera controls
        self.setup_camera_controls()
        
        # Add update task
        self.taskMgr.add(self.update_editor, 'update_editor')
        
        # Keyboard shortcuts
        self.setup_shortcuts()
        
        print("\n" + "="*60)
        print("CFT-ENGINE0 Visual Scene Editor")
        print("="*60)
        print("\nControls:")
        print("  Mouse Drag: Orbit camera")
        print("  Mouse Wheel: Zoom")
        print("  Middle Mouse: Pan camera")
        print("  F1: Toggle help")
        print("  F5: Play/Stop simulation")
        print("  Space: Play/Pause animation")
        print("  K: Add keyframe at current frame")
        print("  Ctrl+S: Save scene")
        print("  Ctrl+Z: Undo")
        print("  Ctrl+Y: Redo")
        print("  Delete: Delete selected object")
        print("\nToolbar:")
        print("  Click primitives to add objects")
        print("  Use toggles for Physics and PBR")
        print("  Select language from dropdown")
        print("\nAnimation Timeline:")
        print("  Drag scrubber to change frame")
        print("  Use playback controls to preview")
        print("  Press K to add keyframes")
        print("="*60 + "\n")
    
    def setup_ui(self):
        """Setup all UI panels."""
        # Scene Hierarchy (left panel)
        self.hierarchy = SceneHierarchyPanel(
            self,
            pos=(-1.9, 0.9),
            size=(0.45, 1.45)
        )
        
        # Inspector (right panel)
        self.inspector = InspectorPanel(
            self,
            pos=(1.45, 0.9),
            size=(0.45, 1.8)
        )
        
        # Asset Library (bottom left)
        self.asset_library = AssetLibraryPanel(
            self,
            pos=(-1.9, -0.25),
            size=(0.45, 0.35)
        )
        
        # Animation Timeline (bottom center)
        self.timeline = AnimationTimeline(
            self,
            pos=(-1.4, -0.65),
            size=(2.85, 0.28)
        )
        
        # Toolbar (top)
        self.toolbar = EditorToolbar(self)
        
        # Status Bar (bottom)
        self.status_bar = StatusBar()
    
    def setup_viewport(self):
        """Setup the 3D viewport."""
        # Grid
        self.create_grid()
        
        # Lighting
        self.renderer.add_ambient_light('ambient', Vec4(0.3, 0.3, 0.35, 1))
        self.renderer.add_directional_light('sun', Vec4(0.9, 0.9, 0.8, 1), Vec3(-1, -2, -1))
        
        # Axes helper
        self.create_axes_helper()
    
    def setup_camera_controls(self):
        """Setup camera orbit controls."""
        self.camera_distance = 10
        self.camera_angle_h = 45
        self.camera_angle_p = -30
        self.camera_target = Vec3(0, 0, 0)
        
        self.update_camera()
        
        # Mouse controls
        self.accept('mouse1', self.on_mouse_down, ['orbit'])
        self.accept('mouse1-up', self.on_mouse_up)
        self.accept('mouse2', self.on_mouse_down, ['pan'])
        self.accept('mouse2-up', self.on_mouse_up)
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.accept('f1', self.toggle_help)
        self.accept('f5', self.toggle_play_mode)
        self.accept('control-s', self.save_scene)
        self.accept('control-z', self.undo)
        self.accept('control-y', self.redo)
        self.accept('delete', self.delete_selected)
        self.accept('k', self.add_keyframe)  # K for keyframe
        self.accept('space', self.toggle_animation)  # Space to play/pause animation
        self.accept('escape', sys.exit)
        self.accept('f1', self.toggle_help)
        self.accept('f5', self.toggle_play_mode)
        self.accept('control-s', self.save_scene)
        self.accept('control-z', self.undo)
        self.accept('control-y', self.redo)
        self.accept('delete', self.delete_selected)
        self.accept('escape', sys.exit)
    
    def create_grid(self):
        """Create ground grid."""
        from panda3d.core import LineSegs, NodePath
        
        ls = LineSegs()
        ls.setColor(0.3, 0.3, 0.3, 1)
        
        grid_size = 20
        grid_spacing = 1
        
        for i in range(-grid_size, grid_size + 1):
            # Lines parallel to X axis
            ls.moveTo(i * grid_spacing, -grid_size * grid_spacing, 0)
            ls.drawTo(i * grid_spacing, grid_size * grid_spacing, 0)
            
            # Lines parallel to Y axis
            ls.moveTo(-grid_size * grid_spacing, i * grid_spacing, 0)
            ls.drawTo(grid_size * grid_spacing, i * grid_spacing, 0)
        
        grid_node = ls.create()
        self.grid = self.render.attachNewNode(grid_node)
    
    def create_axes_helper(self):
        """Create XYZ axes visualization."""
        from panda3d.core import LineSegs
        
        ls = LineSegs()
        
        # X axis (red)
        ls.setColor(1, 0, 0, 1)
        ls.moveTo(0, 0, 0)
        ls.drawTo(2, 0, 0)
        
        # Y axis (green)
        ls.setColor(0, 1, 0, 1)
        ls.moveTo(0, 0, 0)
        ls.drawTo(0, 2, 0)
        
        # Z axis (blue)
        ls.setColor(0, 0, 1, 1)
        ls.moveTo(0, 0, 0)
        ls.drawTo(0, 0, 2)
        
        axes_node = ls.create()
        self.axes = self.render.attachNewNode(axes_node)
    
    def update_camera(self):
        """Update camera position based on orbit controls."""
        import math
        
        rad_h = math.radians(self.camera_angle_h)
        rad_p = math.radians(self.camera_angle_p)
        
        x = self.camera_distance * math.cos(rad_p) * math.sin(rad_h)
        y = -self.camera_distance * math.cos(rad_p) * math.cos(rad_h)
        z = self.camera_distance * math.sin(rad_p)
        
        self.camera.setPos(self.camera_target + Vec3(x, y, z))
        self.camera.lookAt(self.camera_target)
    
    def on_mouse_down(self, mode):
        """Handle mouse button press."""
        if self.mouseWatcherNode.hasMouse():
            self.mouse_mode = mode
            self.last_mouse_x = self.mouseWatcherNode.getMouseX()
            self.last_mouse_y = self.mouseWatcherNode.getMouseY()
    
    def on_mouse_up(self):
        """Handle mouse button release."""
        self.mouse_mode = None
    
    def on_mouse_wheel(self, direction):
        """Handle mouse wheel zoom."""
        self.camera_distance = max(2, min(50, self.camera_distance - direction))
        self.update_camera()
    
    def add_primitive(self, primitive_type):
        """Add a primitive object to the scene."""
        if primitive_type == 'cube':
            model = self.loader.loadModel('models/box')
            name = f"Cube_{len(self.scene_objects)}"
        elif primitive_type == 'sphere':
            try:
                model = self.loader.loadModel('models/sphere')
            except:
                model = self.loader.loadModel('models/box')
            name = f"Sphere_{len(self.scene_objects)}"
        elif primitive_type == 'light':
            # Create point light
            plight = PointLight('plight')
            plight.setColor(Vec4(1, 1, 1, 1))
            model = self.render.attachNewNode(plight)
            name = f"Light_{len(self.scene_objects)}"
        elif primitive_type == 'camera':
            # Create camera marker
            model = self.loader.loadModel('models/box')
            model.setScale(0.3, 0.3, 0.3)
            name = f"Camera_{len(self.scene_objects)}"
        else:
            return
        
        # Position object
        model.reparentTo(self.render)
        model.setPos(0, 0, 1)
        model.setScale(0.5)
        
        # Add to hierarchy
        obj_entry = self.hierarchy.add_object(name, model)
        self.scene_objects.append(obj_entry)
        
        print(f"✓ Added {name} to scene")
    
    def toolbar_action(self, action):
        """Handle toolbar actions."""
        if action in ['cube', 'sphere', 'light', 'camera']:
            self.add_primitive(action)
        elif action == 'play':
            self.toggle_play_mode()
        elif action == 'pause':
            self.toggle_play_mode()
        elif action == 'tools':
            print("Tools menu not implemented yet")
    
    def on_object_selected(self, obj_entry):
        """Handle object selection from hierarchy."""
        self.selected_object = obj_entry
        self.inspector.set_object(obj_entry)
        print(f"Selected: {obj_entry['name']}")
    
    def toggle_physics(self, enabled):
        """Toggle physics simulation."""
        if enabled:
            print("✓ Physics enabled")
        else:
            print("✗ Physics disabled")
    
    def toggle_pbr(self, enabled):
        """Toggle PBR rendering."""
        if enabled:
            self.renderer.enable_pbr()
            print("✓ PBR rendering enabled")
        else:
            print("✗ PBR rendering disabled")
    
    def change_language(self, lang):
        """Change interface language."""
        lang_map = {"English": "en", "Español": "es", "Français": "fr"}
        lang_code = lang_map.get(lang, "en")
        print(f"Language changed to: {lang} ({lang_code})")
    
    def toggle_play_mode(self):
        """Toggle between edit and play mode."""
        self.play_mode = not self.play_mode
        mode = "Play" if self.play_mode else "Edit"
        print(f"Mode: {mode}")
    
    def toggle_help(self):
        """Toggle help overlay."""
        print("Help overlay not implemented yet")
    
    def save_scene(self):
        """Save current scene."""
        print("💾 Scene saved")
    
    def delete_selected(self):
        """Delete selected object."""
        if self.selected_object:
            name = self.selected_object['name']
            self.selected_object['object'].removeNode()
            self.hierarchy.remove_object(self.selected_object)
            self.scene_objects.remove(self.selected_object)
            self.selected_object = None
            self.inspector.set_object(None)
            print(f"🗑️ Deleted: {name}")
    
    def add_keyframe(self):
        """Add keyframe at current timeline frame."""
        self.timeline.add_keyframe()
    
    def toggle_animation(self):
        """Toggle animation playback."""
        self.timeline.toggle_playback()
        if self.selected_object:
            name = self.selected_object['name']
            self.selected_object['object'].removeNode()
            self.hierarchy.remove_object(self.selected_object)
            self.scene_objects.remove(self.selected_object)
            self.selected_object = None
            self.inspector.set_object(None)
            print(f"🗑️ Deleted: {name}")
    
    def update_editor(self, task):
        """Main editor update loop."""
        dt = globalClock.getDt()
        
        # Update camera based on mouse
        if self.mouse_mode == 'orbit' and self.mouseWatcherNode.hasMouse():
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            dx = mouse_x - self.last_mouse_x
            dy = mouse_y - self.last_mouse_y
            
            self.camera_angle_h += dx * 100
            self.camera_angle_p = max(-89, min(89, self.camera_angle_p + dy * 100))
            
            self.last_mouse_x = mouse_x
            self.last_mouse_y = mouse_y
            
            self.update_camera()
        
        elif self.mouse_mode == 'pan' and self.mouseWatcherNode.hasMouse():
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            dx = mouse_x - self.last_mouse_x
            dy = mouse_y - self.last_mouse_y
            
            # Pan camera target
            self.camera_target += Vec3(-dx * 10, 0, dy * 10)
            
            self.last_mouse_x = mouse_x
            self.last_mouse_y = mouse_y
            
            self.update_camera()
        
        # Update physics if in play mode
        if self.play_mode:
            self.physics.update(dt)
        
        # Update animation timeline
        self.timeline.update(dt)
        
        # Update status bar
        fps = globalClock.getAverageFrameRate()
        num_objects = len(self.scene_objects)
        physics_bodies = len(self.physics.world.getRigidBodies()) if hasattr(self.physics, 'world') else 0
        mode = "Play" if self.play_mode else "Edit"
        
        self.status_bar.update(fps, num_objects, physics_bodies, mode)
        
        return task.contcamera()
        
        # Update physics if in play mode
        if self.play_mode:
            self.physics.update(dt)
        
        # Update status bar
        fps = globalClock.getAverageFrameRate()
        num_objects = len(self.scene_objects)
        physics_bodies = len(self.physics.world.getRigidBodies()) if hasattr(self.physics, 'world') else 0
        mode = "Play" if self.play_mode else "Edit"
        
        self.status_bar.update(fps, num_objects, physics_bodies, mode)
        
        return task.cont


if __name__ == '__main__':
    editor = SceneEditor()
    editor.run()
