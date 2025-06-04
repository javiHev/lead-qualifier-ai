# src/main.py

import os
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

from crew_runner import run_lead_flow

app = FastAPI()


class ConnectionManager:
    """Manage multiple WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in list(self.active_connections):
            await connection.send_text(message)


manager = ConnectionManager()


async def run_conversation(message: str) -> str:
    """Stub conversation logic used by the WebSocket endpoint."""
    # In a real implementation this would call an agent or model.
    await asyncio.sleep(0.1)
    return f"Echo: {message}"

# Permitir CORS (para que el iframe pueda hacer fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, limita al dominio de tu front
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Manejamos un único "lead" por conversación_id.
# Para un MVP simple, no guardamos histórico en memoria, arrancamos el flujo desde cero.
@app.post("/chat")
async def chat_endpoint(req: Request):
    """
    Espera un JSON: { "conversation_id": "algunID", "message": "texto del usuario" }
    Para este MVP, ignoramos el mensaje y arrancamos todo el flujo
    de conversación -> cualificación -> airtable (si corresponde).
    """
    payload = await req.json()
    lead_name = payload.get("lead_name", "SinNombre")
    company = payload.get("company", "SinEmpresa")

    # Ejecutar todo el flujo de CrewAI (sin streaming SSE en este MVP).
    result = await run_lead_flow(lead_name, company)

    # result contendrá un dict con:
    # - conversation_task output
    # - qualification_task output
    # - airtable_registration_task output (si score >= 6) o None
    return {"result": result}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response = await run_conversation(data)
            await manager.send_personal_message(response, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
