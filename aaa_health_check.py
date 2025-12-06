#!/usr/bin/env python3
"""
AAA system health check.

Runs lightweight, headless-safe diagnostics across core engine modules and
reports readiness. Avoids opening a graphics pipe; suitable for CI.
"""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from typing import Dict, Any, Tuple


def _status(ok: bool, detail: str = "") -> Dict[str, Any]:
    return {"ok": ok, "detail": detail}


def check_story() -> Dict[str, Any]:
    try:
        from engine_modules.story_generator import generate_story_from_llm
        story = generate_story_from_llm("Health check story", {"genre": "fantasy", "tone": "neutral", "branches": 1})
        return {"ok": True, "beats": len(story.beats), "characters": len(story.characters)}
    except Exception as exc:
        return _status(False, f"story_generator failed: {exc}")


def check_save() -> Dict[str, Any]:
    try:
        from engine_modules.save_system import create_save_system
        save = create_save_system("tmp_saves")
        slot = save.create_save(1)
        save.save_game(slot)
        loaded = save.load_game(1)
        return {"ok": loaded is not None, "slot": loaded.slot_id if loaded else None}
    except Exception as exc:
        return _status(False, f"save_system failed: {exc}")


def _fake_render_node():
    class DummyRender:
        def __init__(self):
            self.lights = []

        def attach_new_node(self, _obj):
            return self

        def attachNewNode(self, obj):
            return self.attach_new_node(obj)

        def set_light(self, light):
            self.lights.append(light)

        def setLight(self, light):
            return self.set_light(light)

        def clear_light(self, light):
            if light in self.lights:
                self.lights.remove(light)

        def set_shader_auto(self):
            return

        def clear_shader(self):
            return

        def set_background_color(self, *_args, **_kwargs):
            return

        def find(self, *_args, **_kwargs):
            return self

        def is_empty(self):
            return False

        def setHpr(self, *_args, **_kwargs):
            return

        def setShaderAuto(self):
            return

        def setShader(self, *_args, **_kwargs):
            return

    return DummyRender()


def check_rendering() -> Dict[str, Any]:
    try:
        from engine_modules.rendering import RenderingManager
        mgr = RenderingManager(_fake_render_node())
        state = mgr.get_state()
        return {"ok": True, "state": state}
    except Exception as exc:
        return _status(False, f"rendering failed: {exc}")


def check_gi() -> Dict[str, Any]:
    try:
        from engine_modules.global_illumination import create_gi_system
        gi = create_gi_system(SimpleNamespace(render=_fake_render_node()))
        return {"ok": True, "state": gi.get_state()}
    except Exception as exc:
        return _status(False, f"global_illumination failed: {exc}")


def check_audio_weather() -> Dict[str, Any]:
    results = {}
    try:
        from engine_modules.audio_system import SpatialAudioSystem
        audio = SpatialAudioSystem(base=None, enable_hrtf=False)
        results["audio"] = audio.get_state()
    except Exception as exc:
        results["audio"] = _status(False, f"audio init failed: {exc}")

    try:
        from engine_modules.weather_system import WeatherSystem, WeatherType
        weather = WeatherSystem(base=None)
        weather.set_weather(WeatherType.CLOUDY, 0.5, transition_time=0.0)
        results["weather"] = weather.get_state()
    except Exception as exc:
        results["weather"] = _status(False, f"weather init failed: {exc}")
    return {"ok": all(v.get("ok", True) for v in results.values()), "details": results}


def check_streaming() -> Dict[str, Any]:
    try:
        from engine_modules.streaming_system import StreamingSystem
        mgr = StreamingSystem(base=SimpleNamespace(render=_fake_render_node(), loader=None))
        mgr.set_enabled(False)  # Avoid work in headless
        return {"ok": True, "state": mgr.streaming_manager.get_status()}
    except Exception as exc:
        return _status(False, f"streaming failed: {exc}")


def check_physics_ai() -> Dict[str, Any]:
    results = {}
    try:
        from engine_modules.physics import PhysicsManager
        phys = PhysicsManager()
        results["physics"] = phys.get_state()
    except Exception as exc:
        results["physics"] = _status(False, f"physics failed: {exc}")

    try:
        from engine_modules.ai_system import AISystem
        ai = AISystem(base=None)
        results["ai"] = ai.get_state()
    except Exception as exc:
        results["ai"] = _status(False, f"ai failed: {exc}")
    return {"ok": all(v.get("ok", True) for v in results.values()), "details": results}


def main() -> int:
    checks: Dict[str, Tuple[Dict[str, Any], bool]] = {}
    checks["story"] = (check_story(), False)
    checks["save"] = (check_save(), False)
    checks["rendering"] = (check_rendering(), True)
    checks["global_illumination"] = (check_gi(), True)
    checks["audio_weather"] = (check_audio_weather(), True)
    checks["streaming"] = (check_streaming(), True)
    checks["physics_ai"] = (check_physics_ai(), True)

    report = {}
    overall_ok = True
    for name, (result, _) in checks.items():
        ok = result.get("ok", False) if isinstance(result, dict) else False
        overall_ok = overall_ok and ok
        report[name] = result

    print(json.dumps({"ok": overall_ok, "checks": report}, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
