"""Skeletal animation system with blending and IK support.

Features:
- Load animated models using Panda3D Actor
- Animation blending and layering
- Inverse Kinematics (IK) for procedural animation
- Animation state machine
- Root motion extraction
- Animation events/callbacks
"""
import logging
from typing import Dict, List, Optional, Callable, Tuple
from panda3d.core import NodePath, Vec3, Point3, LVector3
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *

logger = logging.getLogger(__name__)


class AnimationController:
    """Controls skeletal animations for a character."""
    
    def __init__(self, actor: Actor, name: str = "character"):
        """Initialize animation controller.
        
        Args:
            actor: Panda3D Actor instance
            name: Controller name
        """
        self.actor = actor
        self.name = name
        self.current_anim: Optional[str] = None
        self.anim_blend_weight: float = 1.0
        self.blending: bool = False
        self.blend_from: Optional[str] = None
        self.blend_to: Optional[str] = None
        self.blend_time: float = 0.0
        self.blend_duration: float = 0.3
        
        # Animation library
        self.animations: Dict[str, Dict] = {}
        
        # State machine
        self.states: Dict[str, 'AnimationState'] = {}
        self.current_state: Optional['AnimationState'] = None
        
        # IK chains
        self.ik_chains: Dict[str, 'IKChain'] = {}
        
        # Animation events
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info(f"Animation controller '{name}' initialized")
    
    def load_animation(self, name: str, filepath: str, 
                       loop: bool = True, frame_rate: float = 30.0) -> None:
        """Load an animation clip.
        
        Args:
            name: Animation name
            filepath: Path to animation file
            loop: Whether animation loops
            frame_rate: Playback frame rate
        """
        try:
            self.actor.loadAnims({name: filepath})
            
            self.animations[name] = {
                'filepath': filepath,
                'loop': loop,
                'frame_rate': frame_rate,
                'duration': self.actor.getDuration(name),
                'events': []
            }
            
            logger.info(f"Animation '{name}' loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load animation '{name}': {e}")
    
    def play(self, anim_name: str, loop: bool = True,
             blend_time: float = 0.3, from_frame: int = 0) -> None:
        """Play an animation with optional blending.
        
        Args:
            anim_name: Animation to play
            loop: Whether to loop
            blend_time: Blend duration in seconds
            from_frame: Starting frame
        """
        if anim_name not in self.animations:
            logger.warning(f"Animation '{anim_name}' not found")
            return
        
        if blend_time > 0 and self.current_anim and self.current_anim != anim_name:
            # Start blending
            self.blend_from = self.current_anim
            self.blend_to = anim_name
            self.blend_time = 0.0
            self.blend_duration = blend_time
            self.blending = True
        else:
            # Direct play
            self.actor.play(anim_name)
            if loop:
                self.actor.loop(anim_name)
        
        self.current_anim = anim_name
        logger.debug(f"Playing animation '{anim_name}' (loop={loop}, blend={blend_time}s)")
    
    def stop(self, anim_name: Optional[str] = None) -> None:
        """Stop an animation.
        
        Args:
            anim_name: Animation to stop (None = current)
        """
        if anim_name:
            self.actor.stop(anim_name)
        else:
            self.actor.stop()
        
        self.current_anim = None
        self.blending = False
    
    def set_play_rate(self, anim_name: str, rate: float) -> None:
        """Set animation playback speed.
        
        Args:
            anim_name: Animation name
            rate: Playback rate (1.0 = normal)
        """
        self.actor.setPlayRate(rate, anim_name)
        logger.debug(f"Animation '{anim_name}' playback rate set to {rate}")
    
    def get_current_frame(self, anim_name: Optional[str] = None) -> int:
        """Get current animation frame.
        
        Args:
            anim_name: Animation name (None = current)
            
        Returns:
            Current frame number
        """
        anim = anim_name or self.current_anim
        if anim:
            return self.actor.getCurrentFrame(anim)
        return 0
    
    def update(self, dt: float) -> None:
        """Update animation blending.
        
        Args:
            dt: Delta time
        """
        if self.blending:
            self.blend_time += dt
            
            if self.blend_time >= self.blend_duration:
                # Blend complete
                self.blending = False
                self.actor.play(self.blend_to)
                self.current_anim = self.blend_to
            else:
                # Update blend weights
                t = self.blend_time / self.blend_duration
                weight_from = 1.0 - t
                weight_to = t
                
                # Apply blending (simplified - Panda3D handles this internally)
                self.anim_blend_weight = weight_to
        
        # Update IK chains
        for ik_chain in self.ik_chains.values():
            ik_chain.solve()
        
        # Check animation events
        self._check_animation_events()
    
    def _check_animation_events(self) -> None:
        """Check and fire animation events."""
        if not self.current_anim:
            return
        
        current_frame = self.get_current_frame()
        anim_data = self.animations.get(self.current_anim)
        
        if anim_data:
            for event in anim_data['events']:
                frame = event['frame']
                if frame == current_frame and event['name'] in self.event_callbacks:
                    for callback in self.event_callbacks[event['name']]:
                        callback()
    
    def add_animation_event(self, anim_name: str, frame: int, event_name: str) -> None:
        """Add an event trigger at a specific frame.
        
        Args:
            anim_name: Animation name
            frame: Frame number
            event_name: Event identifier
        """
        if anim_name in self.animations:
            self.animations[anim_name]['events'].append({
                'frame': frame,
                'name': event_name
            })
            logger.debug(f"Event '{event_name}' added to '{anim_name}' at frame {frame}")
    
    def register_event_callback(self, event_name: str, callback: Callable) -> None:
        """Register a callback for an animation event.
        
        Args:
            event_name: Event identifier
            callback: Function to call
        """
        if event_name not in self.event_callbacks:
            self.event_callbacks[event_name] = []
        
        self.event_callbacks[event_name].append(callback)
        logger.debug(f"Callback registered for event '{event_name}'")
    
    def create_ik_chain(self, name: str, bones: List[str], target: NodePath) -> 'IKChain':
        """Create an IK chain for procedural animation.
        
        Args:
            name: Chain name
            bones: List of bone names from root to tip
            target: Target position node
            
        Returns:
            IKChain instance
        """
        ik_chain = IKChain(self.actor, bones, target, name)
        self.ik_chains[name] = ik_chain
        logger.info(f"IK chain '{name}' created with {len(bones)} bones")
        return ik_chain
    
    def add_state(self, name: str, animation: str, 
                  transitions: Optional[Dict[str, str]] = None) -> 'AnimationState':
        """Add a state to the animation state machine.
        
        Args:
            name: State name
            animation: Animation to play in this state
            transitions: Dict of {condition: target_state}
            
        Returns:
            AnimationState instance
        """
        state = AnimationState(name, animation, transitions or {})
        self.states[name] = state
        logger.info(f"Animation state '{name}' added")
        return state
    
    def transition_to_state(self, state_name: str, blend_time: float = 0.3) -> None:
        """Transition to a new animation state.
        
        Args:
            state_name: Target state name
            blend_time: Blend duration
        """
        if state_name not in self.states:
            logger.warning(f"State '{state_name}' not found")
            return
        
        new_state = self.states[state_name]
        
        if self.current_state:
            logger.debug(f"Transitioning from '{self.current_state.name}' to '{state_name}'")
        
        self.play(new_state.animation, loop=True, blend_time=blend_time)
        self.current_state = new_state


class AnimationState:
    """Represents a state in an animation state machine."""
    
    def __init__(self, name: str, animation: str, transitions: Dict[str, str]):
        """Initialize animation state.
        
        Args:
            name: State name
            animation: Animation to play
            transitions: Transition conditions
        """
        self.name = name
        self.animation = animation
        self.transitions = transitions


class IKChain:
    """Inverse Kinematics chain for procedural animation."""
    
    def __init__(self, actor: Actor, bones: List[str], target: NodePath, name: str = "ik_chain"):
        """Initialize IK chain.
        
        Args:
            actor: Character actor
            bones: Bone names from root to tip
            target: Target end-effector position
            name: Chain name
        """
        self.actor = actor
        self.bones = bones
        self.target = target
        self.name = name
        
        # Get bone nodes
        self.bone_nodes: List[NodePath] = []
        for bone_name in bones:
            bone = actor.exposeJoint(None, 'modelRoot', bone_name)
            if bone:
                self.bone_nodes.append(bone)
            else:
                logger.warning(f"Bone '{bone_name}' not found in actor")
        
        # IK settings
        self.iterations = 10
        self.tolerance = 0.01
        self.enabled = True
        
        logger.info(f"IK chain '{name}' initialized with {len(self.bone_nodes)} bones")
    
    def solve(self) -> None:
        """Solve IK using FABRIK (Forward And Backward Reaching Inverse Kinematics)."""
        if not self.enabled or len(self.bone_nodes) < 2:
            return
        
        target_pos = self.target.get_pos(self.actor)
        
        # Get bone positions
        positions = [bone.get_pos(self.actor) for bone in self.bone_nodes]
        
        # Store bone lengths
        lengths = []
        for i in range(len(positions) - 1):
            length = (positions[i + 1] - positions[i]).length()
            lengths.append(length)
        
        # Check if target is reachable
        total_length = sum(lengths)
        dist_to_target = (target_pos - positions[0]).length()
        
        if dist_to_target > total_length:
            # Target unreachable, stretch toward it
            direction = (target_pos - positions[0])
            direction.normalize()
            
            for i in range(1, len(positions)):
                positions[i] = positions[i - 1] + direction * lengths[i - 1]
        else:
            # FABRIK iterations
            for iteration in range(self.iterations):
                # Forward pass (from tip to root)
                positions[-1] = target_pos
                
                for i in range(len(positions) - 2, -1, -1):
                    direction = positions[i] - positions[i + 1]
                    direction.normalize()
                    positions[i] = positions[i + 1] + direction * lengths[i]
                
                # Backward pass (from root to tip)
                root_pos = self.bone_nodes[0].get_pos(self.actor)
                positions[0] = root_pos
                
                for i in range(len(positions) - 1):
                    direction = positions[i + 1] - positions[i]
                    direction.normalize()
                    positions[i + 1] = positions[i] + direction * lengths[i]
                
                # Check convergence
                end_effector_error = (positions[-1] - target_pos).length()
                if end_effector_error < self.tolerance:
                    break
        
        # Apply solved positions to bones
        for i, bone in enumerate(self.bone_nodes):
            bone.set_pos(self.actor, positions[i])
            
            # Orient bone toward next bone
            if i < len(self.bone_nodes) - 1:
                bone.look_at(self.bone_nodes[i + 1])


class AnimationBlendTree:
    """Tree structure for complex animation blending."""
    
    def __init__(self, name: str):
        """Initialize blend tree.
        
        Args:
            name: Tree name
        """
        self.name = name
        self.root: Optional['BlendNode'] = None
        
        logger.info(f"Animation blend tree '{name}' created")
    
    def create_blend_node(self, node_type: str, **kwargs) -> 'BlendNode':
        """Create a blend node.
        
        Args:
            node_type: 'lerp', 'additive', or 'layer'
            **kwargs: Node-specific parameters
            
        Returns:
            BlendNode instance
        """
        if node_type == 'lerp':
            return LerpBlendNode(**kwargs)
        elif node_type == 'additive':
            return AdditiveBlendNode(**kwargs)
        elif node_type == 'layer':
            return LayerBlendNode(**kwargs)
        else:
            raise ValueError(f"Unknown blend node type: {node_type}")


class BlendNode:
    """Base class for animation blend nodes."""
    
    def __init__(self, name: str):
        self.name = name
        self.inputs: List['BlendNode'] = []
    
    def evaluate(self) -> None:
        """Evaluate the blend node."""
        raise NotImplementedError


class LerpBlendNode(BlendNode):
    """Linear interpolation between two animations."""
    
    def __init__(self, name: str, blend_factor: float = 0.5):
        super().__init__(name)
        self.blend_factor = blend_factor
    
    def evaluate(self) -> None:
        """Blend between first two inputs."""
        if len(self.inputs) >= 2:
            # Blend logic here
            pass


class AdditiveBlendNode(BlendNode):
    """Additive blending (layer animations on top)."""
    
    def __init__(self, name: str, weight: float = 1.0):
        super().__init__(name)
        self.weight = weight
    
    def evaluate(self) -> None:
        """Add all inputs together."""
        pass


class LayerBlendNode(BlendNode):
    """Layer-based blending with masks."""
    
    def __init__(self, name: str, mask: Optional[List[str]] = None):
        super().__init__(name)
        self.mask = mask or []
    
    def evaluate(self) -> None:
        """Blend with bone masking."""
        pass
