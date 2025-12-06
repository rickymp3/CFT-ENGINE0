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
from pathlib import Path
from textwrap import dedent

import yaml

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
        elif self.path == '/api/assets':
            self._send_json(self.get_assets())
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

    def get_assets(self):
        """Return manifest-driven asset list with preview paths."""
        base_dir = Path(__file__).parent
        manifest_path = base_dir / 'assets' / 'manifest.yaml'

        if not manifest_path.exists():
            return {'assets': [], 'error': 'manifest not found'}

        with open(manifest_path, 'r', encoding='utf-8') as fh:
            manifest = yaml.safe_load(fh) or {}

        assets = []
        for entry in manifest.get('assets', []):
            asset = {
                'id': entry.get('id'),
                'type': entry.get('type'),
                'tags': entry.get('tags', []),
                'path': entry.get('path'),
                'preview': None,
            }

            path = base_dir / entry.get('path', '')

            if entry.get('type') == 'material':
                try:
                    with open(path, 'r', encoding='utf-8') as mf:
                        mat = json.load(mf)
                    albedo_rel = mat.get('albedo')
                    if albedo_rel:
                        albedo_path = (path.parent / albedo_rel).resolve()
                        asset['preview'] = '/' + albedo_path.relative_to(base_dir).as_posix()
                except Exception:
                    asset['preview'] = None
            elif entry.get('type') == 'image':
                asset['preview'] = '/' + path.relative_to(base_dir).as_posix()
            elif entry.get('type') == 'sound':
                asset['preview'] = '/' + path.relative_to(base_dir).as_posix()
            elif entry.get('type') == 'font':
                asset['preview'] = None

            # Skybox: pick the +X face if provided
            if entry.get('id', '').startswith('skybox/'):
                faces = entry.get('metadata', {}).get('faces', {})
                px = faces.get('px')
                if px:
                    asset['preview'] = '/' + (base_dir / px).relative_to(base_dir).as_posix()

            assets.append(asset)

        return {'assets': assets, 'count': len(assets)}
    
    def get_dashboard(self):
        """HTML dashboard"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>CFT-ENGINE0 Control Deck</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;600&display=swap');
        :root {
            --bg: #0f172a;
            --panel: #111827;
            --panel-strong: #0b1221;
            --card: #141c2e;
            --accent: #60f0c4;
            --accent-2: #82a0ff;
            --text: #e5e7eb;
            --muted: #94a3b8;
            --border: rgba(255,255,255,0.08);
            --shadow: 0 12px 40px rgba(0,0,0,0.4);
            --radius: 14px;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Manrope', 'Space Grotesk', sans-serif;
            background: radial-gradient(circle at 20% 20%, rgba(96,240,196,0.08), transparent 28%),
                        radial-gradient(circle at 80% 0%, rgba(130,160,255,0.12), transparent 30%),
                        var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 32px;
        }
        .shell {
            max-width: 1280px;
            margin: 0 auto 48px;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px 24px;
            background: linear-gradient(135deg, rgba(96,240,196,0.12), rgba(130,160,255,0.08));
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .brand-mark {
            width: 46px;
            height: 46px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            display: grid;
            place-items: center;
            font-weight: 800;
            color: #0b1221;
            letter-spacing: -0.5px;
        }
        h1 {
            margin: 0;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 24px;
            letter-spacing: -0.4px;
        }
        .subtitle {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 14px;
        }
        .pill {
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 13px;
        }
        .cta-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .button {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #0b1221;
            border: none;
            border-radius: 10px;
            padding: 11px 18px;
            font-weight: 700;
            cursor: pointer;
            letter-spacing: 0.2px;
            box-shadow: 0 10px 30px rgba(96,240,196,0.25);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .button.secondary {
            background: transparent;
            color: var(--text);
            border: 1px solid var(--border);
            box-shadow: none;
        }
        .button:hover { transform: translateY(-1px); }
        .button:active { transform: translateY(0); }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .panel {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px;
            box-shadow: var(--shadow);
        }
        .section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 30px 0 12px;
            font-weight: 700;
            letter-spacing: -0.2px;
        }
        .stat {
            padding: 18px;
            border-radius: var(--radius);
            background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            border: 1px solid var(--border);
        }
        .stat-label { color: var(--muted); font-size: 13px; }
        .stat-value { font-size: 28px; font-weight: 800; margin-top: 6px; }
        .system-card {
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 16px;
            border-radius: var(--radius);
            background: var(--panel);
            border: 1px solid var(--border);
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .system-card:hover { transform: translateY(-2px); border-color: rgba(96,240,196,0.4); }
        .system-name { font-weight: 700; font-size: 16px; letter-spacing: -0.2px; }
        .badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; }
        .badge.good { background: rgba(96,240,196,0.14); color: #b7ffe6; }
        .badge.bad { background: rgba(239,68,68,0.14); color: #fecaca; }
        .muted { color: var(--muted); font-size: 13px; }
        .methods { font-size: 13px; line-height: 1.5; color: var(--muted); }
        pre {
            margin: 0;
            background: #0b1221;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 10px;
            color: #cbd5e1;
            font-size: 13px;
            overflow-x: auto;
        }
        .loading { text-align: center; padding: 30px; color: var(--muted); }
        .asset-preview { margin-top: 8px; border-radius: 8px; overflow: hidden; }
        .chip { display: inline-block; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.06); color: var(--muted); font-size: 12px; margin: 2px; }
        @media (max-width: 720px) { header { flex-direction: column; align-items: flex-start; } body { padding: 18px; } }
    </style>
</head>
<body>
    <div class="shell">
        <header>
            <div class="brand">
                <div class="brand-mark">CFT</div>
                <div>
                    <h1>CFT-ENGINE0 Control Deck</h1>
                    <div class="subtitle">Surface-level health, APIs, and assets at a glance.</div>
                </div>
            </div>
            <div class="cta-row">
                <span class="pill">Headless-friendly | Live refresh</span>
                <button class="button" onclick="loadAll()">Refresh View</button>
            </div>
        </header>

        <div class="grid">
            <div class="stat">
                <div class="stat-label">Systems Tracked</div>
                <div class="stat-value" id="totalSystems">–</div>
            </div>
            <div class="stat">
                <div class="stat-label">Available</div>
                <div class="stat-value" id="availableSystems">–</div>
            </div>
            <div class="stat">
                <div class="stat-label">Total Public Methods</div>
                <div class="stat-value" id="totalMethods">–</div>
            </div>
        </div>

        <div class="grid">
            <div class="panel">
                <div class="section-title">Architecture</div>
                <div id="archContainer" class="muted">Loading...</div>
            </div>
            <div class="panel">
                <div class="section-title">Test Status</div>
                <div id="testContainer" class="muted">Loading...</div>
            </div>
        </div>

        <div class="section-title">
            <span>Systems</span>
            <span class="pill">Core + AAA surfaces</span>
        </div>
        <div id="systemsContainer" class="loading">Loading systems...</div>

        <div class="section-title">
            <span>Code Examples</span>
            <span class="pill">Copy-paste ready</span>
        </div>
        <div id="examplesContainer" class="grid">Loading examples...</div>

        <div class="section-title">
            <span>Asset Manifest</span>
            <span class="pill">Previews when available</span>
        </div>
        <div id="assetsContainer" class="grid">Loading assets...</div>
    </div>
    
    <script>
        const statusBadge = (info) => {
            const isAvailable = info.status === 'available';
            const cls = isAvailable ? 'badge good' : 'badge bad';
            const label = isAvailable ? 'Ready' : 'Error';
            return `<span class="${cls}">${label}</span>`;
        };

        async function loadSystems() {
            const container = document.getElementById('systemsContainer');
            container.innerHTML = '<div class="loading">Pulling module metadata…</div>';

            const response = await fetch('/api/systems');
            const systems = await response.json();

            let available = 0;
            let totalMethods = 0;

            let html = '<div class="grid">';

            for (const [name, info] of Object.entries(systems)) {
                const isAvailable = info.status === 'available';
                if (isAvailable) {
                    available++;
                    totalMethods += info.methods || 0;
                }

                html += `
                    <div class="system-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="system-name">${name}</div>
                            ${statusBadge(info)}
                        </div>
                        <div class="muted">Module: ${info.module}</div>
                `;

                if (isAvailable) {
                    html += `
                            <div class="methods">
                                <strong>${info.methods}</strong> public methods · init(${info.init_params.join(', ') || ' '})
                                <div style="margin-top:6px;">${info.doc || 'No docstring available.'}</div>
                                <div style="margin-top:8px;">
                                    <span class="chip">${(info.method_list[0] || 'update')}</span>
                                    <span class="chip">${(info.method_list[1] || 'enable')}</span>
                                    <span class="chip">${(info.method_list[2] || 'disable')}</span>
                                </div>
                            </div>
                    `;
                } else {
                    html += `
                            <div class="methods">
                                <strong>Error:</strong> ${info.error}
                            </div>
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
            container.innerHTML = '<div class="loading">Preparing snippets…</div>';
            const response = await fetch('/api/examples');
            const examples = await response.json();

            let html = '';
            for (const [name, code] of Object.entries(examples)) {
                html += `
                    <div class="panel">
                        <div class="system-name" style="margin-bottom:8px;">${name}</div>
                        <pre>${code}</pre>
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
                <div><strong>Layers</strong><br>${data.layers.join('<br>')}</div>
                <div style="margin-top:10px;"><strong>Data Flow</strong><br>${data.data_flow.join('<br>')}</div>
                <div style="margin-top:10px;"><strong>Performance</strong><br>
                    Render: ${data.performance.render_pipeline}<br>
                    Sim: ${data.performance.simulation}<br>
                    Tooling: ${data.performance.tooling}
                </div>
            `;
        }

        async function loadTests() {
            const container = document.getElementById('testContainer');
            const response = await fetch('/api/tests');
            const data = await response.json();
            container.innerHTML = `
                <div><strong>Unit:</strong> ${data.unit_tests}</div>
                <div style="margin-top:6px;"><strong>Stress:</strong> ${data.stress_tests}</div>
                <div style="margin-top:10px;"><strong>Notes:</strong><br>${data.notes.join('<br>')}</div>
            `;
        }

        async function loadAssets() {
            const container = document.getElementById('assetsContainer');
            container.innerHTML = '<div class="loading">Loading assets...</div>';

            const response = await fetch('/api/assets');
            const data = await response.json();
            const assets = data.assets || [];

            let html = '';
            for (const asset of assets) {
                const preview = asset.preview ? `<div class="asset-preview">${asset.type === 'sound' ? `<audio controls src="${asset.preview}" style="width:100%"></audio>` : `<img src="${asset.preview}" alt="${asset.id}" style="max-width:100%;display:block;">`}</div>` : '';
                html += `
                    <div class="system-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="system-name">${asset.id}</div>
                            <span class="pill">${asset.type}</span>
                        </div>
                        <div class="muted">Path: ${asset.path}</div>
                        <div>${(asset.tags || []).map(t => `<span class="chip">${t}</span>`).join(' ')}</div>
                        ${preview}
                    </div>
                `;
            }

            container.innerHTML = html || '<div class="loading">No assets found</div>';
        }

        async function loadAll() {
            await Promise.all([loadSystems(), loadExamples(), loadArchitecture(), loadTests(), loadAssets()]);
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
