# src/main.py

import os
import asyncio
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from crew_runner import run_lead_flow

app = FastAPI()

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
