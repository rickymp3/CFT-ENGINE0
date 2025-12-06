"""Random scene generator using AI narrative and asset generation.

Features:
- Generate complete scenes from random prompts
- Create photorealistic assets matching visual references
- Automatic scene assembly with lighting and props
- Background processing to avoid UI blocking
"""

import os
import random
import logging
import threading
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Scene generation prompts
SCENE_PROMPTS = [
    "Hero explores an abandoned factory",
    "A battle in a snowy forest",
    "Mystical temple in the jungle",
    "Cyberpunk street market at night",
    "Desert ruins under a harsh sun",
    "Medieval castle throne room",
    "Underwater research facility",
    "Volcanic cave system",
    "Futuristic space station hangar",
    "Gothic cathedral interior",
    "Post-apocalyptic city ruins",
    "Enchanted forest clearing",
    "Ancient library filled with secrets",
    "Mountain top monastery",
    "Steampunk airship interior"
]

# Max assets per scene to control generation time
MAX_SCENE_ASSETS = int(os.getenv('MAX_SCENE_ASSETS', '5'))
MAX_SCENE_BEATS = int(os.getenv('MAX_SCENE_BEATS', '4'))


class RandomSceneGenerator:
    """Generate complete random scenes with AI."""
    
    def __init__(self, asset_pipeline=None, asset_manager=None):
        """Initialize generator.
        
        Args:
            asset_pipeline: AssetPipeline instance
            asset_manager: AssetManager instance
        """
        self.asset_pipeline = asset_pipeline
        self.asset_manager = asset_manager
        self.generation_in_progress = False
        self.progress_callback: Optional[Callable] = None
        self.cancel_requested = False
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set callback for progress updates.
        
        Args:
            callback: Function taking (message, progress_0_to_1)
        """
        self.progress_callback = callback
    
    def _update_progress(self, message: str, progress: float):
        """Update progress."""
        logger.info(f"{message} ({progress*100:.0f}%)")
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def cancel(self):
        """Cancel ongoing generation."""
        self.cancel_requested = True
    
    def generate_random_scene_async(
        self,
        completion_callback: Optional[Callable] = None,
        prompt: str = None
    ):
        """Generate a random scene asynchronously.
        
        Args:
            completion_callback: Called when generation completes
            prompt: Optional custom prompt (uses random if None)
        """
        def worker():
            try:
                result = self.generate_random_scene(prompt)
                if completion_callback:
                    completion_callback(result)
            except Exception as e:
                logger.error(f"Random scene generation failed: {e}")
                if completion_callback:
                    completion_callback(None)
            finally:
                self.generation_in_progress = False
        
        self.generation_in_progress = True
        self.cancel_requested = False
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def generate_random_scene(self, prompt: str = None) -> Optional[Dict[str, Any]]:
        """Generate a complete random scene.
        
        Args:
            prompt: Optional custom prompt
            
        Returns:
            Dict with scene data or None if failed
        """
        try:
            # Step 1: Select prompt
            if not prompt:
                prompt = random.choice(SCENE_PROMPTS)
            
            self._update_progress(f"Generating scene: {prompt}", 0.0)
            logger.info(f"=== Random Scene Generation ===")
            logger.info(f"Prompt: {prompt}")
            
            # Step 2: Find or import reference images
            self._update_progress("Finding reference images...", 0.1)
            ref_images = self._get_reference_images(prompt)
            
            if self.cancel_requested:
                logger.info("Generation cancelled")
                return None
            
            # Step 3: Generate narrative
            self._update_progress("Generating narrative...", 0.2)
            story = self._generate_narrative(prompt, ref_images)
            
            if not story or self.cancel_requested:
                return None
            
            # Step 4: Generate assets for each beat
            generated_assets = []
            total_beats = len(story.beats)
            
            for i, (beat_id, beat) in enumerate(story.beats.items()):
                if self.cancel_requested:
                    break
                
                progress = 0.3 + (i / total_beats) * 0.5
                self._update_progress(
                    f"Generating assets ({i+1}/{total_beats}): {beat.title}",
                    progress
                )
                
                # Generate asset for this beat
                asset = self._generate_beat_asset(beat, ref_images)
                if asset:
                    generated_assets.append(asset)
                    story.attach_generated_asset(beat_id, asset['asset_id'])
            
            if self.cancel_requested:
                return None
            
            # Step 5: Assemble scene
            self._update_progress("Assembling scene...", 0.85)
            scene_data = self._assemble_scene(story, generated_assets)
            
            # Step 6: Setup lighting and environment
            self._update_progress("Setting up environment...", 0.95)
            self._setup_environment(scene_data, prompt)
            
            self._update_progress("Scene generation complete!", 1.0)
            
            logger.info(f"=== Generation Summary ===")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Beats: {len(story.beats)}")
            logger.info(f"Assets generated: {len(generated_assets)}")
            logger.info(f"Average realism score: {sum(a.get('realism_score', 0.0) for a in generated_assets) / max(len(generated_assets), 1):.3f}")
            
            return {
                'prompt': prompt,
                'story': story,
                'assets': generated_assets,
                'scene_data': scene_data
            }
        
        except Exception as e:
            logger.error(f"Random scene generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_reference_images(self, prompt: str) -> List[str]:
        """Find reference images matching prompt.
        
        Args:
            prompt: Scene prompt
            
        Returns:
            List of image paths/IDs
        """
        ref_images = []
        
        # Extract keywords from prompt
        keywords = prompt.lower().split()
        
        # Try to find matching images in asset library
        if self.asset_manager:
            try:
                # Search for images by tags
                for keyword in keywords:
                    images = self.asset_manager.list_by_tag(keyword)
                    ref_images.extend([img for img in images if 'image' in img or 'skybox' in img])
                
                if ref_images:
                    # Limit to a few references
                    ref_images = random.sample(ref_images, min(3, len(ref_images)))
                    logger.info(f"Found {len(ref_images)} reference images")
                else:
                    logger.warning("No reference images found in library")
            except Exception as e:
                logger.warning(f"Could not search asset library: {e}")
        
        # If no images found, use default skyboxes
        if not ref_images:
            default_skyboxes = [
                'assets/images/skybox/clear_skies_up.png',
                'assets/images/skybox/sunset_glow_up.png'
            ]
            ref_images = [s for s in default_skyboxes if os.path.exists(s)]
        
        return ref_images
    
    def _generate_narrative(self, prompt: str, ref_images: List[str]) -> Optional[Any]:
        """Generate narrative with visual references.
        
        Args:
            prompt: Scene prompt
            ref_images: Reference image paths
            
        Returns:
            StoryGraph or None
        """
        try:
            from engine_modules.story_generator import generate_story_from_llm
            
            # Include visual context in prompt
            enhanced_prompt = prompt
            if ref_images:
                enhanced_prompt += f"\n\nVisual references available: {len(ref_images)} images"
                enhanced_prompt += "\nUse these images to inspire the setting, mood, and atmosphere."
            
            # Generate with limited complexity for quick results
            constraints = {
                'genre': self._infer_genre(prompt),
                'tone': self._infer_tone(prompt),
                'branches': 1,  # Keep simple for random scenes
                'beats': min(MAX_SCENE_BEATS, 4)
            }
            
            story = generate_story_from_llm(enhanced_prompt, constraints)
            
            # Attach reference images to beats
            if story and ref_images:
                for i, beat_id in enumerate(list(story.beats.keys())[:len(ref_images)]):
                    story.attach_image(beat_id, ref_images[i])
            
            return story
        
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return None
    
    def _infer_genre(self, prompt: str) -> str:
        """Infer genre from prompt."""
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ['cyber', 'futuristic', 'space', 'sci']):
            return 'scifi'
        elif any(w in prompt_lower for w in ['medieval', 'castle', 'temple', 'enchanted']):
            return 'fantasy'
        elif any(w in prompt_lower for w in ['mystery', 'secret', 'abandoned']):
            return 'mystery'
        elif any(w in prompt_lower for w in ['apocalypse', 'ruins', 'dark']):
            return 'horror'
        else:
            return 'general'
    
    def _infer_tone(self, prompt: str) -> str:
        """Infer tone from prompt."""
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ['battle', 'fight', 'epic']):
            return 'epic'
        elif any(w in prompt_lower for w in ['dark', 'gothic', 'shadow']):
            return 'dark'
        elif any(w in prompt_lower for w in ['mystical', 'enchanted', 'magical']):
            return 'dramatic'
        else:
            return 'neutral'
    
    def _generate_beat_asset(self, beat, ref_images: List[str]) -> Optional[Dict]:
        """Generate asset for a narrative beat.
        
        Args:
            beat: StoryBeat instance
            ref_images: Available reference images
            
        Returns:
            Asset data dict or None
        """
        try:
            from engine_modules.asset_generation import AssetGenerator
            
            generator = AssetGenerator()
            
            # Use beat's reference image if available
            ref_image = beat.image_reference
            if not ref_image and ref_images:
                ref_image = random.choice(ref_images)
            
            # Generate asset
            if ref_image and os.path.exists(ref_image):
                asset = generator.generate_asset_from_reference(
                    ref_image,
                    beat.description,
                    asset_type='environment',
                    enforce_quality=True
                )
            else:
                asset = generator.generate_asset_from_text(
                    beat.description,
                    asset_type='environment',
                    enforce_quality=True
                )
            
            if asset:
                return {
                    'asset_id': asset.asset_id,
                    'model_path': asset.model_path,
                    'texture_paths': asset.texture_paths,
                    'realism_score': asset.realism_score,
                    'generation_attempts': asset.generation_attempts,
                    'beat_title': beat.title
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Asset generation failed for beat: {e}")
            return None
    
    def _assemble_scene(self, story, assets: List[Dict]) -> Dict[str, Any]:
        """Assemble scene from story and assets.
        
        Args:
            story: StoryGraph
            assets: List of asset dicts
            
        Returns:
            Scene assembly data
        """
        scene_data = {
            'story_title': story.title,
            'objects': [],
            'cameras': [],
            'lights': []
        }
        
        # Position assets in scene
        for i, asset in enumerate(assets):
            # Random position within bounds
            x = random.uniform(-10, 10)
            y = 0  # Ground level
            z = random.uniform(-10, 10)
            
            scene_data['objects'].append({
                'asset_id': asset['asset_id'],
                'model_path': asset['model_path'],
                'position': (x, y, z),
                'rotation': (0, random.uniform(0, 360), 0),
                'scale': (1, 1, 1)
            })
        
        # Add default camera
        scene_data['cameras'].append({
            'position': (0, 5, 15),
            'look_at': (0, 0, 0)
        })
        
        return scene_data
    
    def _setup_environment(self, scene_data: Dict, prompt: str):
        """Setup lighting and environment.
        
        Args:
            scene_data: Scene assembly data
            prompt: Original prompt for mood
        """
        # Infer lighting from prompt
        prompt_lower = prompt.lower()
        
        if 'night' in prompt_lower or 'dark' in prompt_lower:
            # Dark scene
            scene_data['lights'].append({
                'type': 'directional',
                'intensity': 0.3,
                'color': (0.7, 0.7, 1.0)
            })
        elif 'sunset' in prompt_lower or 'dusk' in prompt_lower:
            # Warm lighting
            scene_data['lights'].append({
                'type': 'directional',
                'intensity': 0.7,
                'color': (1.0, 0.7, 0.5)
            })
        else:
            # Default daylight
            scene_data['lights'].append({
                'type': 'directional',
                'intensity': 1.0,
                'color': (1.0, 1.0, 1.0)
            })
        
        # Add ambient light
        scene_data['lights'].append({
            'type': 'ambient',
            'intensity': 0.4,
            'color': (1.0, 1.0, 1.0)
        })
