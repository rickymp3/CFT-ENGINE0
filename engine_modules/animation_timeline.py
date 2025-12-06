"""Animation Timeline Panel for CFT-ENGINE0 Editor

Provides keyframe animation capabilities with:
- Timeline scrubbing
- Keyframe creation and editing
- Curve editor
- Animation playback controls
"""
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *


class AnimationTimeline:
    """Animation timeline with keyframe editing."""
    
    def __init__(self, parent, pos, size):
        self.parent = parent
        self.current_frame = 0
        self.total_frames = 120  # 4 seconds at 30fps
        self.fps = 30
        self.playing = False
        self.keyframes = {}  # {frame: {property: value}}
        
        # Create panel background
        self.frame = DirectFrame(
            frameColor=(0.12, 0.12, 0.12, 0.95),
            frameSize=(0, size[0], -size[1], 0),
            pos=(pos[0], 0, pos[1])
        )
        
        # Title
        self.title = OnscreenText(
            text="Animation Timeline",
            pos=(pos[0] + size[0]/2, pos[1] - 0.03),
            scale=0.035,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        
        # Playback controls
        self.setup_playback_controls(pos, size)
        
        # Timeline scrubber
        self.setup_timeline(pos, size)
        
        # Property tracks
        self.tracks = []
        self.setup_property_tracks(pos, size)
    
    def setup_playback_controls(self, pos, size):
        """Setup playback control buttons."""
        btn_y = pos[1] - 0.08
        btn_x = pos[0] + 0.05
        
        # Play/Pause button
        self.play_btn = DirectButton(
            text="▶",
            scale=0.03,
            pos=(btn_x, 0, btn_y),
            text_fg=(0.3, 1, 0.3, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            command=self.toggle_playback
        )
        
        # Stop button
        self.stop_btn = DirectButton(
            text="⏹",
            scale=0.03,
            pos=(btn_x + 0.08, 0, btn_y),
            text_fg=(1, 0.3, 0.3, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            command=self.stop_playback
        )
        
        # Previous keyframe
        self.prev_key_btn = DirectButton(
            text="⏮",
            scale=0.03,
            pos=(btn_x + 0.16, 0, btn_y),
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            command=self.goto_prev_keyframe
        )
        
        # Next keyframe
        self.next_key_btn = DirectButton(
            text="⏭",
            scale=0.03,
            pos=(btn_x + 0.24, 0, btn_y),
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            command=self.goto_next_keyframe
        )
        
        # Add keyframe button
        self.add_key_btn = DirectButton(
            text="+ Key",
            scale=0.03,
            pos=(btn_x + 0.35, 0, btn_y),
            text_fg=(0.3, 0.8, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            command=self.add_keyframe
        )
        
        # Frame counter
        self.frame_label = OnscreenText(
            text=f"Frame: {self.current_frame}/{self.total_frames}",
            pos=(pos[0] + size[0] - 0.15, btn_y),
            scale=0.03,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ARight,
            mayChange=True
        )
        
        # FPS input
        fps_label = OnscreenText(
            text="FPS:",
            pos=(pos[0] + size[0] - 0.35, btn_y),
            scale=0.025,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ARight,
            mayChange=False
        )
        
        self.fps_entry = DirectEntry(
            text=str(self.fps),
            scale=0.025,
            pos=(pos[0] + size[0] - 0.25, 0, btn_y),
            width=3,
            frameColor=(0.2, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self.update_fps
        )
    
    def setup_timeline(self, pos, size):
        """Setup timeline scrubber."""
        timeline_y = pos[1] - 0.15
        timeline_width = size[0] - 0.1
        
        # Timeline background
        self.timeline_bg = DirectFrame(
            frameColor=(0.18, 0.18, 0.18, 1),
            frameSize=(0, timeline_width, -0.05, 0),
            pos=(pos[0] + 0.05, 0, timeline_y)
        )
        
        # Timeline scrubber
        self.scrubber = DirectSlider(
            range=(0, self.total_frames),
            value=self.current_frame,
            pageSize=1,
            scale=(timeline_width * 0.9, 1, 0.04),
            pos=(pos[0] + 0.05 + timeline_width * 0.05, 0, timeline_y - 0.025),
            frameColor=(0.25, 0.25, 0.25, 1),
            thumb_frameColor=(0.3, 0.8, 1, 1),
            command=self.on_scrub
        )
        
        # Frame markers
        self.frame_markers = []
        num_markers = 10
        for i in range(num_markers + 1):
            frame_num = int((i / num_markers) * self.total_frames)
            x_pos = pos[0] + 0.05 + (i / num_markers) * timeline_width
            
            marker = OnscreenText(
                text=str(frame_num),
                pos=(x_pos, timeline_y - 0.07),
                scale=0.02,
                fg=(0.6, 0.6, 0.6, 1),
                align=TextNode.ALeft,
                mayChange=False
            )
            self.frame_markers.append(marker)
    
    def setup_property_tracks(self, pos, size):
        """Setup property animation tracks."""
        track_y = pos[1] - 0.22
        
        # Sample tracks for common properties
        properties = [
            ("Position.X", (1, 0.3, 0.3, 1)),
            ("Position.Y", (0.3, 1, 0.3, 1)),
            ("Position.Z", (0.3, 0.3, 1, 1)),
            ("Rotation", (1, 1, 0.3, 1)),
            ("Scale", (1, 0.5, 1, 1))
        ]
        
        for prop_name, color in properties:
            track = self.create_property_track(prop_name, color, pos, size, track_y)
            self.tracks.append(track)
            track_y -= 0.04
    
    def create_property_track(self, name, color, pos, size, y_offset):
        """Create a single property track."""
        # Track label
        label = OnscreenText(
            text=name,
            pos=(pos[0] + 0.02, y_offset),
            scale=0.022,
            fg=color,
            align=TextNode.ALeft,
            mayChange=False
        )
        
        # Track line (shows keyframes)
        from panda3d.core import LineSegs
        
        track_data = {
            'name': name,
            'color': color,
            'label': label,
            'keyframes': []
        }
        
        return track_data
    
    def toggle_playback(self):
        """Toggle animation playback."""
        self.playing = not self.playing
        
        if self.playing:
            self.play_btn['text'] = "⏸"
            self.play_btn['text_fg'] = (1, 1, 0.3, 1)
            print(f"▶ Playing animation at {self.fps} FPS")
        else:
            self.play_btn['text'] = "▶"
            self.play_btn['text_fg'] = (0.3, 1, 0.3, 1)
            print("⏸ Paused animation")
    
    def stop_playback(self):
        """Stop animation and reset to frame 0."""
        self.playing = False
        self.current_frame = 0
        self.scrubber['value'] = 0
        self.play_btn['text'] = "▶"
        self.play_btn['text_fg'] = (0.3, 1, 0.3, 1)
        self.update_frame_display()
        print("⏹ Stopped animation")
    
    def goto_prev_keyframe(self):
        """Jump to previous keyframe."""
        # Find previous keyframe
        keyframe_frames = sorted([f for f in self.keyframes.keys() if f < self.current_frame])
        
        if keyframe_frames:
            self.current_frame = keyframe_frames[-1]
            self.scrubber['value'] = self.current_frame
            self.update_frame_display()
            print(f"⏮ Jump to keyframe at frame {self.current_frame}")
        else:
            print("No previous keyframe")
    
    def goto_next_keyframe(self):
        """Jump to next keyframe."""
        # Find next keyframe
        keyframe_frames = sorted([f for f in self.keyframes.keys() if f > self.current_frame])
        
        if keyframe_frames:
            self.current_frame = keyframe_frames[0]
            self.scrubber['value'] = self.current_frame
            self.update_frame_display()
            print(f"⏭ Jump to keyframe at frame {self.current_frame}")
        else:
            print("No next keyframe")
    
    def add_keyframe(self):
        """Add keyframe at current frame."""
        if self.current_frame not in self.keyframes:
            self.keyframes[self.current_frame] = {}
        
        # Store current object properties
        if hasattr(self.parent, 'selected_object') and self.parent.selected_object:
            obj = self.parent.selected_object['object']
            
            self.keyframes[self.current_frame] = {
                'position': obj.getPos() if hasattr(obj, 'getPos') else Vec3(0, 0, 0),
                'rotation': obj.getHpr() if hasattr(obj, 'getHpr') else Vec3(0, 0, 0),
                'scale': obj.getScale() if hasattr(obj, 'getScale') else Vec3(1, 1, 1)
            }
            
            print(f"+ Added keyframe at frame {self.current_frame}")
        else:
            print("⚠ No object selected")
    
    def on_scrub(self):
        """Handle timeline scrubbing."""
        self.current_frame = int(self.scrubber['value'])
        self.update_frame_display()
        
        # Apply keyframe if exists
        if self.current_frame in self.keyframes:
            self.apply_keyframe(self.current_frame)
    
    def update_frame_display(self):
        """Update frame counter display."""
        self.frame_label.setText(f"Frame: {self.current_frame}/{self.total_frames}")
    
    def update_fps(self, text):
        """Update animation FPS."""
        try:
            self.fps = int(text)
            print(f"✓ FPS set to {self.fps}")
        except ValueError:
            print("⚠ Invalid FPS value")
    
    def apply_keyframe(self, frame):
        """Apply keyframe values to selected object."""
        if frame not in self.keyframes:
            return
        
        if not hasattr(self.parent, 'selected_object') or not self.parent.selected_object:
            return
        
        obj = self.parent.selected_object['object']
        keyframe_data = self.keyframes[frame]
        
        if 'position' in keyframe_data:
            obj.setPos(keyframe_data['position'])
        
        if 'rotation' in keyframe_data:
            obj.setHpr(keyframe_data['rotation'])
        
        if 'scale' in keyframe_data:
            obj.setScale(keyframe_data['scale'])
    
    def update(self, dt):
        """Update animation playback."""
        if self.playing:
            # Advance frame
            self.current_frame += dt * self.fps
            
            if self.current_frame >= self.total_frames:
                # Loop animation
                self.current_frame = 0
            
            self.scrubber['value'] = int(self.current_frame)
            self.update_frame_display()
            
            # Interpolate between keyframes
            self.interpolate_keyframes()
    
    def interpolate_keyframes(self):
        """Interpolate between keyframes."""
        # Find surrounding keyframes
        prev_frame = None
        next_frame = None
        
        for frame in sorted(self.keyframes.keys()):
            if frame <= self.current_frame:
                prev_frame = frame
            elif frame > self.current_frame and next_frame is None:
                next_frame = frame
                break
        
        # Interpolate if between two keyframes
        if prev_frame is not None and next_frame is not None:
            t = (self.current_frame - prev_frame) / (next_frame - prev_frame)
            
            prev_data = self.keyframes[prev_frame]
            next_data = self.keyframes[next_frame]
            
            if hasattr(self.parent, 'selected_object') and self.parent.selected_object:
                obj = self.parent.selected_object['object']
                
                # Lerp position
                if 'position' in prev_data and 'position' in next_data:
                    pos = prev_data['position'] * (1 - t) + next_data['position'] * t
                    obj.setPos(pos)
                
                # Lerp rotation
                if 'rotation' in prev_data and 'rotation' in next_data:
                    rot = prev_data['rotation'] * (1 - t) + next_data['rotation'] * t
                    obj.setHpr(rot)
                
                # Lerp scale
                if 'scale' in prev_data and 'scale' in next_data:
                    scale = prev_data['scale'] * (1 - t) + next_data['scale'] * t
                    obj.setScale(scale)
    
    def show_curve_editor(self):
        """Open curve editor for advanced keyframe editing."""
        print("📊 Curve editor not implemented yet")
        # TODO: Implement bezier curve editor for smooth interpolation
    
    def export_animation(self):
        """Export animation data."""
        print(f"💾 Exporting animation ({len(self.keyframes)} keyframes)")
        # TODO: Save to file format (JSON, YAML, or binary)
    
    def import_animation(self):
        """Import animation data."""
        print("📂 Import animation not implemented yet")
        # TODO: Load from file format
