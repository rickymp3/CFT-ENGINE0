"""Visual scripting system with node-based logic editor.

Features:
- Node-based visual programming
- Game logic nodes (input, math, logic, events)
- Python code generation
- Runtime execution
- Save/load node graphs
"""
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import tkinter as tk
from tkinter import ttk, Canvas, messagebox

logger = logging.getLogger(__name__)


class PinType(Enum):
    """Data types for node pins."""
    EXEC = "exec"  # Execution flow
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    VECTOR3 = "vector3"
    NODE = "node"  # NodePath reference
    ANY = "any"


class PinDirection(Enum):
    """Pin direction."""
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class NodePin:
    """Input or output pin on a node."""
    name: str
    pin_type: PinType
    direction: PinDirection
    node_id: str
    connected_to: List[str] = field(default_factory=list)  # List of "node_id:pin_name"
    default_value: Any = None
    
    def get_connection_id(self) -> str:
        """Get unique connection ID."""
        return f"{self.node_id}:{self.name}"


@dataclass
class ScriptNode:
    """A node in the visual script."""
    node_id: str
    node_type: str
    x: float
    y: float
    inputs: List[NodePin] = field(default_factory=list)
    outputs: List[NodePin] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'x': self.x,
            'y': self.y,
            'inputs': [{'name': p.name, 'type': p.pin_type.value, 'direction': p.direction.value, 
                       'connected_to': p.connected_to, 'default_value': p.default_value} 
                      for p in self.inputs],
            'outputs': [{'name': p.name, 'type': p.pin_type.value, 'direction': p.direction.value,
                        'connected_to': p.connected_to} 
                       for p in self.outputs],
            'parameters': self.parameters
        }


class VisualScript:
    """Container for a visual script graph."""
    
    def __init__(self, name: str = "NewScript"):
        """Initialize visual script.
        
        Args:
            name: Script name
        """
        self.name = name
        self.nodes: Dict[str, ScriptNode] = {}
        self.next_node_id = 1
        
        logger.info(f"Visual script created: {name}")
    
    def add_node(self, node_type: str, x: float, y: float, **params) -> ScriptNode:
        """Add a node to the script.
        
        Args:
            node_type: Type of node to add
            x: X position
            y: Y position
            **params: Node parameters
            
        Returns:
            Created node
        """
        node_id = f"node_{self.next_node_id}"
        self.next_node_id += 1
        
        node = self._create_node(node_id, node_type, x, y, **params)
        self.nodes[node_id] = node
        
        logger.debug(f"Added node: {node_type} ({node_id})")
        return node
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node.
        
        Args:
            node_id: Node to remove
        """
        if node_id in self.nodes:
            # Remove connections
            node = self.nodes[node_id]
            for pin in node.inputs + node.outputs:
                for conn_id in pin.connected_to[:]:
                    self.disconnect(pin.get_connection_id(), conn_id)
            
            del self.nodes[node_id]
            logger.debug(f"Removed node: {node_id}")
    
    def connect(self, from_pin: str, to_pin: str) -> bool:
        """Connect two pins.
        
        Args:
            from_pin: Output pin ID (node_id:pin_name)
            to_pin: Input pin ID (node_id:pin_name)
            
        Returns:
            True if connected successfully
        """
        from_node_id, from_pin_name = from_pin.split(':')
        to_node_id, to_pin_name = to_pin.split(':')
        
        from_node = self.nodes.get(from_node_id)
        to_node = self.nodes.get(to_node_id)
        
        if not from_node or not to_node:
            return False
        
        # Find pins
        output_pin = next((p for p in from_node.outputs if p.name == from_pin_name), None)
        input_pin = next((p for p in to_node.inputs if p.name == to_pin_name), None)
        
        if not output_pin or not input_pin:
            return False
        
        # Type checking (allow ANY to connect to anything)
        if output_pin.pin_type != PinType.ANY and input_pin.pin_type != PinType.ANY:
            if output_pin.pin_type != input_pin.pin_type:
                logger.warning(f"Type mismatch: {output_pin.pin_type} -> {input_pin.pin_type}")
                return False
        
        # Add connection
        if to_pin not in output_pin.connected_to:
            output_pin.connected_to.append(to_pin)
        if from_pin not in input_pin.connected_to:
            input_pin.connected_to.append(from_pin)
        
        logger.debug(f"Connected: {from_pin} -> {to_pin}")
        return True
    
    def disconnect(self, pin1: str, pin2: str) -> None:
        """Disconnect two pins.
        
        Args:
            pin1: First pin ID
            pin2: Second pin ID
        """
        node1_id, pin1_name = pin1.split(':')
        node2_id, pin2_name = pin2.split(':')
        
        node1 = self.nodes.get(node1_id)
        node2 = self.nodes.get(node2_id)
        
        if node1:
            for pin in node1.inputs + node1.outputs:
                if pin.name == pin1_name and pin2 in pin.connected_to:
                    pin.connected_to.remove(pin2)
        
        if node2:
            for pin in node2.inputs + node2.outputs:
                if pin.name == pin2_name and pin1 in pin.connected_to:
                    pin.connected_to.remove(pin1)
        
        logger.debug(f"Disconnected: {pin1} <-> {pin2}")
    
    def _create_node(self, node_id: str, node_type: str, x: float, y: float, **params) -> ScriptNode:
        """Create a node based on type.
        
        Args:
            node_id: Unique node ID
            node_type: Type of node
            x: X position
            y: Y position
            **params: Node parameters
            
        Returns:
            Created node
        """
        node = ScriptNode(node_id=node_id, node_type=node_type, x=x, y=y, parameters=params)
        
        # Define node types and their pins
        if node_type == "Event_BeginPlay":
            node.outputs.append(NodePin("Exec", PinType.EXEC, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Event_Tick":
            node.outputs.append(NodePin("Exec", PinType.EXEC, PinDirection.OUTPUT, node_id))
            node.outputs.append(NodePin("DeltaTime", PinType.FLOAT, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Event_KeyPressed":
            node.outputs.append(NodePin("Exec", PinType.EXEC, PinDirection.OUTPUT, node_id))
            node.outputs.append(NodePin("Key", PinType.STRING, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Math_Add":
            node.inputs.append(NodePin("A", PinType.FLOAT, PinDirection.INPUT, node_id, default_value=0.0))
            node.inputs.append(NodePin("B", PinType.FLOAT, PinDirection.INPUT, node_id, default_value=0.0))
            node.outputs.append(NodePin("Result", PinType.FLOAT, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Math_Multiply":
            node.inputs.append(NodePin("A", PinType.FLOAT, PinDirection.INPUT, node_id, default_value=1.0))
            node.inputs.append(NodePin("B", PinType.FLOAT, PinDirection.INPUT, node_id, default_value=1.0))
            node.outputs.append(NodePin("Result", PinType.FLOAT, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Logic_Branch":
            node.inputs.append(NodePin("Exec", PinType.EXEC, PinDirection.INPUT, node_id))
            node.inputs.append(NodePin("Condition", PinType.BOOL, PinDirection.INPUT, node_id))
            node.outputs.append(NodePin("True", PinType.EXEC, PinDirection.OUTPUT, node_id))
            node.outputs.append(NodePin("False", PinType.EXEC, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Logic_Compare":
            node.inputs.append(NodePin("A", PinType.FLOAT, PinDirection.INPUT, node_id))
            node.inputs.append(NodePin("B", PinType.FLOAT, PinDirection.INPUT, node_id))
            node.outputs.append(NodePin("Equal", PinType.BOOL, PinDirection.OUTPUT, node_id))
            node.outputs.append(NodePin("Greater", PinType.BOOL, PinDirection.OUTPUT, node_id))
            node.outputs.append(NodePin("Less", PinType.BOOL, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Node_SetPosition":
            node.inputs.append(NodePin("Exec", PinType.EXEC, PinDirection.INPUT, node_id))
            node.inputs.append(NodePin("Node", PinType.NODE, PinDirection.INPUT, node_id))
            node.inputs.append(NodePin("Position", PinType.VECTOR3, PinDirection.INPUT, node_id))
            node.outputs.append(NodePin("Exec", PinType.EXEC, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Node_GetPosition":
            node.inputs.append(NodePin("Node", PinType.NODE, PinDirection.INPUT, node_id))
            node.outputs.append(NodePin("Position", PinType.VECTOR3, PinDirection.OUTPUT, node_id))
        
        elif node_type == "Print":
            node.inputs.append(NodePin("Exec", PinType.EXEC, PinDirection.INPUT, node_id))
            node.inputs.append(NodePin("Message", PinType.STRING, PinDirection.INPUT, node_id, default_value=""))
            node.outputs.append(NodePin("Exec", PinType.EXEC, PinDirection.OUTPUT, node_id))
        
        return node
    
    def generate_python(self) -> str:
        """Generate Python code from the script.
        
        Returns:
            Generated Python code
        """
        code_lines = [
            "# Auto-generated from visual script",
            "from panda3d.core import Vec3",
            "from direct.showbase.ShowBase import ShowBase",
            "",
            "class GeneratedScript:",
            "    def __init__(self, base):",
            "        self.base = base",
            "        self.nodes = {}",
            ""
        ]
        
        # Find entry points (event nodes)
        for node in self.nodes.values():
            if node.node_type.startswith("Event_"):
                code_lines.extend(self._generate_event_handler(node))
        
        return "\n".join(code_lines)
    
    def _generate_event_handler(self, event_node: ScriptNode) -> List[str]:
        """Generate code for an event handler.
        
        Args:
            event_node: Event node
            
        Returns:
            Generated code lines
        """
        lines = []
        
        if event_node.node_type == "Event_BeginPlay":
            lines.append("    def begin_play(self):")
            # Follow execution chain
            exec_pin = next((p for p in event_node.outputs if p.name == "Exec"), None)
            if exec_pin and exec_pin.connected_to:
                lines.extend(self._generate_exec_chain(exec_pin.connected_to[0], indent=2))
            else:
                lines.append("        pass")
            lines.append("")
        
        elif event_node.node_type == "Event_Tick":
            lines.append("    def tick(self, dt):")
            exec_pin = next((p for p in event_node.outputs if p.name == "Exec"), None)
            if exec_pin and exec_pin.connected_to:
                lines.extend(self._generate_exec_chain(exec_pin.connected_to[0], indent=2))
            else:
                lines.append("        pass")
            lines.append("")
        
        return lines
    
    def _generate_exec_chain(self, pin_id: str, indent: int = 1) -> List[str]:
        """Generate code for execution chain.
        
        Args:
            pin_id: Starting pin ID
            indent: Indentation level
            
        Returns:
            Generated code lines
        """
        lines = []
        ind = "    " * indent
        
        node_id, pin_name = pin_id.split(':')
        node = self.nodes.get(node_id)
        
        if not node:
            return lines
        
        if node.node_type == "Print":
            msg_pin = next((p for p in node.inputs if p.name == "Message"), None)
            if msg_pin:
                msg = msg_pin.default_value or ""
                lines.append(f"{ind}print('{msg}')")
        
        elif node.node_type == "Node_SetPosition":
            lines.append(f"{ind}# Set node position")
        
        # Continue chain
        exec_out = next((p for p in node.outputs if p.pin_type == PinType.EXEC), None)
        if exec_out and exec_out.connected_to:
            lines.extend(self._generate_exec_chain(exec_out.connected_to[0], indent))
        
        return lines
    
    def save(self, filepath: str) -> bool:
        """Save script to JSON file.
        
        Args:
            filepath: File path
            
        Returns:
            True if successful
        """
        try:
            data = {
                'name': self.name,
                'nodes': [node.to_dict() for node in self.nodes.values()]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Script saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            return False
    
    def load(self, filepath: str) -> bool:
        """Load script from JSON file.
        
        Args:
            filepath: File path
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.name = data.get('name', 'LoadedScript')
            self.nodes.clear()
            
            for node_data in data.get('nodes', []):
                node = ScriptNode(
                    node_id=node_data['node_id'],
                    node_type=node_data['node_type'],
                    x=node_data['x'],
                    y=node_data['y'],
                    parameters=node_data.get('parameters', {})
                )
                
                # Reconstruct pins
                for pin_data in node_data.get('inputs', []):
                    pin = NodePin(
                        name=pin_data['name'],
                        pin_type=PinType(pin_data['type']),
                        direction=PinDirection(pin_data['direction']),
                        node_id=node.node_id,
                        connected_to=pin_data.get('connected_to', []),
                        default_value=pin_data.get('default_value')
                    )
                    node.inputs.append(pin)
                
                for pin_data in node_data.get('outputs', []):
                    pin = NodePin(
                        name=pin_data['name'],
                        pin_type=PinType(pin_data['type']),
                        direction=PinDirection(pin_data['direction']),
                        node_id=node.node_id,
                        connected_to=pin_data.get('connected_to', [])
                    )
                    node.outputs.append(pin)
                
                self.nodes[node.node_id] = node
            
            logger.info(f"Script loaded: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load script: {e}")
            return False


class NodeEditorUI:
    """Visual node editor UI using Tkinter."""
    
    def __init__(self, root: tk.Tk):
        """Initialize node editor UI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.script = VisualScript()
        
        # UI setup
        self.canvas = Canvas(root, bg='#2b2b2b', width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pan/zoom
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        
        # Node visuals
        self.node_visuals: Dict[str, int] = {}  # node_id -> canvas item ID
        
        # Toolbar
        self._create_toolbar()
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        
        logger.info("Node editor UI initialized")
    
    def _create_toolbar(self) -> None:
        """Create toolbar with node palette."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="Add Event", command=lambda: self.add_node_menu("Event")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Add Math", command=lambda: self.add_node_menu("Math")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Add Logic", command=lambda: self.add_node_menu("Logic")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Generate Code", command=self.generate_code).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Save", command=self.save_script).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Load", command=self.load_script).pack(side=tk.LEFT)
    
    def add_node_menu(self, category: str) -> None:
        """Show menu to add node.
        
        Args:
            category: Node category
        """
        # Simple implementation - just add a default node
        if category == "Event":
            self.add_node("Event_BeginPlay", 100, 100)
        elif category == "Math":
            self.add_node("Math_Add", 200, 100)
        elif category == "Logic":
            self.add_node("Logic_Branch", 300, 100)
    
    def add_node(self, node_type: str, x: float, y: float) -> None:
        """Add a node to the graph.
        
        Args:
            node_type: Type of node
            x: X position
            y: Y position
        """
        node = self.script.add_node(node_type, x, y)
        self._draw_node(node)
    
    def _draw_node(self, node: ScriptNode) -> None:
        """Draw a node on the canvas.
        
        Args:
            node: Node to draw
        """
        x, y = node.x, node.y
        width, height = 150, 80
        
        # Draw node box
        rect_id = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#404040', outline='#606060', width=2
        )
        
        # Draw title
        self.canvas.create_text(
            x + width/2, y + 15,
            text=node.node_type,
            fill='white', font=('Arial', 10, 'bold')
        )
        
        # Draw pins
        pin_y = y + 35
        for pin in node.inputs:
            self.canvas.create_oval(
                x - 5, pin_y - 5, x + 5, pin_y + 5,
                fill='#4CAF50', outline='white'
            )
            self.canvas.create_text(
                x + 10, pin_y,
                text=pin.name, fill='white', anchor='w', font=('Arial', 8)
            )
            pin_y += 15
        
        pin_y = y + 35
        for pin in node.outputs:
            self.canvas.create_oval(
                x + width - 5, pin_y - 5, x + width + 5, pin_y + 5,
                fill='#2196F3', outline='white'
            )
            self.canvas.create_text(
                x + width - 10, pin_y,
                text=pin.name, fill='white', anchor='e', font=('Arial', 8)
            )
            pin_y += 15
        
        self.node_visuals[node.node_id] = rect_id
    
    def on_canvas_click(self, event) -> None:
        """Handle canvas click."""
        pass
    
    def on_canvas_drag(self, event) -> None:
        """Handle canvas drag."""
        pass
    
    def generate_code(self) -> None:
        """Generate Python code from graph."""
        code = self.script.generate_python()
        
        # Show in dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Generated Code")
        
        text = tk.Text(dialog, width=80, height=30)
        text.pack()
        text.insert('1.0', code)
    
    def save_script(self) -> None:
        """Save script to file."""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(defaultextension=".json")
        if filepath:
            self.script.save(filepath)
    
    def load_script(self) -> None:
        """Load script from file."""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            self.script.load(filepath)
            self.refresh_canvas()
    
    def refresh_canvas(self) -> None:
        """Refresh canvas with current script."""
        self.canvas.delete("all")
        self.node_visuals.clear()
        
        for node in self.script.nodes.values():
            self._draw_node(node)
