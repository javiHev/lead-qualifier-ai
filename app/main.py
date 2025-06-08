import uvicorn
import logging
import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.config import settings
from app.models import (
    ChatStreamRequest,
    ChatFinishRequest,
    ChatFinishResponse
)
from app.services.openai_service import OpenAIService, stream_chat
from app.services.crewai_service import CrewaiService
from app.utils.streaming_utils import sse_response_generator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chatbot API con Streaming y Crewai → Airtable",
    version="1.0.0",
    description=(
        "Backend que utiliza la API de Asistentes de OpenAI (streaming SSE), "
        "CrewAI y Airtable."
    )
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
    try:
        # 1) Construir el texto completo de la conversación
        full_conv = "\n".join(
            f"{'USER' if m.role == 'user' else 'ASSISTANT'}: {m.content}"
            for m in request.messages
        )
        logger.info(f"Full conversation:\n{full_conv}")

        # 2) Extraer datos estructurados del lead
        try:
            extracted_data = await OpenAIService.extract_lead_data(full_conv)
            logger.info(f"Extracted data: {extracted_data}")
        except Exception as e:
            logger.exception("Error extrayendo datos del lead")
            raise HTTPException(
                status_code=500,
                detail=f"Error extrayendo datos del lead: {e}"
            )

        # 3) Ejecutar CrewAI y obtener CrewaiResult directamente
        try:
            crewai_result = CrewaiService.run_lead_scoring(
                form_response=full_conv,
                additional_info=extracted_data
            )
            logger.info(f"CrewAI result: {crewai_result}")
        except HTTPException:
            # Re-lanzar HTTPException para respetar código y detalle
            raise
        except Exception as e:
            logger.exception("Error en Crewai")
            raise HTTPException(
                status_code=500,
                detail=f"Error en Crewai: {e}"
            )

        # 4) Generar resumen/insights con OpenAI
        try:
            summary_text = await OpenAIService.summarize_conversation(
                request.messages,
                assistant_id=settings.openai_assistant_id
            )
            logger.info(f"Summary text: {summary_text}")
        except Exception as e:
            logger.exception("Error al resumir conversación")
            raise HTTPException(
                status_code=500,
                detail=f"Error al resumir conversación: {e}"
            )

        # 5) Guardar resultado en JSON
        try:
            # Convertir Pydantic model a dict
            try:
                result_dict = crewai_result.model_dump()  # Pydantic v2
            except AttributeError:
                result_dict = crewai_result.dict()       # Pydantic v1

            output_data = {
                "user_id": request.user_id or "unknown",
                "session_id": request.session_id or "unknown",
                "crewai_data": result_dict,
                "summary": summary_text,
                "conversation": full_conv,
                "timestamp": datetime.now().isoformat()
            }

            os.makedirs("data", exist_ok=True)
            filename = f"data/lead_{request.session_id}_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Datos guardados en: {filename}")

        except Exception as e:
            logger.exception("Error al guardar datos en JSON")
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar datos: {e}"
            )

        # 6) Responder satisfactoriamente
        return ChatFinishResponse(
            success=True,
            crewai_result=crewai_result,
            summary=summary_text,
            message="Lead procesado y almacenado correctamente en JSON.",
            airtable_record_id=None  # o el ID que devuelva AirtableService si lo integras
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error inesperado en /chat/finish")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {e}"
        )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
