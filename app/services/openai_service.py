import asyncio
from typing import List, AsyncGenerator
from openai import OpenAI, AssistantEventHandler
from app.models import ChatMessage
from app.config import settings

# Instanciamos el cliente OpenAI (>=1.51.2) para usar Assistants API (beta/v2)
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
    # max_tokens ya no se pasa a runs.stream()
) -> AsyncGenerator[dict, None]:
    """
    Llama a la Assistants API en modo streaming y devuelve un AsyncGenerator
    que emite {'role': 'assistant', 'delta': 'fragmento_de_texto'}.
    """

    # 1) Creamos un asyncio.Queue para comunicar el thread de streaming con este async generator
    queue: asyncio.Queue = asyncio.Queue()

    # 2) Construir el array de mensajes sin incluir 'system'
    #    (El system_prompt se pasará como 'instructions' en el run)
    user_and_assistant_msgs = []
    for m in messages:
        # Solo roles válidos para messages: 'user' o 'assistant'
        user_and_assistant_msgs.append({"role": m.role, "content": m.content})

    # 3) Función síncrona que crea Thread + Mensajes + Run en streaming
    def _run_stream():
        # 3.1) Crear un nuevo Thread para esta conversación
        thread = client.beta.threads.create()  # 

        # 3.2) Añadir al Thread todos los mensajes previos de la conversación
        for m in user_and_assistant_msgs:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role=m["role"],
                content=m["content"]
            )

        # 3.3) Instanciar el handler que pone cada delta en la cola
        handler = _StreamHandler(queue)

        # 3.4) Ejecutar el Asistente en streaming.
        #      OBSERVA que NO ponemos max_tokens aquí, ya que runs.stream no lo acepta.
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=settings.system_prompt,  # 
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
    temperature: float = 0.3,
    max_tokens: int = 300,
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
        completion = client.beta.threads.runs.create(
            thread_id=None,                # No necesitamos thread previo
            assistant_id=assistant_id,
            instructions=prompt,           # 
            temperature=temperature,
            max_tokens=max_tokens,         # Este parámetro SÍ es válido para runs.create()
            stream=False,
        )
        return completion.choices[0].message.content.strip()

    # 3) Ejecutar en executor para no bloquear el event loop
    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)
    summary = await loop.run_in_executor(executor, _run_summarize)
    return summary


# ——————————————————————————
# Clase wrapper para exponer summarize a Main
# ——————————————————————————
class OpenAIService:
    """
    Wrapper que expone summarize_conversation a través de una clase estática.
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
