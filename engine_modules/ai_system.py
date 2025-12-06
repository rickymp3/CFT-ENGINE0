"""
CFT-ENGINE0 Advanced AI System
Behavior trees, navigation mesh, pathfinding, and ML integration
"""

import numpy as np
from panda3d.core import Point3, Vec3, NodePath, LineSegs, CollisionRay, CollisionTraverser, CollisionHandlerQueue
from enum import Enum
import heapq
import json
from typing import List, Dict, Optional, Callable, Tuple
import asyncio


# ==================== Behavior Tree Framework ====================

class NodeStatus(Enum):
    """Status of a behavior tree node execution"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode:
    """Base class for all behavior tree nodes"""
    
    def __init__(self, name: str = "Node"):
        self.name = name
        self.status = NodeStatus.FAILURE
    
    def tick(self, agent, dt: float) -> NodeStatus:
        """Execute this node. Override in subclasses."""
        raise NotImplementedError
    
    def reset(self):
        """Reset node state"""
        self.status = NodeStatus.FAILURE


class CompositeNode(BehaviorNode):
    """Node that contains child nodes"""
    
    def __init__(self, name: str = "Composite", children: List[BehaviorNode] = None):
        super().__init__(name)
        self.children = children or []
        self.current_child = 0
    
    def add_child(self, child: BehaviorNode):
        self.children.append(child)
    
    def reset(self):
        super().reset()
        self.current_child = 0
        for child in self.children:
            child.reset()


class SequenceNode(CompositeNode):
    """Executes children in order, fails if any child fails"""
    
    def tick(self, agent, dt: float) -> NodeStatus:
        while self.current_child < len(self.children):
            child = self.children[self.current_child]
            status = child.tick(agent, dt)
            
            if status == NodeStatus.RUNNING:
                self.status = NodeStatus.RUNNING
                return self.status
            elif status == NodeStatus.FAILURE:
                self.reset()
                self.status = NodeStatus.FAILURE
                return self.status
            
            self.current_child += 1
        
        self.reset()
        self.status = NodeStatus.SUCCESS
        return self.status


class SelectorNode(CompositeNode):
    """Executes children until one succeeds"""
    
    def tick(self, agent, dt: float) -> NodeStatus:
        while self.current_child < len(self.children):
            child = self.children[self.current_child]
            status = child.tick(agent, dt)
            
            if status == NodeStatus.RUNNING:
                self.status = NodeStatus.RUNNING
                return self.status
            elif status == NodeStatus.SUCCESS:
                self.reset()
                self.status = NodeStatus.SUCCESS
                return self.status
            
            self.current_child += 1
        
        self.reset()
        self.status = NodeStatus.FAILURE
        return self.status


class ParallelNode(CompositeNode):
    """Executes all children simultaneously"""
    
    def __init__(self, name: str = "Parallel", require_all: bool = True, children: List[BehaviorNode] = None):
        super().__init__(name, children)
        self.require_all = require_all
    
    def tick(self, agent, dt: float) -> NodeStatus:
        success_count = 0
        failure_count = 0
        
        for child in self.children:
            status = child.tick(agent, dt)
            if status == NodeStatus.SUCCESS:
                success_count += 1
            elif status == NodeStatus.FAILURE:
                failure_count += 1
        
        if self.require_all:
            if success_count == len(self.children):
                self.status = NodeStatus.SUCCESS
            elif failure_count > 0:
                self.status = NodeStatus.FAILURE
            else:
                self.status = NodeStatus.RUNNING
        else:
            if success_count > 0:
                self.status = NodeStatus.SUCCESS
            elif failure_count == len(self.children):
                self.status = NodeStatus.FAILURE
            else:
                self.status = NodeStatus.RUNNING
        
        return self.status


class DecoratorNode(BehaviorNode):
    """Wraps a single child node"""
    
    def __init__(self, name: str = "Decorator", child: BehaviorNode = None):
        super().__init__(name)
        self.child = child
    
    def reset(self):
        super().reset()
        if self.child:
            self.child.reset()


class InverterNode(DecoratorNode):
    """Inverts child's success/failure"""
    
    def tick(self, agent, dt: float) -> NodeStatus:
        if not self.child:
            self.status = NodeStatus.FAILURE
            return self.status
        
        status = self.child.tick(agent, dt)
        
        if status == NodeStatus.SUCCESS:
            self.status = NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            self.status = NodeStatus.SUCCESS
        else:
            self.status = NodeStatus.RUNNING
        
        return self.status


class RepeaterNode(DecoratorNode):
    """Repeats child N times or indefinitely"""
    
    def __init__(self, name: str = "Repeater", child: BehaviorNode = None, count: int = -1):
        super().__init__(name, child)
        self.count = count  # -1 for infinite
        self.current_count = 0
    
    def tick(self, agent, dt: float) -> NodeStatus:
        if not self.child:
            self.status = NodeStatus.FAILURE
            return self.status
        
        if self.count > 0 and self.current_count >= self.count:
            self.current_count = 0
            self.status = NodeStatus.SUCCESS
            return self.status
        
        status = self.child.tick(agent, dt)
        
        if status != NodeStatus.RUNNING:
            self.current_count += 1
            self.child.reset()
        
        self.status = NodeStatus.RUNNING if self.count == -1 or self.current_count < self.count else NodeStatus.SUCCESS
        return self.status


class ConditionNode(BehaviorNode):
    """Evaluates a condition function"""
    
    def __init__(self, name: str = "Condition", condition: Callable = None):
        super().__init__(name)
        self.condition = condition or (lambda agent: False)
    
    def tick(self, agent, dt: float) -> NodeStatus:
        self.status = NodeStatus.SUCCESS if self.condition(agent) else NodeStatus.FAILURE
        return self.status


class ActionNode(BehaviorNode):
    """Executes an action function"""
    
    def __init__(self, name: str = "Action", action: Callable = None):
        super().__init__(name)
        self.action = action or (lambda agent, dt: NodeStatus.SUCCESS)
    
    def tick(self, agent, dt: float) -> NodeStatus:
        self.status = self.action(agent, dt)
        return self.status


class BehaviorTree:
    """Complete behavior tree with root node"""
    
    def __init__(self, root: BehaviorNode):
        self.root = root
    
    def tick(self, agent, dt: float) -> NodeStatus:
        """Execute the behavior tree"""
        return self.root.tick(agent, dt)
    
    def reset(self):
        """Reset entire tree"""
        self.root.reset()


# ==================== Navigation Mesh ====================

class NavMeshNode:
    """Single node/polygon in navigation mesh"""
    
    def __init__(self, center: Point3, radius: float, walkable: bool = True):
        self.center = center
        self.radius = radius
        self.walkable = walkable
        self.neighbors: List[NavMeshNode] = []
        self.cost = 1.0  # Movement cost multiplier
    
    def add_neighbor(self, node: 'NavMeshNode'):
        if node not in self.neighbors:
            self.neighbors.append(node)
            node.neighbors.append(self)
    
    def distance_to(self, other: 'NavMeshNode') -> float:
        return (self.center - other.center).length()


class NavigationMesh:
    """Navigation mesh for pathfinding"""
    
    def __init__(self, grid_size: Tuple[int, int, int] = (20, 20, 10), cell_size: float = 2.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.nodes: List[NavMeshNode] = []
        self.grid: Dict[Tuple[int, int, int], NavMeshNode] = {}
        self.debug_visual: Optional[NodePath] = None
    
    def generate_grid(self, bounds_min: Point3, bounds_max: Point3):
        """Generate a grid-based navigation mesh"""
        self.nodes.clear()
        self.grid.clear()
        
        x_range = int((bounds_max.x - bounds_min.x) / self.cell_size)
        y_range = int((bounds_max.y - bounds_min.y) / self.cell_size)
        z_range = int((bounds_max.z - bounds_min.z) / self.cell_size)
        
        # Create nodes
        for x in range(x_range):
            for y in range(y_range):
                for z in range(z_range):
                    pos = Point3(
                        bounds_min.x + x * self.cell_size,
                        bounds_min.y + y * self.cell_size,
                        bounds_min.z + z * self.cell_size
                    )
                    node = NavMeshNode(pos, self.cell_size / 2)
                    self.nodes.append(node)
                    self.grid[(x, y, z)] = node
        
        # Connect neighbors (6-connectivity)
        for x in range(x_range):
            for y in range(y_range):
                for z in range(z_range):
                    node = self.grid[(x, y, z)]
                    
                    # Connect to adjacent cells
                    for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if (nx, ny, nz) in self.grid:
                            neighbor = self.grid[(nx, ny, nz)]
                            if neighbor not in node.neighbors:
                                node.add_neighbor(neighbor)
    
    def mark_obstacle(self, position: Point3, radius: float):
        """Mark area as non-walkable"""
        for node in self.nodes:
            if (node.center - position).length() <= radius + node.radius:
                node.walkable = False
    
    def find_nearest_node(self, position: Point3) -> Optional[NavMeshNode]:
        """Find closest walkable node to position"""
        closest = None
        min_dist = float('inf')
        
        for node in self.nodes:
            if not node.walkable:
                continue
            dist = (node.center - position).length()
            if dist < min_dist:
                min_dist = dist
                closest = node
        
        return closest
    
    def find_path(self, start: Point3, goal: Point3) -> List[Point3]:
        """A* pathfinding"""
        start_node = self.find_nearest_node(start)
        goal_node = self.find_nearest_node(goal)
        
        if not start_node or not goal_node:
            return []
        
        # A* algorithm
        open_set = [(0, start_node)]
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: start_node.distance_to(goal_node)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal_node:
                # Reconstruct path
                path = [goal]
                node = goal_node
                while node in came_from:
                    path.append(node.center)
                    node = came_from[node]
                path.append(start)
                return list(reversed(path))
            
            for neighbor in current.neighbors:
                if not neighbor.walkable:
                    continue
                
                tentative_g = g_score[current] + current.distance_to(neighbor) * neighbor.cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + neighbor.distance_to(goal_node)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found
    
    def create_debug_visual(self, render: NodePath) -> NodePath:
        """Create visual representation of navmesh"""
        if self.debug_visual:
            self.debug_visual.remove_node()
        
        lines = LineSegs()
        lines.set_thickness(2.0)
        
        # Draw nodes
        for node in self.nodes:
            if node.walkable:
                lines.set_color(0, 1, 0, 0.5)
            else:
                lines.set_color(1, 0, 0, 0.5)
            
            # Draw connections
            for neighbor in node.neighbors:
                if neighbor.walkable and node.walkable:
                    lines.move_to(node.center)
                    lines.draw_to(neighbor.center)
        
        self.debug_visual = render.attach_new_node(lines.create())
        return self.debug_visual


# ==================== AI Agent ====================

class AIAgent:
    """AI-controlled agent with behavior tree and pathfinding"""
    
    def __init__(self, name: str, node_path: NodePath, navmesh: NavigationMesh):
        self.name = name
        self.node_path = node_path
        self.navmesh = navmesh
        self.behavior_tree: Optional[BehaviorTree] = None
        
        # State
        self.position = Point3(0, 0, 0)
        self.velocity = Vec3(0, 0, 0)
        self.target_position: Optional[Point3] = None
        self.path: List[Point3] = []
        self.current_path_index = 0
        
        # Properties
        self.max_speed = 5.0
        self.acceleration = 10.0
        self.stopping_distance = 0.5
        
        # Perception
        self.visible_agents: List['AIAgent'] = []
        self.visible_objects: List[NodePath] = []
        self.vision_range = 20.0
        self.vision_angle = 120.0  # degrees
        
        # Custom data for behaviors
        self.blackboard: Dict = {}
    
    def set_behavior_tree(self, tree: BehaviorTree):
        """Set the behavior tree for this agent"""
        self.behavior_tree = tree
    
    def set_target(self, target: Point3):
        """Set movement target and calculate path"""
        self.target_position = target
        self.path = self.navmesh.find_path(self.position, target)
        self.current_path_index = 0
    
    def move_to_next_waypoint(self, dt: float) -> NodeStatus:
        """Move along calculated path"""
        if not self.path or self.current_path_index >= len(self.path):
            return NodeStatus.SUCCESS
        
        waypoint = self.path[self.current_path_index]
        direction = waypoint - self.position
        distance = direction.length()
        
        if distance < self.stopping_distance:
            self.current_path_index += 1
            if self.current_path_index >= len(self.path):
                self.velocity = Vec3(0, 0, 0)
                return NodeStatus.SUCCESS
            return NodeStatus.RUNNING
        
        # Steer toward waypoint
        direction.normalize()
        desired_velocity = direction * self.max_speed
        steering = desired_velocity - self.velocity
        
        self.velocity += steering * self.acceleration * dt
        if self.velocity.length() > self.max_speed:
            self.velocity.normalize()
            self.velocity *= self.max_speed
        
        self.position += self.velocity * dt
        self.node_path.set_pos(self.position)
        
        return NodeStatus.RUNNING
    
    def update_perception(self, all_agents: List['AIAgent'], collision_system=None):
        """Update what the agent can see"""
        self.visible_agents.clear()
        
        forward = self.node_path.get_quat().get_forward()
        
        for agent in all_agents:
            if agent == self:
                continue
            
            to_agent = agent.position - self.position
            distance = to_agent.length()
            
            if distance > self.vision_range:
                continue
            
            to_agent.normalize()
            angle = np.degrees(np.arccos(np.clip(forward.dot(to_agent), -1, 1)))
            
            if angle <= self.vision_angle / 2:
                self.visible_agents.append(agent)
    
    def update(self, dt: float):
        """Update agent"""
        self.position = self.node_path.get_pos()
        
        if self.behavior_tree:
            self.behavior_tree.tick(self, dt)


# ==================== AI System Manager ====================

class AISystem:
    """Manages all AI agents and navigation"""
    
    def __init__(self, base):
        self.base = base
        self.agents: List[AIAgent] = []
        self.navmesh: Optional[NavigationMesh] = None
        
        # ML integration
        self.ml_models: Dict[str, any] = {}
    
    def create_navmesh(self, grid_size: Tuple[int, int, int] = (20, 20, 10), cell_size: float = 2.0):
        """Create navigation mesh"""
        self.navmesh = NavigationMesh(grid_size, cell_size)
        return self.navmesh
    
    def create_agent(self, name: str, node_path: NodePath) -> AIAgent:
        """Create new AI agent"""
        if not self.navmesh:
            self.create_navmesh()
        
        agent = AIAgent(name, node_path, self.navmesh)
        self.agents.append(agent)
        return agent
    
    def remove_agent(self, agent: AIAgent):
        """Remove agent from system"""
        if agent in self.agents:
            self.agents.remove(agent)
    
    def get_state(self) -> Dict[str, any]:
        """Expose basic AI system telemetry."""
        return {
            "agents": len(self.agents),
            "navmesh": {
                "exists": self.navmesh is not None,
                "grid_size": getattr(self.navmesh, "grid_size", None),
                "cell_size": getattr(self.navmesh, "cell_size", None),
                "nodes": len(self.navmesh.nodes) if self.navmesh else 0,
            }
        }
    
    def load_ml_model(self, name: str, model_path: str, backend: str = "onnx"):
        """Load ML model for inference (ONNX or TensorFlow Lite)"""
        try:
            if backend == "onnx":
                import onnxruntime as ort
                session = ort.InferenceSession(model_path)
                self.ml_models[name] = {
                    'type': 'onnx',
                    'session': session,
                    'inputs': [inp.name for inp in session.get_inputs()],
                    'outputs': [out.name for out in session.get_outputs()]
                }
                print(f"Loaded ONNX model: {name}")
            elif backend == "tflite":
                import tensorflow as tf
                interpreter = tf.lite.Interpreter(model_path=model_path)
                interpreter.allocate_tensors()
                self.ml_models[name] = {
                    'type': 'tflite',
                    'interpreter': interpreter,
                    'inputs': interpreter.get_input_details(),
                    'outputs': interpreter.get_output_details()
                }
                print(f"Loaded TFLite model: {name}")
        except ImportError as e:
            print(f"ML backend not available: {e}")
    
    def run_inference(self, model_name: str, input_data: np.ndarray) -> np.ndarray:
        """Run inference on loaded model"""
        if model_name not in self.ml_models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.ml_models[model_name]
        
        if model['type'] == 'onnx':
            session = model['session']
            input_name = model['inputs'][0]
            result = session.run(None, {input_name: input_data})
            return result[0]
        elif model['type'] == 'tflite':
            interpreter = model['interpreter']
            interpreter.set_tensor(model['inputs'][0]['index'], input_data)
            interpreter.invoke()
            return interpreter.get_tensor(model['outputs'][0]['index'])
    
    def update(self, dt: float):
        """Update all agents"""
        # Update perception for all agents
        for agent in self.agents:
            agent.update_perception(self.agents)
        
        # Update agent behaviors
        for agent in self.agents:
            agent.update(dt)


# ==================== Helper Functions ====================

def create_patrol_behavior(waypoints: List[Point3]) -> BehaviorTree:
    """Create a simple patrol behavior"""
    waypoint_index = [0]  # Mutable container for closure
    
    def next_waypoint(agent, dt):
        agent.set_target(waypoints[waypoint_index[0]])
        waypoint_index[0] = (waypoint_index[0] + 1) % len(waypoints)
        return NodeStatus.SUCCESS
    
    def at_waypoint(agent):
        if not agent.path:
            return True
        return agent.current_path_index >= len(agent.path)
    
    root = SequenceNode("Patrol", [
        ConditionNode("AtWaypoint", at_waypoint),
        ActionNode("NextWaypoint", next_waypoint)
    ])
    
    return BehaviorTree(RepeaterNode("Forever", root, count=-1))


def create_chase_behavior(target_getter: Callable) -> BehaviorTree:
    """Create chase behavior"""
    
    def update_chase_target(agent, dt):
        target = target_getter(agent)
        if target:
            agent.set_target(target)
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE
    
    def chase(agent, dt):
        return agent.move_to_next_waypoint(dt)
    
    root = SequenceNode("Chase", [
        ActionNode("UpdateTarget", update_chase_target),
        ActionNode("MoveToTarget", chase)
    ])
    
    return BehaviorTree(RepeaterNode("Forever", root, count=-1))


def create_ai_system(base) -> AISystem:
    """Factory function to create AI system"""
    return AISystem(base)
