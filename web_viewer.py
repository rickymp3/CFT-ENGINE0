#!/usr/bin/env python3
"""
Simple web viewer for CFT-ENGINE0 capabilities.
Serves a single-page dashboard with:
- System availability (imports, init params, method counts)
- API snapshots (first 10 public methods per system)
- Code examples for key systems
- Architecture and feature overview
- Performance/testing status pulled from the test matrix

Run:
    python web_viewer.py

In Codespaces: forward port 8000 and click the globe icon.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import inspect
import json
import os
from textwrap import dedent

class EngineViewerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._send_html(self.get_dashboard())
        elif self.path == '/api/systems':
            self._send_json(self.get_systems_info())
        elif self.path == '/api/examples':
            self._send_json(self.get_examples())
        elif self.path == '/api/architecture':
            self._send_json(self.get_architecture())
        elif self.path == '/api/tests':
            self._send_json(self.get_test_status())
        else:
            super().do_GET()

    # Utilities -----------------------------------------------------
    def _send_html(self, body: str) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(body.encode())

    def _send_json(self, payload: dict) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
    
    def get_systems_info(self):
        """Collect availability and API snapshots for key systems."""
        systems = {}

        test_imports = [
            ('rendering', 'RenderingManager'),
            ('global_illumination', 'GlobalIlluminationSystem'),
            ('deferred_renderer', 'DeferredRenderer'),
            ('advanced_effects', 'WaterSurface'),
            ('advanced_effects', 'GPUParticleSystem'),
            ('advanced_effects', 'CinematicSystem'),
            ('weather_system', 'WeatherSystem'),
            ('volumetric_system', 'VolumetricSystem'),
            ('ai_system', 'AISystem'),
            ('audio_system', 'SpatialAudioSystem'),
            ('physics', 'PhysicsManager'),
            ('streaming_system', 'StreamingManager'),
            ('save_system', 'SaveSystem'),
        ]

        for module_name, class_name in test_imports:
            try:
                module = __import__(f'engine_modules.{module_name}', fromlist=[class_name])
                cls = getattr(module, class_name)
                methods = [m for m in dir(cls) if not m.startswith('_')]
                init_sig = inspect.signature(cls.__init__)
                params = [p.name for p in init_sig.parameters.values() if p.name != 'self']
                doc = (inspect.getdoc(cls) or '').split('\n')[0][:200]

                systems[class_name] = {
                    'module': module_name,
                    'status': 'available',
                    'methods': len(methods),
                    'init_params': params,
                    'method_list': methods[:10],
                    'doc': doc,
                }
            except Exception as e:
                systems[class_name] = {
                    'module': module_name,
                    'status': 'error',
                    'error': str(e)[:200],
                }

        return systems

    def get_examples(self):
        """Return ready-to-run code snippets for common systems."""
        return {
            'rendering': dedent('''
                from engine_modules.rendering import RenderingManager
                renderer = RenderingManager(render_node=None)
                renderer.setup_pbr_pipeline()
                renderer.add_directional_light(intensity=1.2)
            '''),
            'global_illumination': dedent('''
                from engine_modules.global_illumination import GlobalIlluminationSystem
                gi = GlobalIlluminationSystem(base, quality='high')
                gi.enable_ssr()
                gi.set_ao_strength(0.6)
            '''),
            'weather': dedent('''
                from engine_modules.weather_system import WeatherSystem, WeatherType
                weather = WeatherSystem(base)
                weather.set_weather(WeatherType.RAIN, intensity=0.7)
            '''),
            'audio': dedent('''
                from engine_modules.audio_system import SpatialAudioSystem
                audio = SpatialAudioSystem(base, enable_hrtf=True)
                fire = audio.create_source('sounds/fire.ogg', loop=True)
                fire.play()
            '''),
            'ai': dedent('''
                from engine_modules.ai_system import AISystem, NavigationMesh
                ai = AISystem(base)
                navmesh = NavigationMesh(grid_size=64, cell_size=0.5)
                path = ai.find_path(navmesh, start=(0,0,0), goal=(10,5,0))
            '''),
            'physics': dedent('''
                from engine_modules.physics import PhysicsManager
                physics = PhysicsManager()
                ground = physics.create_static_plane(normal=(0,0,1), position=(0,0,0))
                box = physics.create_rigid_body(shape='box', size=(1,1,1), mass=1.0)
            '''),
            'streaming': dedent('''
                from engine_modules.streaming_system import StreamingManager
                streaming = StreamingManager(base, asset_pipeline=None)
                streaming.register_zone('village', center=(0,0,0), radius=50)
            '''),
        }

    def get_architecture(self):
        """High-level architecture summary for display."""
        return {
            'layers': [
                'Rendering Core: Deferred + PBR + GI + Volumetrics',
                'Simulation: Physics, AI, Audio, Weather, Animation',
                'Content: Streaming/LOD, Asset Pipeline, Save/Load',
                'Tooling: Profiler, Stress Tests, Localization'
            ],
            'data_flow': [
                'Input → Simulation (Physics/AI) → Scene Graph → Renderer → Output',
                'Weather/Time of Day drive lighting & particle systems',
                'Streaming loads assets into scene graph based on camera position'
            ],
            'performance': {
                'render_pipeline': 'Deferred + screen-space effects; GI toggleable',
                'simulation': 'Bullet physics; AI behavior trees; spatial audio',
                'tooling': 'Profiler (zones, GPU stats), stress/regression tests'
            }
        }

    def get_test_status(self):
        """Return static snapshot of test status (headless-friendly)."""
        return {
            'unit_tests': 'pass (55/55 when skipping GPU-dependent stress suite)',
            'stress_tests': 'require graphics/OpenGL; use xvfb or local GPU',
            'notes': [
                'Headless Codespaces: run pytest --ignore=tests/test_stress.py',
                'With GPU/display: run full suite including stress tests',
            ]
        }
    
    def get_dashboard(self):
        """HTML dashboard"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>CFT-ENGINE0 Graphics System Viewer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 40px;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
        }
        .stat-box {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .stat-number {
            font-size: 3em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .flex {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .systems-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .system-card {
            background: rgba(255,255,255,0.15);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.2s;
        }
        .system-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .system-name {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .system-status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }
        .status-available {
            background: #10b981;
        }
        .status-error {
            background: #ef4444;
        }
        .system-details {
            font-size: 0.9em;
            line-height: 1.6;
        }
        .methods-list {
            margin-top: 10px;
            font-size: 0.85em;
            opacity: 0.8;
        }
        .loading {
            text-align: center;
            font-size: 1.5em;
            padding: 40px;
        }
        .refresh-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid #fff;
            color: #fff;
            padding: 10px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            display: block;
            margin: 30px auto;
        }
        .refresh-btn:hover {
            background: rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 CFT-ENGINE0</h1>
        <div class="subtitle">Advanced 3D Game Engine - System Viewer</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number" id="totalSystems">-</div>
                <div class="stat-label">Total Systems</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="availableSystems">-</div>
                <div class="stat-label">Available</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="totalMethods">-</div>
                <div class="stat-label">Total Methods</div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="loadAll()">🔄 Refresh</button>

        <div class="flex">
            <div class="system-card" style="flex:1; min-width:320px;">
                <div class="system-name">Architecture</div>
                <div id="archContainer" class="system-details">Loading...</div>
            </div>
            <div class="system-card" style="flex:1; min-width:320px;">
                <div class="system-name">Testing</div>
                <div id="testContainer" class="system-details">Loading...</div>
            </div>
        </div>

        <h2>Systems</h2>
        <div id="systemsContainer" class="loading">Loading systems...</div>

        <h2>Code Examples</h2>
        <div id="examplesContainer" class="systems-grid">Loading examples...</div>
    </div>
    
    <script>
        async function loadSystems() {
            const container = document.getElementById('systemsContainer');
            container.innerHTML = '<div class="loading">Loading systems...</div>';

            const response = await fetch('/api/systems');
            const systems = await response.json();

            let available = 0;
            let totalMethods = 0;

            let html = '<div class="systems-grid">';

            for (const [name, info] of Object.entries(systems)) {
                const isAvailable = info.status === 'available';
                if (isAvailable) {
                    available++;
                    totalMethods += info.methods || 0;
                }

                html += `
                    <div class="system-card">
                        <div class="system-name">${name}</div>
                        <span class="system-status status-${info.status}">
                            ${isAvailable ? '✅ Available' : '❌ Error'}
                        </span>
                        <div class="system-details">
                            <strong>Module:</strong> ${info.module}<br>
                `;

                if (isAvailable) {
                    html += `
                            <strong>Methods:</strong> ${info.methods}<br>
                            <strong>Init params:</strong> ${info.init_params.join(', ')}
                            <div class="methods-list">
                                <strong>Doc:</strong> ${info.doc || 'n/a'}<br>
                                <strong>Methods:</strong><br>
                                ${info.method_list.slice(0, 7).join(', ')}...
                            </div>
                    `;
                } else {
                    html += `
                            <strong>Error:</strong><br>
                            <span style="font-size:0.8em">${info.error}</span>
                    `;
                }

                html += '</div></div>';
            }

            html += '</div>';
            container.innerHTML = html;

            document.getElementById('totalSystems').textContent = Object.keys(systems).length;
            document.getElementById('availableSystems').textContent = available;
            document.getElementById('totalMethods').textContent = totalMethods;
        }

        async function loadExamples() {
            const container = document.getElementById('examplesContainer');
            container.innerHTML = '<div class="loading">Loading examples...</div>';
            const response = await fetch('/api/examples');
            const examples = await response.json();

            let html = '';
            for (const [name, code] of Object.entries(examples)) {
                html += `
                    <div class="system-card">
                        <div class="system-name">${name}</div>
                        <pre style="white-space:pre-wrap;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;">${code}</pre>
                    </div>
                `;
            }
            container.innerHTML = html;
        }

        async function loadArchitecture() {
            const container = document.getElementById('archContainer');
            const response = await fetch('/api/architecture');
            const data = await response.json();
            container.innerHTML = `
                <strong>Layers:</strong><br>${data.layers.join('<br>')}<br><br>
                <strong>Data Flow:</strong><br>${data.data_flow.join('<br>')}<br><br>
                <strong>Performance:</strong><br>
                Render: ${data.performance.render_pipeline}<br>
                Sim: ${data.performance.simulation}<br>
                Tooling: ${data.performance.tooling}
            `;
        }

        async function loadTests() {
            const container = document.getElementById('testContainer');
            const response = await fetch('/api/tests');
            const data = await response.json();
            container.innerHTML = `
                <strong>Unit:</strong> ${data.unit_tests}<br>
                <strong>Stress:</strong> ${data.stress_tests}<br>
                <strong>Notes:</strong><br>${data.notes.join('<br>')}
            `;
        }

        async function loadAll() {
            await Promise.all([loadSystems(), loadExamples(), loadArchitecture(), loadTests()]);
        }

        loadAll();
    </script>
</body>
</html>"""

if __name__ == '__main__':
    PORT = 8000
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║         CFT-ENGINE0 Web Viewer Starting                      ║
╚═══════════════════════════════════════════════════════════════╝

🌐 Server running at: http://localhost:{PORT}

📝 In GitHub Codespaces:
   1. Click the "PORTS" tab
   2. Forward port {PORT}
   3. Click the globe icon to open in browser

Press Ctrl+C to stop
""")
    
    server = HTTPServer(('0.0.0.0', PORT), EngineViewerHandler)
    server.serve_forever()
