import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Upgrades websocket connection
        Sends initial messages (login and register to events)
        Adds websocket to active connections list

        Args:
            websocket (WebSocket): the websocket connection
        """
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "Cmd": "Login",
                    "MT": "Req",
                    "TID": 1000,
                    "Data": {
                        "User": "system",
                        "Password": "R0FU",
                        "OnlineDecision": True,
                        "Info": "GAT Relaxx - V3.3.1",
                    },
                }
            )
        )
        await websocket.send_text(
            json.dumps(
                {
                    "Cmd": "RegisterEvent",
                    "MT": "Req",
                    "TID": 2000,
                    "Data": {"Event": "App.*"},
                }
            )
        )
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to websocket clients: {e}")
                print("Message: ", message)
                self.active_connections.remove(connection)


connection_manager = ConnectionManager()
