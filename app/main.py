# app/main.py

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import ChatStreamRequest, ChatFinishRequest, ChatFinishResponse
from app.services.openai_service import OpenAIService, stream_chat
from app.services.crewai_service import CrewaiService
from app.services.airtable_service import AirtableService
from app.utils.streaming_utils import sse_response_generator

app = FastAPI(
    title="Chatbot API con Streaming y Crewai → Airtable",
    version="1.0.0",
    description="Backend que utiliza la API de Asistentes de OpenAI (streaming SSE), "
                "Crewai y Airtable."
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    if not request.messages or len(request.messages) < 1:
        raise HTTPException(status_code=400, detail="La conversación debe incluir al menos 1 mensaje.")

    async def event_generator():
        # Llamamos a nuestro stream_chat, que internamente crea thread, mensajes y run
        async for chunk in stream_chat(
            request.messages,
            assistant_id=settings.openai_assistant_id
        ):
            yield chunk

    return StreamingResponse(
        sse_response_generator(event_generator()),
        media_type="text/event-stream",
    )


@app.post("/chat/finish", response_model=ChatFinishResponse)
async def chat_finish(request: ChatFinishRequest):
    # 1) Concatenar conversación
    full_conv = ""
    for msg in request.messages:
        prefix = "USER: " if msg.role == "user" else "ASSISTANT: "
        full_conv += f"{prefix}{msg.content}\n"
    form_response = full_conv

    # 2) Ejecutar Crewai
    try:
        crewai_result = CrewaiService.run_lead_scoring(form_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Crewai: {e}")

    # 3) Generar resumen/insights con Assistants API
    try:
        summary_text = await OpenAIService.summarize_conversation(
            request.messages,
            assistant_id=settings.openai_assistant_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al resumir conversación: {e}")

    # 4) Insertar en Airtable
    try:
        fields = AirtableService.build_lead_fields(
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            crewai_data=crewai_result.dict(),
            summary=summary_text,
            conversation=full_conv
        )
        record_id = AirtableService.create_record(fields)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en Airtable: {e}")

    return ChatFinishResponse(
        success=True,
        airtable_record_id=record_id,
        crewai_result=crewai_result,
        summary=summary_text,
        message="Lead procesado y almacenado correctamente en Airtable."
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
