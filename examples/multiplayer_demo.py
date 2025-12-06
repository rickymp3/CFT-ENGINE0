"""Networking Multiplayer Demo - showcases asyncio networking.

Demonstrates:
- Client-server architecture
- State synchronization
- Input handling
- Player spawning/despawning
- Lag compensation with ping/pong
"""
import asyncio
import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, Point3
from engine_modules.networking import NetworkClient, NetworkServer, MessageType

class MultiplayerDemo(ShowBase):
    """Demo showcasing multiplayer networking."""
    
    def __init__(self, mode="client", server_url="ws://localhost:8765"):
        ShowBase.__init__(self)
        
        self.mode = mode
        self.players = {}  # client_id -> NodePath
        
        # Setup camera
        self.camera.setPos(0, -20, 10)
        self.camera.lookAt(0, 0, 0)
        
        # Create ground
        self.ground = self.loader.loadModel("models/box")
        self.ground.setScale(50, 50, 0.1)
        self.ground.setPos(0, 0, -0.1)
        self.ground.reparentTo(self.render)
        
        # Initialize networking
        if mode == "server":
            self.server = NetworkServer(host="localhost", port=8765)
            self.setup_server()
            print("Server mode - waiting for clients on port 8765")
        else:
            self.client = NetworkClient(client_id=f"player_{id(self)}")
            self.setup_client(server_url)
            print(f"Client mode - connecting to {server_url}")
        
        # Controls
        self.accept("escape", sys.exit)
        self.accept("w", self.move_forward)
        self.accept("s", self.move_backward)
        self.accept("a", self.move_left)
        self.accept("d", self.move_right)
        
        # Update task
        self.taskMgr.add(self.update, "update")
        
        print("Multiplayer Demo")
        print("Controls:")
        print("  WASD - Move")
        print("  ESC - Exit")
    
    def setup_server(self):
        """Setup server handlers."""
        # Register message handlers
        self.server.register_handler(MessageType.INPUT, self.on_server_input)
        
        # Start server in background
        asyncio.create_task(self.server.start())
    
    def setup_client(self, server_url):
        """Setup client handlers."""
        # Register message handlers
        self.client.register_handler(MessageType.STATE_UPDATE, self.on_state_update)
        self.client.register_handler(MessageType.SPAWN, self.on_player_spawn)
        self.client.register_handler(MessageType.DESPAWN, self.on_player_despawn)
        
        # Connect to server
        asyncio.create_task(self.connect_client(server_url))
    
    async def connect_client(self, server_url):
        """Connect client to server."""
        await self.client.connect(server_url)
        
        # Start receive loop
        asyncio.create_task(self.client.receive_loop())
        
        # Spawn local player
        self.spawn_player(self.client.client_id, is_local=True)
    
    def spawn_player(self, client_id, is_local=False):
        """Spawn a player entity."""
        if client_id in self.players:
            return
        
        # Create player model (simple box)
        player = self.loader.loadModel("models/box")
        player.setScale(1, 1, 2)
        player.setPos(0, 0, 1)
        player.reparentTo(self.render)
        
        # Color based on client
        if is_local:
            player.setColor(0, 1, 0, 1)  # Green for local player
        else:
            player.setColor(1, 0, 0, 1)  # Red for remote players
        
        self.players[client_id] = player
        print(f"Player spawned: {client_id}")
    
    def on_player_spawn(self, data):
        """Handle player spawn message."""
        client_id = data.get('client_id')
        if client_id and client_id != self.client.client_id:
            self.spawn_player(client_id, is_local=False)
    
    def on_player_despawn(self, data):
        """Handle player despawn message."""
        client_id = data.get('client_id')
        if client_id in self.players:
            self.players[client_id].removeNode()
            del self.players[client_id]
            print(f"Player despawned: {client_id}")
    
    def on_state_update(self, data):
        """Handle state update from server."""
        # Update remote players
        for client_id, state in data.items():
            if client_id != self.client.client_id and client_id in self.players:
                pos = state.get('position', [0, 0, 0])
                self.players[client_id].setPos(*pos)
    
    def on_server_input(self, message):
        """Handle input from client (server-side)."""
        client_id = message.client_id
        input_data = message.data.get('input', {})
        
        # Process input and update player position
        # (simplified - real game would use physics)
        # Broadcast updated state to all clients
    
    def move_forward(self):
        """Move player forward."""
        if self.mode == "client":
            asyncio.create_task(self.client.send_input({'move': 'forward'}))
            # Client-side prediction
            if self.client.client_id in self.players:
                pos = self.players[self.client.client_id].getPos()
                self.players[self.client.client_id].setPos(pos + Vec3(0, 1, 0))
    
    def move_backward(self):
        """Move player backward."""
        if self.mode == "client":
            asyncio.create_task(self.client.send_input({'move': 'backward'}))
            if self.client.client_id in self.players:
                pos = self.players[self.client.client_id].getPos()
                self.players[self.client.client_id].setPos(pos + Vec3(0, -1, 0))
    
    def move_left(self):
        """Move player left."""
        if self.mode == "client":
            asyncio.create_task(self.client.send_input({'move': 'left'}))
            if self.client.client_id in self.players:
                pos = self.players[self.client.client_id].getPos()
                self.players[self.client.client_id].setPos(pos + Vec3(-1, 0, 0))
    
    def move_right(self):
        """Move player right."""
        if self.mode == "client":
            asyncio.create_task(self.client.send_input({'move': 'right'}))
            if self.client.client_id in self.players:
                pos = self.players[self.client.client_id].getPos()
                self.players[self.client.client_id].setPos(pos + Vec3(1, 0, 0))
    
    def update(self, task):
        """Update game state."""
        dt = globalClock.getDt()
        
        if self.mode == "client":
            asyncio.create_task(self.client.update(dt))
        
        return task.cont


if __name__ == "__main__":
    # Check command line args
    mode = "client"
    server_url = "ws://localhost:8765"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            mode = "server"
        elif sys.argv[1].startswith("ws://"):
            server_url = sys.argv[1]
    
    demo = MultiplayerDemo(mode=mode, server_url=server_url)
    demo.run()
