#!/usr/bin/env python3
"""
Web-viewable demo that captures screenshots from the 3D engine
Run with: xvfb-run python web_demo.py
"""

import os
import sys

# Configure for offscreen rendering
os.environ['PANDA_PRC_DIR'] = '/tmp'
with open('/tmp/Config.prc', 'w') as f:
    f.write('window-type offscreen\n')
    f.write('audio-library-name null\n')
    f.write('show-frame-rate-meter false\n')

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, Filename
from engine_modules.weather_system import WeatherSystem, WeatherType
from engine_modules.rendering import RenderingManager

class WebDemo(ShowBase):
    def __init__(self):
        # Must configure before ShowBase init
        loadPrcFileData('', 'window-type offscreen')
        loadPrcFileData('', 'audio-library-name null')
        
        ShowBase.__init__(self)
        
        print("🎮 Initializing CFT-ENGINE0 Web Demo...")
        
        # Create simple scene
        self.setup_scene()
        self.setup_weather()
        
        # Take screenshots
        self.frame = 0
        self.max_frames = 5
        
        self.taskMgr.add(self.update_and_capture, "update")
    
    def setup_scene(self):
        """Create a simple 3D scene"""
        # Add a ground plane
        from panda3d.core import CardMaker, Vec3
        cm = CardMaker("ground")
        cm.setFrame(-10, 10, -10, 10)
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, -1)
        ground.setP(-90)
        ground.setColor(0.3, 0.5, 0.3, 1)
        
        # Add some boxes
        from panda3d.core import GeomNode
        for i in range(3):
            box = self.loader.loadModel("models/box")
            if box:
                box.reparentTo(self.render)
                box.setPos(i * 3 - 3, 5, 0)
                box.setScale(0.5)
        
        # Setup camera
        self.camera.setPos(0, -15, 5)
        self.camera.lookAt(0, 0, 0)
        
        print("✅ Scene created")
    
    def setup_weather(self):
        """Add weather effects"""
        try:
            self.weather = WeatherSystem(self)
            self.weather.set_weather(WeatherType.CLEAR)
            print("✅ Weather system initialized")
        except Exception as e:
            print(f"⚠️  Weather system unavailable: {e}")
    
    def update_and_capture(self, task):
        """Update scene and capture screenshots"""
        if self.frame >= self.max_frames:
            print(f"\n✅ Captured {self.max_frames} frames")
            print("📸 Screenshots saved to:")
            for i in range(self.max_frames):
                print(f"   frame_{i:03d}.png")
            sys.exit(0)
        
        # Change weather each frame
        if hasattr(self, 'weather'):
            weather_types = [WeatherType.CLEAR, WeatherType.RAIN, WeatherType.FOG]
            self.weather.set_weather(weather_types[self.frame % len(weather_types)])
        
        # Capture screenshot
        filename = f"frame_{self.frame:03d}.png"
        self.screenshot(namePrefix='', defaultFilename=False,
                       source=None, imageComment="CFT-ENGINE0 Demo")
        
        # Rename to our format
        if os.path.exists('screenshot.png'):
            os.rename('screenshot.png', filename)
            print(f"📸 Captured {filename}")
        
        self.frame += 1
        return task.cont

if __name__ == "__main__":
    app = WebDemo()
    app.run()
