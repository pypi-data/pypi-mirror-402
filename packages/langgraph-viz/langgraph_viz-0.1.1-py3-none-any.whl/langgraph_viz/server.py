"""WebSocket server for streaming visualization updates."""

import os
import json
import asyncio
import threading
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .state_tracker import StateTracker, StateSnapshot


class VisualizerServer:
    """FastAPI + WebSocket server for real-time state updates."""

    def __init__(self, app, port: int, state_tracker: StateTracker):
        """
        Initialize the visualizer server.
        
        Args:
            app: Compiled LangGraph app
            port: Port to run server on
            state_tracker: StateTracker instance to subscribe to
        """
        self.app = app
        self.port = port
        self.state_tracker = state_tracker
        self.fastapi_app = FastAPI(title="LangGraph Visualizer")
        self.connections: List[WebSocket] = []
        self.server_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Subscribe to state updates
        self.state_tracker.subscribe(self._on_state_update)
        
        # Setup routes
        self._setup_routes()

    def _get_graph_def(self) -> dict:
        """Extract graph definition from the app."""
        try:
            graph = self.app.get_graph(xray=True)
            nodes = []
            for node in graph.nodes:
                nodes.append({"id": str(node), "type": "node"})
            
            edges = []
            for edge in graph.edges:
                edges.append({
                    "source": str(edge.source),
                    "target": str(edge.target),
                    "type": "edge"
                })
                
            return {
                "nodes": nodes,
                "edges": edges
            }
        except Exception as e:
            print(f"Error extracting graph definition: {e}")
            return {"nodes": [], "edges": []}

    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.fastapi_app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.connections.append(websocket)
            
            try:
                # Send graph definition first
                await websocket.send_json({
                    "type": "graph_def",
                    "data": self._get_graph_def()
                })

                # Send initial history
                await websocket.send_json({
                    "type": "history",
                    "data": self.state_tracker.get_history(),
                })
                
                # Keep connection alive
                while True:
                    # Wait for ping or disconnect
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.connections.remove(websocket)
            except Exception as e:
                print(f"WebSocket error: {e}")
                if websocket in self.connections:
                    self.connections.remove(websocket)

        @self.fastapi_app.get("/api/history")
        async def get_history():
            """REST endpoint to get full execution history."""
            return {"history": self.state_tracker.get_history()}
            
        @self.fastapi_app.get("/api/graph")
        async def get_graph():
            """REST endpoint to get graph definition."""
            return self._get_graph_def()

        @self.fastapi_app.get("/api/health")
        async def health():
            """Health check endpoint."""
            return {"status": "ok", "connections": len(self.connections)}

        # Serve React UI
        ui_dir = Path(__file__).parent / "ui"
        if ui_dir.exists():
            # Serve static assets with cache control
            from fastapi.responses import FileResponse
            
            @self.fastapi_app.get("/assets/{path:path}")
            async def serve_assets(path: str):
                """Serve static assets."""
                file_path = ui_dir / "assets" / path
                if file_path.exists():
                    return FileResponse(
                        file_path,
                        headers={
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0"
                        }
                    )
                return HTMLResponse("Not found", status_code=404)
            
            # Serve index.html for all other routes
            @self.fastapi_app.get("/{full_path:path}")
            async def serve_ui(full_path: str):
                """Serve the React UI."""
                index_path = ui_dir / "index.html"
                if index_path.exists():
                    return HTMLResponse(
                        index_path.read_text(),
                        headers={
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0"
                        }
                    )
                return HTMLResponse("<h1>UI not built yet. Run: cd frontend && npm run build</h1>")
        else:
            @self.fastapi_app.get("/")
            async def root():
                """Serve fallback if UI not built."""
                return HTMLResponse(self._get_placeholder_html())

    def _get_placeholder_html(self) -> str:
        """Get placeholder HTML until React build is ready."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>LangGraph Visualizer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #1e1e1e;
            color: #e0e0e0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #4CAF50;
        }
        .event {
            background: #2d2d2d;
            border-left: 3px solid #4CAF50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .node {
            color: #64B5F6;
            font-weight: bold;
        }
        .timestamp {
            color: #888;
            font-size: 0.9em;
        }
        pre {
            background: #1a1a1a;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        .status {
            padding: 10px;
            background: #2d2d2d;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .connected {
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 LangGraph Visualizer</h1>
        <div class="status">
            Status: <span id="status" class="connected">Connecting...</span>
        </div>
        <div id="events"></div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const eventsDiv = document.getElementById('events');
        const statusSpan = document.getElementById('status');
        
        ws.onopen = () => {
            statusSpan.textContent = 'Connected';
            statusSpan.className = 'connected';
        };
        
        ws.onclose = () => {
            statusSpan.textContent = 'Disconnected';
            statusSpan.style.color = '#f44336';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'history') {
                // Display initial history
                data.data.forEach(snapshot => displayEvent(snapshot));
            } else if (data.type === 'update') {
                // Display new update
                displayEvent(data.data);
            }
        };
        
        function displayEvent(snapshot) {
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event';
            
            const timestamp = new Date(snapshot.timestamp * 1000).toLocaleTimeString();
            
            eventDiv.innerHTML = `
                <div class="node">Node: ${snapshot.node}</div>
                <div class="timestamp">${timestamp}</div>
                <pre>${JSON.stringify(snapshot.state, null, 2)}</pre>
                ${snapshot.diff ? `<details><summary>Diff</summary><pre>${JSON.stringify(snapshot.diff, null, 2)}</pre></details>` : ''}
            `;
            
            eventsDiv.appendChild(eventDiv);
            eventDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Send ping every 30 seconds to keep connection alive
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    </script>
</body>
</html>
"""

    def _on_state_update(self, snapshot: StateSnapshot):
        """
        Handle state updates from StateTracker.
        
        Args:
            snapshot: New state snapshot
        """
        if not self.connections:
            return
        
        # Schedule broadcast in the event loop
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._broadcast(snapshot),
                self.loop
            )

    async def _broadcast(self, snapshot: StateSnapshot):
        """
        Broadcast update to all connected clients.
        
        Args:
            snapshot: State snapshot to broadcast
        """
        message = {
            "type": "update",
            "data": {
                "timestamp": snapshot.timestamp,
                "node": snapshot.node,
                "state": snapshot.state,
                "diff": snapshot.diff,
                "event_type": snapshot.event_type,
            },
        }
        
        # Send to all connections
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            if ws in self.connections:
                self.connections.remove(ws)

    def start(self):
        """Start the server in a background thread."""
        def run_server():
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Run uvicorn
            config = uvicorn.Config(
                self.fastapi_app,
                host="127.0.0.1",
                port=self.port,
                log_level="warning",
                loop="asyncio",
            )
            server = uvicorn.Server(config)
            self.loop.run_until_complete(server.serve())
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait a bit for server to start
        import time
        time.sleep(1.5)

    def stop(self):
        """Stop the server."""
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
