from __future__ import annotations

"""Lightweight weather and environment helpers.

The goal of this module is to keep the demo scripts running even when Panda3D
features are missing. Visual effects are applied when available and otherwise
silently downgraded to simple state tracking.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

try:  # Optional Panda3D support
    from panda3d.core import Fog, Vec3, Vec4
    PANDA3D_AVAILABLE = True
except Exception:  # pragma: no cover - only hits when Panda3D is missing
    PANDA3D_AVAILABLE = False

    class Vec3:
        def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
            self.x, self.y, self.z = x, y, z

        def __iter__(self):
            return iter((self.x, self.y, self.z))

        def __repr__(self) -> str:
            return f"Vec3({self.x}, {self.y}, {self.z})"

    class Vec4:
        def __init__(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0):
            self.r, self.g, self.b, self.a = r, g, b, a

    class Fog:
        MLinear = 0

        def __init__(self, name: str = "fog"):
            self.name = name
            self.color = Vec4()
            self.start = 0.0
            self.end = 100.0

        def setColor(self, color: Vec4) -> None:
            self.color = color

        def setLinearRange(self, start: float, end: float) -> None:
            self.start, self.end = start, end


class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    HEAVY_SNOW = "heavy_snow"
    STORM = "storm"
    FOG = "fog"


@dataclass
class WeatherState:
    weather_type: WeatherType
    intensity: float = 1.0


class WeatherSystem:
    """Minimal weather controller with graceful fallbacks."""

    def __init__(self, base=None, default_weather: WeatherType = WeatherType.CLEAR):
        self.base = base
        self.current = WeatherState(default_weather, 1.0)
        self.target = WeatherState(default_weather, 1.0)
        self._transition_time = 0.0
        self._transition_total = 0.0
        self.wind: Vec3 = Vec3(1, 0, 0)

        self.has_scene = bool(
            PANDA3D_AVAILABLE and base is not None and getattr(base, "render", None) is not None
        )
        self._fog: Optional[Fog] = None

        if self.has_scene and PANDA3D_AVAILABLE:
            try:
                self._fog = Fog("weather_fog")
                self._fog.setColor(Vec4(0.7, 0.8, 1.0, 1.0))
                self._fog.setLinearRange(50.0, 200.0)
                base.render.setFog(self._fog)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("WeatherSystem: fog setup unavailable: %s", exc)
                self._fog = None

        logger.info("WeatherSystem initialized (panda3d=%s)", PANDA3D_AVAILABLE)

    def set_weather(self, weather_type: WeatherType, intensity: float = 1.0, transition_time: float = 1.0) -> None:
        """Set the target weather. Transition is optional and will be skipped if set to 0."""
        self.target = WeatherState(weather_type, max(0.0, min(1.0, intensity)))
        self._transition_total = max(0.0, transition_time)
        self._transition_time = 0.0
        logger.info("Weather changing to %s (intensity %.2f)", weather_type.value, intensity)

        if self._transition_total == 0.0:
            self.current = WeatherState(self.target.weather_type, self.target.intensity)
            self._apply_to_scene()

    def update(self, dt: float) -> None:
        """Blend towards the target weather and apply effects."""
        if dt is None:
            dt = 0.0

        if self._transition_total > 0 and self._transition_time < self._transition_total:
            self._transition_time += max(dt, 0.0)
            blend = min(1.0, self._transition_time / self._transition_total)
            new_intensity = (1 - blend) * self.current.intensity + blend * self.target.intensity
            self.current = WeatherState(self.target.weather_type, new_intensity)
        else:
            self.current = WeatherState(self.target.weather_type, self.target.intensity)

        self._apply_to_scene()

    def _apply_to_scene(self) -> None:
        """Apply very small visual tweaks; no-ops if Panda3D is missing."""
        if not self.has_scene:
            return

        color_map = {
            WeatherType.CLEAR: Vec4(0.6, 0.8, 1.0, 1.0),
            WeatherType.CLOUDY: Vec4(0.6, 0.65, 0.7, 1.0),
            WeatherType.RAIN: Vec4(0.5, 0.55, 0.6, 1.0),
            WeatherType.HEAVY_RAIN: Vec4(0.4, 0.45, 0.5, 1.0),
            WeatherType.SNOW: Vec4(0.8, 0.85, 0.9, 1.0),
            WeatherType.HEAVY_SNOW: Vec4(0.85, 0.9, 0.95, 1.0),
            WeatherType.STORM: Vec4(0.35, 0.35, 0.4, 1.0),
            WeatherType.FOG: Vec4(0.7, 0.75, 0.8, 1.0),
        }

        color = color_map.get(self.current.weather_type, Vec4(0.6, 0.8, 1.0, 1.0))
        fog_density = 1.0 - min(1.0, self.current.intensity)

        try:
            if hasattr(self.base, "setBackgroundColor"):
                self.base.setBackgroundColor(color.r, color.g, color.b, color.a)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Background color update skipped: %s", exc)

        if self._fog:
            try:
                self._fog.setColor(color)
                near = 10.0 + 30.0 * fog_density
                far = 80.0 + 120.0 * fog_density
                self._fog.setLinearRange(near, far)
            except Exception as exc:  # pragma: no cover
                logger.debug("Fog update skipped: %s", exc)

    def set_wind(self, direction: tuple = (1.0, 0.0, 0.0), speed: float = 1.0) -> None:
        """Update wind vector used by dependent systems."""
        self.wind = Vec3(direction[0] * speed, direction[1] * speed, direction[2] * speed)

    def get_state(self) -> dict:
        """Expose current weather state for diagnostics."""
        return {
            "weather": self.current.weather_type.value,
            "intensity": self.current.intensity,
            "wind": (self.wind.x, self.wind.y, self.wind.z),
            "has_scene": self.has_scene,
        }


class EnvironmentalSystem(WeatherSystem):
    """Weather system with a simple time-of-day tracker."""

    def __init__(self, base=None):
        super().__init__(base)
        self.time_of_day: float = 12.0  # 0-24 hours

    def set_time_of_day(self, hour: float) -> None:
        self.time_of_day = hour % 24.0
        self._apply_to_scene()

    def update(self, dt: float) -> None:
        # Advance time slowly to keep demo moving if running continuously
        if dt is None:
            dt = 0.0
        self.time_of_day = (self.time_of_day + (dt / 60.0) * 24.0) % 24.0
        super().update(dt)


# Backwards compatibility aliases used by docs and demos
WeatherManager = WeatherSystem
EnvironmentalManager = EnvironmentalSystem
