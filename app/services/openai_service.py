# app/services/openai_service.py

import asyncio
import json
from typing import List, AsyncGenerator, Dict, Any

import openai
from openai import OpenAI, AssistantEventHandler

from app.models import ChatMessage
from app.config import settings

# 1) Configurar la clave para ChatCompletion (gpt-3.5-turbo) y para Assistants API
openai.api_key = settings.openai_api_key
client = OpenAI(api_key=settings.openai_api_key)


class _StreamHandler(AssistantEventHandler):
    """
    Handler para capturar los eventos de texto en streaming de la Assistants API.
    Cada vez que llega un fragmento de texto (textDelta), lo ponemos en la cola.
    """

    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self._queue = queue

    def on_text_delta(self, delta, snapshot):
        """
        Se llama cada vez que llega un fragmento de texto.
        `delta.value` contiene la parte nueva de texto del assistant.
        """
        self._queue.put_nowait(delta.value)

    def on_text_created(self, text):
        """
        Se llama cuando comienza un bloque de texto. A veces incluye rol,
        pero aquí lo ignoramos porque asumimos siempre rol "assistant".
        """
        pass


async def stream_chat(
    messages: List[ChatMessage],
    assistant_id: str = settings.openai_assistant_id,
    temperature: float = 0.7,
) -> AsyncGenerator[dict, None]:
    """
    Llama a la Assistants API en modo streaming y devuelve un AsyncGenerator
    que emite {'role': 'assistant', 'delta': 'fragmento_de_texto'}.
    """

    # 1) Creamos un asyncio.Queue para comunicar el thread de streaming con este async generator
    queue: asyncio.Queue = asyncio.Queue()

    # 2) Construir el array de mensajes históricos (sin incluir 'system')
    user_and_assistant_msgs = [
        {"role": m.role, "content": m.content} for m in messages
    ]

    # 3) Función síncrona que crea Thread + Mensajes + Run en streaming
    def _run_stream():
        # 3.1) Crear un nuevo Thread para esta conversación
        thread = client.beta.threads.create()

        # 3.2) Añadir al Thread todos los mensajes previos de la conversación
        for m in user_and_assistant_msgs:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role=m["role"],
                content=m["content"]
            )

        # 3.3) Instanciar el handler que pone cada delta en la cola
        handler = _StreamHandler(queue)

        # 3.4) Ejecutar el Asistente en streaming. Pasamos system_prompt como instructions.
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=settings.system_prompt,
            temperature=temperature,
            event_handler=handler
        ) as stream_obj:
            stream_obj.until_done()

        # 3.5) Cuando el streaming termina, ponemos un sentinel `None` para cerrar el generator
        queue.put_nowait(None)

    # 4) Ejecutamos `_run_stream` en un ThreadPoolExecutor para no bloquear el event loop
    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=1)
    loop.run_in_executor(executor, _run_stream)

    # 5) Ahora, en este coroutine, vamos sacando de la cola cada fragmento y yield
    while True:
        item = await queue.get()
        if item is None:
            # Llegó el sentinel: streaming completado
            break
        yield {"role": "assistant", "delta": item}


async def summarize_conversation(
    messages: List[ChatMessage],
    assistant_id: str = settings.openai_assistant_id,
    temperature: float = 0.2,
    max_tokens: int = 1000,
) -> str:
    """
    Genera un resumen de toda la conversación usando la Assistants API en modo no‐streaming.
    Devuelve el texto completo de la respuesta.
    """

    # 1) Construir el “prompt” sacando transcript de mensajes
    transcript = ""
    for msg in messages:
        prefix = "Usuario:" if msg.role == "user" else "Asistente:"
        transcript += f"{prefix} {msg.content}\n"

    prompt = (
        "Por favor, resume esta conversación enfocándote en los insights clave "
        "sobre el lead (motivaciones, necesidades, objeciones, datos de contacto, etc.).\n\n"
        + transcript
        + "\n\nResumen:"
    )

    # 2) Para no‐streaming, usamos el helper runs.create
    def _run_summarize():
        resp = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content":"Eres un experto resumiendo conversaciones donde es importante captar los insights clave sobre el lead (motivaciones, necesidades, objeciones, datos de contacto, etc.)."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return resp.choices[0].message.content.strip()
    # 3) Ejecutar en executor para no bloquear el event loop
    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=1)
    summary = await loop.run_in_executor(executor, _run_summarize)
    return summary


async def extract_lead_data(
    full_conversation: str,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.0,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    """
    Extrae datos estructurados (nombre, empresa, necesidad, presupuesto, urgencia, tono)
    de la conversación completa usando openai.ChatCompletion.create con gpt-3.5-turbo.
    Devuelve un dict con esas claves.
    """

    # 1) Construir el prompt instructivo para extraer JSON
    extraction_prompt = f"""
Extrae los siguientes datos del lead basándote en esta conversación. Devuelve únicamente un JSON:

- Nombre del lead (si se menciona; sino "" )
- Empresa (si se menciona; sino "" )
- Necesidad expresada por el lead
- Presupuesto estimado (por ejemplo: "5000€", o vacío "")
- Urgencia ("alta", "media", "baja", o "")
- Tono de la conversación ("positivo", "dudoso", "negativo", o "")

Conversación:
\"\"\"
{full_conversation}
\"\"\"

JSON con claves: nombre, empresa, necesidad, presupuesto, urgencia, tono.
"""
    # 2) Llamada síncrona en executor para no bloquear
    def _run_extract():
        resp = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": settings.prompt_extract_info},
                {"role": "user",   "content": extraction_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        text = resp.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Si el texto no es JSON válido, devolvemos todo como necesidad y vacíos los demás campos
            return {
                "nombre": "",
                "empresa": "",
                "necesidad": text,
                "presupuesto": "",
                "urgencia": "",
                "tono": ""
            }

    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=1)
    result = await loop.run_in_executor(executor, _run_extract)
    return result


# ——————————————————————————
# Clase wrapper para exponer métodos a Main
# ——————————————————————————
class OpenAIService:
    """
    Wrapper que expone métodos de extracción, resumen y streaming.
    """

    @staticmethod
    async def summarize_conversation(
        messages: List[ChatMessage],
        assistant_id: str = settings.openai_assistant_id,
        temperature: float = 0.3,
        max_tokens: int = 300,
    ) -> str:
        return await summarize_conversation(
            messages, assistant_id=assistant_id, temperature=temperature, max_tokens=max_tokens
        )

    @staticmethod
    async def extract_lead_data(
        full_conversation: str,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        return await extract_lead_data(full_conversation, model=model, temperature=temperature)
