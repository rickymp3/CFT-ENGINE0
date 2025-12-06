from __future__ import annotations

"""Lightweight spatial audio wrapper.

This implementation keeps the public API stable while working in environments
without full Panda3D audio support. When Panda3D is present we use Audio3DManager
for positional sound; otherwise calls become logged no-ops so demos keep running.
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from panda3d.core import Vec3, Point3
    from direct.showbase.Audio3DManager import Audio3DManager
    PANDA3D_AVAILABLE = True
except Exception:  # pragma: no cover - Panda3D missing
    PANDA3D_AVAILABLE = False

    class Vec3:
        def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
            self.x, self.y, self.z = x, y, z

    class Point3(Vec3):
        pass

    Audio3DManager = None  # type: ignore


class AudioBusType(Enum):
    MASTER = "master"
    MUSIC = "music"
    SFX = "sfx"
    VOICE = "voice"
    AMBIENT = "ambient"
    UI = "ui"


@dataclass
class AudioSource:
    name: str
    path: Optional[Path]
    position: Point3
    loop: bool = False
    volume: float = 1.0
    bus: AudioBusType = AudioBusType.SFX
    _handle: Optional[object] = None  # AudioSound when available


class SpatialAudioSystem:
    """Small positional audio helper with optional Panda3D integration."""

    def __init__(self, base=None, enable_hrtf: bool = True):
        self.base = base
        self.enable_hrtf = enable_hrtf
        self.sources: Dict[str, AudioSource] = {}
        self.listener_pos = Point3(0, 0, 0)
        self._audio3d: Optional[Audio3DManager] = None
        self.bus_volumes: Dict[AudioBusType, float] = {bus: 1.0 for bus in AudioBusType}
        self.occlusion_factor = 0.0  # 0 = none, 1 = heavy muffling

        if PANDA3D_AVAILABLE and base is not None:
            try:
                sfx_manager = base.sfxManagerList[0] if getattr(base, "sfxManagerList", None) else None
                camera = getattr(base, "camera", None)
                if sfx_manager and camera:
                    self._audio3d = Audio3DManager(sfx_manager, camera)
                    if enable_hrtf:
                        self._audio3d.setDropOffFactor(0.03)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Audio3D unavailable, using stub audio: %s", exc)
                self._audio3d = None

        logger.info("SpatialAudioSystem initialized (panda3d=%s)", PANDA3D_AVAILABLE)

    def set_listener_position(self, pos: Tuple[float, float, float]) -> None:
        self.listener_pos = Point3(*pos)
        if self._audio3d:
            self._audio3d.setListenerPosition(self.listener_pos)

    def play(self, name: str, path: Optional[str] = None, loop: bool = False, position: Tuple[float, float, float] = (0, 0, 0)) -> None:
        """Play (or simulate) a positional sound."""
        src = self.sources.get(name)
        if src is None:
            src = AudioSource(name=name, path=Path(path) if path else None, position=Point3(*position), loop=loop)
            self.sources[name] = src
        else:
            src.position = Point3(*position)
            src.loop = loop
            if path:
                src.path = Path(path)

        if self._audio3d and src.path and src.path.exists():
            sound = self._audio3d.loadSfx(str(src.path))
            if sound:
                sound.setLoop(loop)
                sound.setVolume(src.volume * self.bus_volumes.get(src.bus, 1.0))
                self._audio3d.attachSoundToObject(sound, getattr(self.base, "camera", None))
                sound.play()
                src._handle = sound
                logger.debug("Playing sound '%s' via Panda3D", name)
                return

        # Fallback stub: log the action so demos keep moving
        logger.info("Audio play (stub): %s at %s loop=%s", name, position, loop)

    def stop(self, name: str) -> None:
        src = self.sources.get(name)
        if src and src._handle:
            try:
                src._handle.stop()
            except Exception:
                pass
        self.sources.pop(name, None)

    def update(self, dt: float) -> None:
        """Update 3D attenuation when Panda3D audio is present."""
        if not self._audio3d:
            return

        for src in self.sources.values():
            if not src._handle:
                continue
            distance = math.dist((self.listener_pos.x, self.listener_pos.y, self.listener_pos.z), (src.position.x, src.position.y, src.position.z))
            volume = max(0.0, 1.0 - distance / 50.0)
            try:
                occlusion = (1.0 - self.occlusion_factor)
                bus_mul = self.bus_volumes.get(src.bus, 1.0)
                src._handle.setVolume(volume * src.volume * bus_mul * occlusion)
                if loop := src.loop:
                    src._handle.setLoop(loop)
            except Exception as exc:  # pragma: no cover
                logger.debug("Audio volume update skipped for %s: %s", src.name, exc)

    # ---------- Mixing and environment ----------
    def set_bus_volume(self, bus: AudioBusType, volume: float) -> None:
        """Adjust volume for a specific bus."""
        self.bus_volumes[bus] = max(0.0, min(1.0, volume))

    def set_occlusion(self, factor: float) -> None:
        """Apply simple occlusion across all sounds (0-1)."""
        self.occlusion_factor = max(0.0, min(1.0, factor))

    def get_state(self) -> Dict[str, float]:
        """Expose mixer/occlusion state for diagnostics."""
        return {
            "sources": len(self.sources),
            "listener": (self.listener_pos.x, self.listener_pos.y, self.listener_pos.z),
            "occlusion": self.occlusion_factor,
            "buses": {bus.value: vol for bus, vol in self.bus_volumes.items()},
        }


# Convenience alias used by docs
SpatialAudioManager = SpatialAudioSystem
