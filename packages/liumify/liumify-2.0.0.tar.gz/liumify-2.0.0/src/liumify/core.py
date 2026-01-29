# (c) 2026 Liumi Corporation. All Rights Reserved. Private & Proprietary.

import uvicorn
import webbrowser
import asyncio
import json
from typing import List
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .components import LiumifyComponent

class LiumifyApp:
    """
    The Liumify Application Controller.
    Orchestrates the connection between Python logic and the Liumify HD Rendering Core.
    """
    def __init__(self, app_name: str = "Liumi Application"):
        self.app_name = app_name
        self._components: List[LiumifyComponent] = []
        self._server = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        self._setup_internal_routes()
        
    def add(self, component: LiumifyComponent):
        """Adds an element to the Liumify Scene Graph."""
        self._components.append(component)

    def _get_scene_state(self):
        return {
            "meta": {"app_name": self.app_name},
            "scene": [c.serialize() for c in self._components]
        }

    def _setup_internal_routes(self):
        base_dir = Path(__file__).resolve().parent
        templates = Jinja2Templates(directory=str(base_dir / "templates"))

        @self._server.get("/", response_class=HTMLResponse)
        async def render_shell(request: Request):
            """Serves the secure, proprietary rendering shell."""
            return templates.TemplateResponse("engine.html", {
                "request": request,
                "app_title": self.app_name
            })

        @self._server.websocket("/ws/link")
        async def websocket_endpoint(websocket: WebSocket):
            """Real-time bi-directional link to the Fluid Visual Engine."""
            await websocket.accept()
            # Send initial scene state
            await websocket.send_text(json.dumps({
                "type": "INIT_SCENE",
                "payload": self._get_scene_state()
            }))
            
            # Keep alive & listen for interactions
            try:
                while True:
                    data = await websocket.receive_text()
                    # Future: Handle UI callbacks here
                    pass
            except Exception:
                pass

    def launch(self, host: str = "127.0.0.1", port: int = 8080, browser: bool = True):
        """
        Boots the Liumify Server and opens the HD Viewport.
        """
        print(f"[*] Liumi Corporation - Liumify v2.0.0-gold")
        print(f"[*] initializing HD Rendering Core on {host}:{port}...")
        
        if browser:
            def open_client():
                import time
                time.sleep(1.0)
                webbrowser.open(f"http://{host}:{port}")
            import threading
            threading.Thread(target=open_client, daemon=True).start()

        uvicorn.run(self._server, host=host, port=port, log_level="critical")