"""Dynamic Weather and Environmental Simulation System.

Features:
- Day-night cycle with sun/moon positioning
- Weather effects (rain, snow, fog, storms)
- Dynamic sky colors and atmospheric scattering
- Weather impact on physics (slippery surfaces, wind)
- Weather impact on lighting and visibility
- Seasonal variations
- Editor-accessible parameters
"""
import logging
import math
import random
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

try:
    from panda3d.core import (
        NodePath, Vec3, Vec4, Point3, LVector3, DirectionalLight,
        AmbientLight, Fog, ParticleEffect, PointParticleFactory,
        LinearVectorForce, Shader
    )
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False

logger = logging.getLogger(__name__)


class WeatherType(Enum):
    """Weather conditions."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    HEAVY_SNOW = "heavy_snow"
    STORM = "storm"
    FOG = "fog"


class TimeOfDay(Enum):
    """Time periods."""
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    NIGHT = "night"
    MIDNIGHT = "midnight"


@dataclass
class WeatherParameters:
    """Weather effect parameters."""
    weather_type: WeatherType
    intensity: float = 1.0  # 0.0 to 1.0
    wind_direction: Vec3 = Vec3(1, 0, 0)
    wind_speed: float = 5.0
    visibility: float = 1.0  # 0.0 (zero visibility) to 1.0 (clear)
    wetness: float = 0.0  # Surface wetness (0-1)
    temperature: float = 20.0  # Celsius
    

class DayNightCycle:
    """Manages day-night cycle and celestial body positions."""
    
    def __init__(self, base, start_time: float = 12.0, day_length: float = 300.0):
        """Initialize day-night cycle.
        
        Args:
            base: Panda3D ShowBase
            start_time: Starting time (0-24 hours)
            day_length: Length of full day in real seconds
        """
        self.base = base
        self.current_time = start_time  # 0-24 hours
        self.day_length = day_length
        self.time_speed = 1.0  # Multiplier for time passage
        
        # Celestial bodies
        self.sun: Optional[DirectionalLight] = None
        self.sun_node: Optional[NodePath] = None
        self.moon: Optional[DirectionalLight] = None
        self.moon_node: Optional[NodePath] = None
        
        # Ambient lighting
        self.ambient_light: Optional[AmbientLight] = None
        self.ambient_node: Optional[NodePath] = None
        
        # Sky colors
        self.sky_color = Vec4(0.5, 0.7, 1.0, 1.0)
        self.horizon_color = Vec4(0.8, 0.9, 1.0, 1.0)
        
        # Setup lights
        self._setup_celestial_lights()
        
        logger.info(f"Day-night cycle initialized (start: {start_time}h, length: {day_length}s)")
    
    def _setup_celestial_lights(self) -> None:
        """Setup sun and moon lights."""
        # Sun
        self.sun = DirectionalLight("sun")
        self.sun.setColor(Vec4(1.0, 0.95, 0.8, 1.0))
        self.sun_node = self.base.render.attachNewNode(self.sun)
        self.base.render.setLight(self.sun_node)
        
        # Moon
        self.moon = DirectionalLight("moon")
        self.moon.setColor(Vec4(0.2, 0.2, 0.3, 1.0))
        self.moon_node = self.base.render.attachNewNode(self.moon)
        self.base.render.setLight(self.moon_node)
        
        # Ambient
        self.ambient_light = AmbientLight("ambient")
        self.ambient_light.setColor(Vec4(0.2, 0.2, 0.25, 1.0))
        self.ambient_node = self.base.render.attachNewNode(self.ambient_light)
        self.base.render.setLight(self.ambient_node)
    
    def update(self, dt: float) -> None:
        """Update day-night cycle.
        
        Args:
            dt: Delta time in seconds
        """
        # Advance time
        hours_per_second = 24.0 / self.day_length
        self.current_time += dt * hours_per_second * self.time_speed
        
        # Wrap around 24 hours
        if self.current_time >= 24.0:
            self.current_time -= 24.0
        
        # Update celestial positions
        self._update_sun_position()
        self._update_moon_position()
        self._update_ambient_light()
        self._update_sky_color()
    
    def _update_sun_position(self) -> None:
        """Update sun position based on time."""
        # Sun angle: 0° at noon, -90° at sunrise, 90° at sunset
        hour_angle = (self.current_time - 12.0) * 15.0  # 15° per hour
        sun_angle = math.radians(hour_angle)
        
        # Calculate sun direction
        sun_dir = Vec3(
            0,
            -math.cos(sun_angle),
            -math.sin(sun_angle)
        )
        
        self.sun_node.lookAt(sun_dir * 1000)
        
        # Fade sun based on angle (below horizon = dark)
        sun_altitude = math.degrees(math.asin(-sun_dir.z))
        
        if sun_altitude > 0:
            # Day time - sun is visible
            intensity = min(1.0, sun_altitude / 15.0)  # Full brightness at 15° above horizon
            
            # Color shift (warmer at sunrise/sunset)
            color_temp = 1.0 - abs(sun_altitude - 45) / 45.0
            r = 1.0
            g = 0.95 - color_temp * 0.2
            b = 0.8 - color_temp * 0.4
            
            self.sun.setColor(Vec4(r, g, b, 1.0) * intensity)
        else:
            # Night time - sun is below horizon
            self.sun.setColor(Vec4(0, 0, 0, 1))
    
    def _update_moon_position(self) -> None:
        """Update moon position (opposite of sun)."""
        hour_angle = (self.current_time - 12.0) * 15.0 + 180.0  # Opposite sun
        moon_angle = math.radians(hour_angle)
        
        moon_dir = Vec3(
            0,
            -math.cos(moon_angle),
            -math.sin(moon_angle)
        )
        
        self.moon_node.lookAt(moon_dir * 1000)
        
        # Fade moon
        moon_altitude = math.degrees(math.asin(-moon_dir.z))
        
        if moon_altitude > 0:
            intensity = min(1.0, moon_altitude / 15.0)
            self.moon.setColor(Vec4(0.2, 0.2, 0.3, 1.0) * intensity * 0.5)
        else:
            self.moon.setColor(Vec4(0, 0, 0, 1))
    
    def _update_ambient_light(self) -> None:
        """Update ambient light based on time."""
        # Darker at night, brighter during day
        hour_angle = (self.current_time - 12.0) * 15.0
        sun_angle = math.radians(hour_angle)
        sun_altitude = math.degrees(math.asin(-math.sin(sun_angle)))
        
        if sun_altitude > -10:
            # Day to dusk
            intensity = max(0.15, min(1.0, (sun_altitude + 10) / 25.0))
            self.ambient_light.setColor(Vec4(0.3, 0.3, 0.35, 1.0) * intensity)
        else:
            # Night
            self.ambient_light.setColor(Vec4(0.05, 0.05, 0.08, 1.0))
    
    def _update_sky_color(self) -> None:
        """Update sky color based on time."""
        hour_angle = (self.current_time - 12.0) * 15.0
        sun_angle = math.radians(hour_angle)
        sun_altitude = math.degrees(math.asin(-math.sin(sun_angle)))
        
        if sun_altitude > 15:
            # Day
            self.sky_color = Vec4(0.5, 0.7, 1.0, 1.0)
            self.horizon_color = Vec4(0.8, 0.9, 1.0, 1.0)
        elif sun_altitude > -5:
            # Sunrise/sunset
            t = (sun_altitude + 5) / 20.0
            self.sky_color = Vec4(
                0.1 + t * 0.4,
                0.2 + t * 0.5,
                0.3 + t * 0.7,
                1.0
            )
            self.horizon_color = Vec4(1.0, 0.5 + t * 0.4, 0.3 + t * 0.7, 1.0)
        else:
            # Night
            self.sky_color = Vec4(0.05, 0.05, 0.1, 1.0)
            self.horizon_color = Vec4(0.1, 0.1, 0.15, 1.0)
    
    def get_time_of_day(self) -> TimeOfDay:
        """Get current time of day period.
        
        Returns:
            Time of day enum
        """
        if 5 <= self.current_time < 7:
            return TimeOfDay.DAWN
        elif 7 <= self.current_time < 11:
            return TimeOfDay.MORNING
        elif 11 <= self.current_time < 13:
            return TimeOfDay.NOON
        elif 13 <= self.current_time < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= self.current_time < 19:
            return TimeOfDay.DUSK
        elif 19 <= self.current_time < 23:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.MIDNIGHT
    
    def set_time(self, hour: float) -> None:
        """Set current time.
        
        Args:
            hour: Time in hours (0-24)
        """
        self.current_time = hour % 24.0
        logger.debug(f"Time set to {self.current_time:.1f}h")


class WeatherSystem:
    """Manages dynamic weather effects."""
    
    def __init__(self, base, day_night_cycle: Optional[DayNightCycle] = None):
        """Initialize weather system.
        
        Args:
            base: Panda3D ShowBase
            day_night_cycle: Optional day-night cycle to sync with
        """
        self.base = base
        self.day_night = day_night_cycle
        
        # Current weather
        self.current_weather = WeatherParameters(WeatherType.CLEAR)
        self.target_weather = WeatherParameters(WeatherType.CLEAR)
        self.transition_time = 0.0
        self.transition_duration = 30.0  # Seconds for weather transition
        
        # Effects
        self.rain_particles: Optional[NodePath] = None
        self.snow_particles: Optional[NodePath] = None
        self.fog_node: Optional[Fog] = None
        
        # Physics callback for slippery surfaces
        self.physics_callback: Optional[Any] = None
        
        logger.info("Weather system initialized")
    
    def set_weather(self, weather_type: WeatherType, intensity: float = 1.0,
                    transition_duration: float = 30.0) -> None:
        """Change weather with smooth transition.
        
        Args:
            weather_type: Target weather
            intensity: Weather intensity (0-1)
            transition_duration: Transition time in seconds
        """
        self.target_weather = WeatherParameters(
            weather_type=weather_type,
            intensity=intensity
        )
        self.transition_duration = transition_duration
        self.transition_time = 0.0
        
        logger.info(f"Weather changing to {weather_type.value} (intensity: {intensity})")
    
    def update(self, dt: float) -> None:
        """Update weather system.
        
        Args:
            dt: Delta time
        """
        # Transition weather
        if self.transition_time < self.transition_duration:
            self.transition_time += dt
            t = min(1.0, self.transition_time / self.transition_duration)
            
            # Interpolate weather parameters
            self.current_weather.intensity = (
                self.current_weather.intensity * (1 - t) +
                self.target_weather.intensity * t
            )
            
            if t >= 1.0:
                self.current_weather.weather_type = self.target_weather.weather_type
        
        # Update effects based on weather
        self._update_weather_effects()
        self._update_visibility()
        self._update_physics_properties()
    
    def _update_weather_effects(self) -> None:
        """Update visual weather effects."""
        weather = self.current_weather.weather_type
        intensity = self.current_weather.intensity
        
        if weather == WeatherType.RAIN or weather == WeatherType.HEAVY_RAIN:
            self._update_rain(intensity * (2.0 if weather == WeatherType.HEAVY_RAIN else 1.0))
            self._stop_snow()
        
        elif weather == WeatherType.SNOW or weather == WeatherType.HEAVY_SNOW:
            self._update_snow(intensity * (2.0 if weather == WeatherType.HEAVY_SNOW else 1.0))
            self._stop_rain()
        
        elif weather == WeatherType.STORM:
            self._update_rain(intensity * 3.0)
            # Add lightning effects
            self._update_storm_effects()
        
        else:
            self._stop_rain()
            self._stop_snow()
    
    def _update_rain(self, intensity: float) -> None:
        """Update rain particle system.
        
        Args:
            intensity: Rain intensity
        """
        # Simplified rain - would use proper particle system
        if not self.rain_particles:
            self.rain_particles = self.base.render.attachNewNode("rain")
        
        # Set wetness for physics
        self.current_weather.wetness = min(1.0, intensity / 2.0)
    
    def _stop_rain(self) -> None:
        """Stop rain effects."""
        if self.rain_particles:
            self.rain_particles.removeNode()
            self.rain_particles = None
        
        # Wetness decreases over time
        self.current_weather.wetness *= 0.99
    
    def _update_snow(self, intensity: float) -> None:
        """Update snow particle system.
        
        Args:
            intensity: Snow intensity
        """
        if not self.snow_particles:
            self.snow_particles = self.base.render.attachNewNode("snow")
        
        # Snow makes surfaces slippery but differently than rain
        self.current_weather.wetness = min(0.8, intensity / 3.0)
    
    def _stop_snow(self) -> None:
        """Stop snow effects."""
        if self.snow_particles:
            self.snow_particles.removeNode()
            self.snow_particles = None
    
    def _update_storm_effects(self) -> None:
        """Update storm-specific effects like lightning."""
        # Random lightning flashes
        if random.random() < 0.01:  # 1% chance per frame
            self._trigger_lightning()
    
    def _trigger_lightning(self) -> None:
        """Trigger lightning flash."""
        # Briefly increase ambient light
        logger.debug("Lightning strike!")
        # Would flash screen white briefly
    
    def _update_visibility(self) -> None:
        """Update fog based on weather."""
        weather = self.current_weather.weather_type
        
        if weather == WeatherType.FOG:
            if not self.fog_node:
                self.fog_node = Fog("weather_fog")
                self.base.render.setFog(self.fog_node)
            
            self.fog_node.setColor(0.7, 0.7, 0.7)
            self.fog_node.setExpDensity(0.05 * self.current_weather.intensity)
            self.current_weather.visibility = 1.0 - self.current_weather.intensity * 0.8
        
        elif weather in [WeatherType.HEAVY_RAIN, WeatherType.STORM]:
            # Rain reduces visibility
            if not self.fog_node:
                self.fog_node = Fog("weather_fog")
                self.base.render.setFog(self.fog_node)
            
            self.fog_node.setColor(0.5, 0.5, 0.5)
            self.fog_node.setExpDensity(0.02 * self.current_weather.intensity)
            self.current_weather.visibility = 1.0 - self.current_weather.intensity * 0.5
        
        else:
            if self.fog_node:
                self.base.render.clearFog()
                self.fog_node = None
            self.current_weather.visibility = 1.0
    
    def _update_physics_properties(self) -> None:
        """Update physics properties based on weather."""
        # Call physics callback if registered
        if self.physics_callback:
            self.physics_callback({
                'wetness': self.current_weather.wetness,
                'wind_speed': self.current_weather.wind_speed,
                'wind_direction': self.current_weather.wind_direction
            })
    
    def register_physics_callback(self, callback: Any) -> None:
        """Register callback for physics updates.
        
        Args:
            callback: Function(weather_params) called when weather affects physics
        """
        self.physics_callback = callback
        logger.debug("Physics callback registered for weather system")
    
    def get_surface_friction_multiplier(self) -> float:
        """Get friction multiplier based on wetness.
        
        Returns:
            Friction multiplier (0.0 = very slippery, 1.0 = normal)
        """
        # Wet surfaces are more slippery
        return max(0.2, 1.0 - self.current_weather.wetness * 0.7)


class EnvironmentalSystem:
    """Combined day-night and weather system."""
    
    def __init__(self, base):
        """Initialize environmental system.
        
        Args:
            base: Panda3D ShowBase
        """
        self.base = base
        
        # Sub-systems
        self.day_night = DayNightCycle(base)
        self.weather = WeatherSystem(base, self.day_night)
        
        logger.info("Environmental system initialized")
    
    def update(self, dt: float) -> None:
        """Update all environmental systems.
        
        Args:
            dt: Delta time
        """
        self.day_night.update(dt)
        self.weather.update(dt)
    
    def set_time(self, hour: float) -> None:
        """Set time of day.
        
        Args:
            hour: Hour (0-24)
        """
        self.day_night.set_time(hour)
    
    def set_weather(self, weather_type: WeatherType, intensity: float = 1.0) -> None:
        """Set weather.
        
        Args:
            weather_type: Weather condition
            intensity: Intensity (0-1)
        """
        self.weather.set_weather(weather_type, intensity)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environmental state.
        
        Returns:
            State dictionary
        """
        return {
            'time': self.day_night.current_time,
            'time_of_day': self.day_night.get_time_of_day().value,
            'weather': self.weather.current_weather.weather_type.value,
            'weather_intensity': self.weather.current_weather.intensity,
            'visibility': self.weather.current_weather.visibility,
            'wetness': self.weather.current_weather.wetness,
            'sky_color': tuple(self.day_night.sky_color)
        }
