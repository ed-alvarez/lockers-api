from typing import Dict
from uuid import UUID

from fastapi import WebSocket

active_connections: Dict[UUID, WebSocket] = {}
