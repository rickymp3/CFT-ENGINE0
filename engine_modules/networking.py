"""Networking layer for multiplayer games using asyncio.

Features:
- Client-server architecture
- Async message handling
- State synchronization
- Input prediction and reconciliation
- Lag compensation
- WebSocket support for cross-platform
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets not installed. Run: pip install websockets")

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Network message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    STATE_UPDATE = "state_update"
    INPUT = "input"
    SPAWN = "spawn"
    DESPAWN = "despawn"
    PING = "ping"
    PONG = "pong"
    CHAT = "chat"
    CUSTOM = "custom"


@dataclass
class NetworkMessage:
    """Network message structure."""
    type: MessageType
    timestamp: float
    data: Dict[str, Any]
    client_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            'type': self.type.value,
            'timestamp': self.timestamp,
            'data': self.data,
            'client_id': self.client_id
        })
    
    @staticmethod
    def from_json(json_str: str) -> 'NetworkMessage':
        """Parse from JSON string."""
        data = json.loads(json_str)
        return NetworkMessage(
            type=MessageType(data['type']),
            timestamp=data['timestamp'],
            data=data['data'],
            client_id=data.get('client_id')
        )


class NetworkClient:
    """Network client for multiplayer games."""
    
    def __init__(self, client_id: str):
        """Initialize network client.
        
        Args:
            client_id: Unique client identifier
        """
        self.client_id = client_id
        self.websocket: Optional[Any] = None
        self.connected = False
        self.server_url: Optional[str] = None
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        
        # State synchronization
        self.server_tick = 0
        self.client_tick = 0
        self.tick_rate = 20  # Hz
        self.tick_interval = 1.0 / self.tick_rate
        
        # Lag compensation
        self.rtt = 0.0  # Round-trip time in seconds
        self.last_ping_time = 0.0
        
        # Input buffer for prediction
        self.input_buffer: List[Dict] = []
        self.max_input_buffer = 60
        
        logger.info(f"Network client '{client_id}' initialized")
    
    async def connect(self, server_url: str) -> bool:
        """Connect to game server.
        
        Args:
            server_url: Server WebSocket URL (e.g., ws://localhost:8765)
            
        Returns:
            True if connected successfully
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets module not available")
            return False
        
        try:
            self.server_url = server_url
            self.websocket = await websockets.connect(server_url)
            self.connected = True
            
            # Send connect message
            await self.send_message(NetworkMessage(
                type=MessageType.CONNECT,
                timestamp=time.time(),
                data={'client_id': self.client_id},
                client_id=self.client_id
            ))
            
            logger.info(f"Connected to server: {server_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from server."""
        if self.websocket and self.connected:
            await self.send_message(NetworkMessage(
                type=MessageType.DISCONNECT,
                timestamp=time.time(),
                data={},
                client_id=self.client_id
            ))
            
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")
    
    async def send_message(self, message: NetworkMessage) -> None:
        """Send a message to the server.
        
        Args:
            message: Message to send
        """
        if not self.websocket or not self.connected:
            logger.warning("Cannot send message: not connected")
            return
        
        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_input(self, input_data: Dict[str, Any]) -> None:
        """Send player input to server.
        
        Args:
            input_data: Input state (keys, mouse, etc.)
        """
        # Add to input buffer for prediction
        self.input_buffer.append({
            'tick': self.client_tick,
            'data': input_data,
            'timestamp': time.time()
        })
        
        # Trim buffer
        if len(self.input_buffer) > self.max_input_buffer:
            self.input_buffer.pop(0)
        
        # Send to server
        await self.send_message(NetworkMessage(
            type=MessageType.INPUT,
            timestamp=time.time(),
            data={
                'tick': self.client_tick,
                'input': input_data
            },
            client_id=self.client_id
        ))
    
    async def send_state_update(self, state: Dict[str, Any]) -> None:
        """Send state update to server.
        
        Args:
            state: Game state data
        """
        await self.send_message(NetworkMessage(
            type=MessageType.STATE_UPDATE,
            timestamp=time.time(),
            data=state,
            client_id=self.client_id
        ))
    
    async def receive_loop(self) -> None:
        """Main receive loop for processing server messages."""
        if not self.websocket or not self.connected:
            return
        
        try:
            async for message_str in self.websocket:
                message = NetworkMessage.from_json(message_str)
                await self._handle_message(message)
                
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            self.connected = False
    
    async def _handle_message(self, message: NetworkMessage) -> None:
        """Handle incoming message.
        
        Args:
            message: Received message
        """
        # Update server tick
        if 'server_tick' in message.data:
            self.server_tick = message.data['server_tick']
        
        # Handle ping/pong
        if message.type == MessageType.PING:
            await self.send_message(NetworkMessage(
                type=MessageType.PONG,
                timestamp=time.time(),
                data={'ping_timestamp': message.timestamp},
                client_id=self.client_id
            ))
        elif message.type == MessageType.PONG:
            self.rtt = time.time() - message.data['ping_timestamp']
        
        # Call registered handlers
        if message.type in self.message_handlers:
            for handler in self.message_handlers[message.type]:
                handler(message.data)
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function
        """
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Handler registered for {message_type.value}")
    
    async def update(self, dt: float) -> None:
        """Update network client.
        
        Args:
            dt: Delta time
        """
        self.client_tick += 1
        
        # Send periodic ping
        if time.time() - self.last_ping_time > 1.0:
            if self.connected:
                await self.send_message(NetworkMessage(
                    type=MessageType.PING,
                    timestamp=time.time(),
                    data={},
                    client_id=self.client_id
                ))
                self.last_ping_time = time.time()


class NetworkServer:
    """Network server for multiplayer games."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize network server.
        
        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.clients: Dict[str, Any] = {}  # client_id -> websocket
        self.running = False
        
        # Server tick
        self.tick = 0
        self.tick_rate = 20  # Hz
        self.tick_interval = 1.0 / self.tick_rate
        
        # Game state
        self.game_state: Dict[str, Any] = {}
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        
        logger.info(f"Network server initialized on {host}:{port}")
    
    async def start(self) -> None:
        """Start the server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets module not available")
            return
        
        self.running = True
        
        async with websockets.serve(self._handle_client, self.host, self.port):
            logger.info(f"Server listening on ws://{self.host}:{self.port}")
            await self._game_loop()
    
    async def _handle_client(self, websocket, path) -> None:
        """Handle new client connection.
        
        Args:
            websocket: Client websocket
            path: Connection path
        """
        client_id = None
        
        try:
            async for message_str in websocket:
                message = NetworkMessage.from_json(message_str)
                
                # Handle connection
                if message.type == MessageType.CONNECT:
                    client_id = message.data.get('client_id')
                    self.clients[client_id] = websocket
                    logger.info(f"Client connected: {client_id}")
                    
                    # Notify other clients
                    await self.broadcast(NetworkMessage(
                        type=MessageType.SPAWN,
                        timestamp=time.time(),
                        data={'client_id': client_id}
                    ), exclude=client_id)
                
                # Handle other messages
                elif client_id:
                    await self._handle_message(message, client_id)
        
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        
        finally:
            # Client disconnected
            if client_id and client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Client disconnected: {client_id}")
                
                await self.broadcast(NetworkMessage(
                    type=MessageType.DESPAWN,
                    timestamp=time.time(),
                    data={'client_id': client_id}
                ))
    
    async def _handle_message(self, message: NetworkMessage, client_id: str) -> None:
        """Handle client message.
        
        Args:
            message: Received message
            client_id: Sending client
        """
        message.client_id = client_id
        
        # Call registered handlers
        if message.type in self.message_handlers:
            for handler in self.message_handlers[message.type]:
                handler(message)
        
        # Echo state updates to all clients
        if message.type == MessageType.STATE_UPDATE:
            await self.broadcast(message)
    
    async def broadcast(self, message: NetworkMessage, exclude: Optional[str] = None) -> None:
        """Broadcast message to all clients.
        
        Args:
            message: Message to broadcast
            exclude: Client ID to exclude
        """
        # Add server tick
        message.data['server_tick'] = self.tick
        
        for client_id, websocket in list(self.clients.items()):
            if client_id != exclude:
                try:
                    await websocket.send(message.to_json())
                except Exception as e:
                    logger.error(f"Failed to send to {client_id}: {e}")
    
    async def send_to_client(self, client_id: str, message: NetworkMessage) -> None:
        """Send message to specific client.
        
        Args:
            client_id: Target client
            message: Message to send
        """
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send to {client_id}: {e}")
    
    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function
        """
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Handler registered for {message_type.value}")
    
    async def _game_loop(self) -> None:
        """Main server game loop."""
        last_tick = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_tick
            
            if dt >= self.tick_interval:
                self.tick += 1
                await self._tick()
                last_tick = current_time
            
            await asyncio.sleep(0.001)  # Small sleep to prevent CPU spinning
    
    async def _tick(self) -> None:
        """Process one server tick."""
        # Update game state
        # Broadcast state to clients
        await self.broadcast(NetworkMessage(
            type=MessageType.STATE_UPDATE,
            timestamp=time.time(),
            data=self.game_state
        ))
    
    def stop(self) -> None:
        """Stop the server."""
        self.running = False
        logger.info("Server stopped")


# Utility functions

def interpolate_state(state1: Dict, state2: Dict, t: float) -> Dict:
    """Interpolate between two states.
    
    Args:
        state1: First state
        state2: Second state
        t: Interpolation factor (0-1)
        
    Returns:
        Interpolated state
    """
    result = {}
    
    for key in state1:
        if key in state2:
            val1 = state1[key]
            val2 = state2[key]
            
            # Numeric interpolation
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                result[key] = val1 * (1 - t) + val2 * t
            else:
                result[key] = val2 if t > 0.5 else val1
    
    return result
