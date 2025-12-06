from __future__ import annotations

"""Thin global illumination shim.

The real-time GI pipeline described in the docs is represented here by a tiny
light manager that keeps demos and factories alive. When Panda3D is available
we set up a couple of helper lights; otherwise we simply track state and log
operations so callers never crash.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from panda3d.core import DirectionalLight, AmbientLight, Vec4
    PANDA3D_AVAILABLE = True
except Exception:  # pragma: no cover - Panda3D missing
    PANDA3D_AVAILABLE = False

    class Vec4:
        def __init__(self, r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0):
            self.r, self.g, self.b, self.a = r, g, b, a

    class DirectionalLight:  # type: ignore
        def __init__(self, name: str):
            self.name = name

        def setColor(self, *_args, **_kwargs):
            return

    class AmbientLight(DirectionalLight):
        pass


class GIQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class GlobalIlluminationSystem:
    """Small lighting helper that approximates the planned API."""

    def __init__(self, base=None, quality: GIQuality = GIQuality.MEDIUM):
        self.base = base
        self.quality = quality
        self.enabled = PANDA3D_AVAILABLE and base is not None and getattr(base, "render", None) is not None
        self.sun_light: Optional[DirectionalLight] = None
        self.ambient_light: Optional[AmbientLight] = None
        self.ssr_enabled = quality in (GIQuality.HIGH, GIQuality.ULTRA)
        self.ao_strength = 0.3
        self.indirect_scale = 1.0

        if self.enabled:
            self._init_lights()
        else:
            logger.warning("Global illumination running in stub mode (panda3d=%s)", PANDA3D_AVAILABLE)

    def _init_lights(self) -> None:
        """Create a simple key + ambient light setup."""
        try:
            self.sun_light = DirectionalLight("gi_sun")
            self.sun_light.setColor(Vec4(1.0, 0.98, 0.9, 1.0))
            sun_np = self.base.render.attachNewNode(self.sun_light)
            sun_np.setHpr(-45, -60, 0)
            self.base.render.setLight(sun_np)

            self.ambient_light = AmbientLight("gi_ambient")
            self.ambient_light.setColor(Vec4(0.2, 0.2, 0.25, 1.0))
            ambient_np = self.base.render.attachNewNode(self.ambient_light)
            self.base.render.setLight(ambient_np)

            # Small quality hint for future expansion
            if hasattr(self.base.render, "setShaderAuto"):
                self.base.render.setShaderAuto()

            logger.info("GlobalIlluminationSystem initialized (quality=%s)", self.quality.value)
        except Exception as exc:  # pragma: no cover
            self.enabled = False
            logger.warning("GI light setup failed; continuing without lights: %s", exc)

    def update(self, _dt: float = 0.0) -> None:
        """Placeholder for future GI updates."""
        # Intentionally lightweight; nothing to do yet.
        return

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def set_quality(self, quality: GIQuality | str) -> None:
        """Adjust quality preset; re-applies lights if available."""
        self.quality = quality if isinstance(quality, GIQuality) else GIQuality(quality.lower())
        self.ssr_enabled = self.quality in (GIQuality.HIGH, GIQuality.ULTRA)
        logger.info("GI quality set to %s (SSR=%s)", self.quality.value, self.ssr_enabled)

    def set_ambient_intensity(self, value: float) -> None:
        """Tune ambient light level."""
        self.indirect_scale = value
        if self.ambient_light:
            try:
                current = self.ambient_light.getColor()
                self.ambient_light.setColor(Vec4(current[0] * value, current[1] * value, current[2] * value, 1.0))
            except Exception:
                pass

    def set_sun_intensity(self, value: float) -> None:
        """Tune main sun/directional intensity."""
        if self.sun_light:
            try:
                color = self.sun_light.getColor()
                self.sun_light.setColor(color * value)
            except Exception:
                pass

    def set_sun_direction(self, hpr: tuple[float, float, float]) -> None:
        """Adjust sun orientation (hook for time-of-day systems)."""
        if self.enabled and self.sun_light:
            try:
                node = self.base.render.find("**/gi_sun")
                if not node.is_empty():
                    node.setHpr(*hpr)
            except Exception:
                pass

    def enable_ssr(self) -> None:
        """Enable screen-space reflections flag (stub)."""
        self.ssr_enabled = True

    def disable_ssr(self) -> None:
        self.ssr_enabled = False

    def get_state(self) -> dict:
        """Expose GI state for dashboards."""
        return {
            "quality": self.quality.value,
            "enabled": self.enabled,
            "ssr": self.ssr_enabled,
            "indirect_scale": self.indirect_scale,
        }


def create_gi_system(base, quality: str | GIQuality = "medium") -> GlobalIlluminationSystem:
    """Factory used by demos/tests; accepts string or GIQuality."""
    quality_enum = quality if isinstance(quality, GIQuality) else GIQuality(quality.lower())
    return GlobalIlluminationSystem(base, quality_enum)
