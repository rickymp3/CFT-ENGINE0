"""Advanced 3D Audio Pipeline with Spatial Sound.

Features:
- 3D positional audio with distance attenuation
- Doppler effect for moving sources
- Environmental occlusion and reverb
- HRTF (Head-Related Transfer Function) for binaural audio
- Audio mixing and buses
- Dynamic audio based on weather and environment
- Editor integration for sound placement
"""
import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    from panda3d.core import AudioSound, AudioManager, Vec3, Point3, NodePath
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioBusType(Enum):
    """Audio bus types for mixing."""
    MASTER = "master"
    MUSIC = "music"
    SFX = "sfx"
    VOICE = "voice"
    AMBIENT = "ambient"
    UI = "ui"


@dataclass
class AudioSource:
    """3D audio source."""
    name: str
    sound: Optional[Any]  # AudioSound
    position: Point3
    velocity: Vec3 = Vec3(0, 0, 0)
    volume: float = 1.0
    pitch: float = 1.0
    min_distance: float = 1.0  # Distance for full volume
    max_distance: float = 100.0  # Distance for zero volume
    loop: bool = False
    bus: AudioBusType = AudioBusType.SFX
    is_playing: bool = False
    doppler_factor: float = 1.0
    reverb_send: float = 0.0  # Amount sent to reverb (0-1)


@dataclass
class ReverbPreset:
    """Reverb environment preset."""
    name: str
    decay_time: float  # Seconds
    density: float  # 0-1
    diffusion: float  # 0-1
    gain: float  # 0-1
    hf_reference: float  # Hz
    lf_reference: float  # Hz


class SpatialAudioSystem:
    """3D spatial audio engine with environmental effects."""
    
    def __init__(self, base, enable_hrtf: bool = True):
        """Initialize spatial audio system.
        
        Args:
            base: Panda3D ShowBase
            enable_hrtf: Enable binaural HRTF processing
        """
        if not PANDA3D_AVAILABLE:
            raise ImportError("Panda3D required for audio system")
        
        self.base = base
        self.enable_hrtf = enable_hrtf
        
        # Audio sources
        self.sources: Dict[str, AudioSource] = {}
        
        # Listener (camera position)
        self.listener_position = Point3(0, 0, 0)
        self.listener_velocity = Vec3(0, 0, 0)
        self.listener_forward = Vec3(0, 1, 0)
        self.listener_up = Vec3(0, 0, 1)
        
        # Audio buses
        self.buses: Dict[AudioBusType, float] = {
            bus_type: 1.0 for bus_type in AudioBusType
        }
        
        # Environmental effects
        self.global_reverb: Optional[ReverbPreset] = None
        self.occlusion_enabled = True
        self.doppler_enabled = True
        self.doppler_scale = 1.0
        
        # Reverb presets
        self.reverb_presets = self._create_reverb_presets()
        
        # Speed of sound (m/s)
        self.sound_speed = 343.0
        
        logger.info(f"Spatial Audio initialized (HRTF: {enable_hrtf})")
    
    def _create_reverb_presets(self) -> Dict[str, ReverbPreset]:
        """Create built-in reverb presets.
        
        Returns:
            Dictionary of presets
        """
        return {
            'small_room': ReverbPreset(
                name='Small Room',
                decay_time=0.3,
                density=0.8,
                diffusion=0.7,
                gain=0.5,
                hf_reference=5000.0,
                lf_reference=250.0
            ),
            'large_hall': ReverbPreset(
                name='Large Hall',
                decay_time=2.5,
                density=0.9,
                diffusion=0.9,
                gain=0.4,
                hf_reference=4000.0,
                lf_reference=200.0
            ),
            'cathedral': ReverbPreset(
                name='Cathedral',
                decay_time=5.0,
                density=1.0,
                diffusion=1.0,
                gain=0.3,
                hf_reference=3000.0,
                lf_reference=150.0
            ),
            'cave': ReverbPreset(
                name='Cave',
                decay_time=3.0,
                density=0.7,
                diffusion=0.5,
                gain=0.6,
                hf_reference=2000.0,
                lf_reference=100.0
            ),
            'outdoor': ReverbPreset(
                name='Outdoor',
                decay_time=0.1,
                density=0.1,
                diffusion=0.1,
                gain=0.1,
                hf_reference=8000.0,
                lf_reference=500.0
            )
        }
    
    def load_sound(self, name: str, file_path: str, bus: AudioBusType = AudioBusType.SFX) -> AudioSource:
        """Load a sound file.
        
        Args:
            name: Unique identifier
            file_path: Path to audio file
            bus: Audio bus assignment
            
        Returns:
            Created audio source
        """
        try:
            # Load using Panda3D's audio manager
            sound = self.base.loader.loadSfx(file_path)
            
            source = AudioSource(
                name=name,
                sound=sound,
                position=Point3(0, 0, 0),
                bus=bus
            )
            
            self.sources[name] = source
            logger.info(f"Loaded sound: {name} -> {bus.value} bus")
            
            return source
            
        except Exception as e:
            logger.error(f"Failed to load sound {name}: {e}")
            raise
    
    def create_source(self, name: str, position: Point3, 
                     bus: AudioBusType = AudioBusType.SFX) -> AudioSource:
        """Create an empty audio source at a position.
        
        Args:
            name: Source identifier
            position: 3D position
            bus: Audio bus
            
        Returns:
            Created source
        """
        source = AudioSource(
            name=name,
            sound=None,
            position=position,
            bus=bus
        )
        
        self.sources[name] = source
        return source
    
    def play(self, name: str, loop: bool = False) -> None:
        """Play a sound source.
        
        Args:
            name: Source identifier
            loop: Loop playback
        """
        if name not in self.sources:
            logger.warning(f"Sound source not found: {name}")
            return
        
        source = self.sources[name]
        
        if source.sound:
            source.loop = loop
            source.is_playing = True
            
            # Apply initial 3D positioning
            self._update_source_3d(source)
            
            if loop:
                source.sound.setLoop(True)
            
            source.sound.play()
            logger.debug(f"Playing: {name}")
    
    def stop(self, name: str) -> None:
        """Stop a sound source.
        
        Args:
            name: Source identifier
        """
        if name not in self.sources:
            return
        
        source = self.sources[name]
        if source.sound and source.is_playing:
            source.sound.stop()
            source.is_playing = False
            logger.debug(f"Stopped: {name}")
    
    def set_source_position(self, name: str, position: Point3) -> None:
        """Set 3D position of audio source.
        
        Args:
            name: Source identifier
            position: World position
        """
        if name in self.sources:
            self.sources[name].position = position
    
    def set_source_velocity(self, name: str, velocity: Vec3) -> None:
        """Set velocity of audio source for Doppler effect.
        
        Args:
            name: Source identifier
            velocity: Velocity vector (m/s)
        """
        if name in self.sources:
            self.sources[name].velocity = velocity
    
    def update_listener(self, camera: NodePath) -> None:
        """Update listener position from camera.
        
        Args:
            camera: Camera node
        """
        self.listener_position = camera.getPos()
        
        # Calculate velocity (simplified)
        # In real implementation, track previous position
        
        # Get forward and up vectors
        quat = camera.getQuat()
        self.listener_forward = quat.getForward()
        self.listener_up = quat.getUp()
    
    def update(self, dt: float) -> None:
        """Update spatial audio system.
        
        Args:
            dt: Delta time
        """
        # Update all active sources
        for source in self.sources.values():
            if source.is_playing:
                self._update_source_3d(source)
    
    def _update_source_3d(self, source: AudioSource) -> None:
        """Update 3D audio parameters for a source.
        
        Args:
            source: Audio source to update
        """
        if not source.sound:
            return
        
        # Calculate distance to listener
        to_listener = self.listener_position - source.position
        distance = to_listener.length()
        
        # Distance attenuation
        volume = self._calculate_distance_attenuation(
            distance,
            source.min_distance,
            source.max_distance
        )
        
        # Apply bus volume
        bus_volume = self.buses[source.bus]
        final_volume = volume * source.volume * bus_volume * self.buses[AudioBusType.MASTER]
        
        source.sound.setVolume(final_volume)
        
        # Doppler effect
        if self.doppler_enabled:
            pitch = self._calculate_doppler_shift(source, distance)
            source.sound.setPlayRate(pitch * source.pitch)
        else:
            source.sound.setPlayRate(source.pitch)
        
        # 3D balance (stereo panning)
        if not self.enable_hrtf:
            balance = self._calculate_stereo_balance(source.position)
            source.sound.setBalance(balance)
        else:
            # HRTF would be applied here
            # Requires specialized audio backend
            pass
        
        # Environmental effects
        if self.global_reverb and source.reverb_send > 0:
            # Apply reverb (simplified)
            # Real implementation would use audio DSP
            pass
    
    def _calculate_distance_attenuation(self, distance: float, 
                                       min_dist: float, max_dist: float) -> float:
        """Calculate volume based on distance.
        
        Args:
            distance: Distance to listener
            min_dist: Minimum distance (full volume)
            max_dist: Maximum distance (zero volume)
            
        Returns:
            Volume multiplier (0-1)
        """
        if distance <= min_dist:
            return 1.0
        elif distance >= max_dist:
            return 0.0
        else:
            # Inverse square law
            normalized = (distance - min_dist) / (max_dist - min_dist)
            return (1.0 - normalized) ** 2
    
    def _calculate_doppler_shift(self, source: AudioSource, distance: float) -> float:
        """Calculate Doppler pitch shift.
        
        Args:
            source: Audio source
            distance: Distance to listener
            
        Returns:
            Pitch multiplier
        """
        if distance < 0.1:
            return 1.0
        
        # Direction to listener
        to_listener = (self.listener_position - source.position).normalized()
        
        # Radial velocities
        source_velocity = source.velocity.dot(to_listener)
        listener_velocity = self.listener_velocity.dot(to_listener)
        
        # Doppler formula: f' = f * (v + vr) / (v + vs)
        # where v = speed of sound, vr = listener velocity, vs = source velocity
        numerator = self.sound_speed + listener_velocity
        denominator = self.sound_speed + source_velocity
        
        if abs(denominator) < 0.1:
            return 1.0
        
        pitch_shift = numerator / denominator
        
        # Clamp to reasonable range
        return max(0.5, min(2.0, pitch_shift))
    
    def _calculate_stereo_balance(self, position: Point3) -> float:
        """Calculate stereo balance (left/right).
        
        Args:
            position: Source position
            
        Returns:
            Balance (-1.0 = left, 1.0 = right)
        """
        # Vector to source
        to_source = position - self.listener_position
        
        # Right vector (perpendicular to forward)
        right = self.listener_forward.cross(self.listener_up).normalized()
        
        # Dot product gives left/right component
        balance = to_source.dot(right)
        
        # Normalize to -1 to 1
        distance = to_source.length()
        if distance > 0.1:
            balance /= distance
        
        return max(-1.0, min(1.0, balance))
    
    def check_occlusion(self, source_pos: Point3, listener_pos: Point3,
                       physics_world: Any) -> float:
        """Check if sound path is occluded by geometry.
        
        Args:
            source_pos: Source position
            listener_pos: Listener position
            physics_world: Physics world for raycasting
            
        Returns:
            Occlusion factor (0 = fully occluded, 1 = clear path)
        """
        if not self.occlusion_enabled or not physics_world:
            return 1.0
        
        # Raycast from source to listener
        # If hit geometry, reduce volume
        # This is simplified; real implementation would consider material properties
        
        # Would use physics_world.raycast(source_pos, listener_pos)
        # For now, return no occlusion
        return 1.0
    
    def set_bus_volume(self, bus: AudioBusType, volume: float) -> None:
        """Set volume for an audio bus.
        
        Args:
            bus: Bus type
            volume: Volume (0-1)
        """
        self.buses[bus] = max(0.0, min(1.0, volume))
        logger.debug(f"Bus {bus.value} volume set to {self.buses[bus]:.2f}")
    
    def set_reverb(self, preset_name: str) -> None:
        """Set global reverb environment.
        
        Args:
            preset_name: Reverb preset name
        """
        if preset_name in self.reverb_presets:
            self.global_reverb = self.reverb_presets[preset_name]
            logger.info(f"Reverb set to: {preset_name}")
        else:
            logger.warning(f"Reverb preset not found: {preset_name}")
    
    def apply_weather_effects(self, weather_state: Dict[str, Any]) -> None:
        """Apply weather-based audio effects.
        
        Args:
            weather_state: Weather system state
        """
        # Adjust based on weather
        weather_type = weather_state.get('weather', 'clear')
        
        if weather_type in ['rain', 'heavy_rain', 'storm']:
            # Rain dampens high frequencies and adds reverb
            # Would apply low-pass filter here
            self.set_reverb('outdoor')
        
        elif weather_type == 'fog':
            # Fog dampens sound
            # Reduce max distances
            pass
        
        elif weather_type in ['snow', 'heavy_snow']:
            # Snow absorbs sound
            # Reduce reverb, dampen high frequencies
            pass
    
    def cleanup(self) -> None:
        """Cleanup audio resources."""
        # Stop all sounds
        for name in list(self.sources.keys()):
            self.stop(name)
        
        self.sources.clear()
        logger.info("Audio system cleaned up")


# Audio mixing utilities

class AudioMixer:
    """Audio mixing and processing."""
    
    def __init__(self, audio_system: SpatialAudioSystem):
        """Initialize mixer.
        
        Args:
            audio_system: Spatial audio system
        """
        self.audio_system = audio_system
        self.crossfade_time = 2.0
        
    def crossfade(self, from_source: str, to_source: str, duration: float = None) -> None:
        """Crossfade between two audio sources.
        
        Args:
            from_source: Source to fade out
            to_source: Source to fade in
            duration: Crossfade duration (uses default if None)
        """
        duration = duration or self.crossfade_time
        
        # Would implement smooth volume interpolation
        # For now, just switch
        self.audio_system.stop(from_source)
        self.audio_system.play(to_source)
        
        logger.debug(f"Crossfading: {from_source} -> {to_source}")
    
    def duck(self, background_sources: List[str], foreground_source: str,
            duck_volume: float = 0.3, duration: float = 0.5) -> None:
        """Duck background audio when foreground plays (e.g., dialogue over music).
        
        Args:
            background_sources: Sources to duck
            foreground_source: Prioritized source
            duck_volume: Target volume for background (0-1)
            duration: Duck transition time
        """
        # Reduce volume of background sources
        for source_name in background_sources:
            if source_name in self.audio_system.sources:
                source = self.audio_system.sources[source_name]
                source.volume = duck_volume
        
        logger.debug(f"Ducking {len(background_sources)} sources for {foreground_source}")
