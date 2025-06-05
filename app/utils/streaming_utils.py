import json
from typing import AsyncGenerator
from fastapi import Response
import asyncio

async def format_sse_event(data: dict) -> str:
    """
    Dado un diccionario, lo convierte a la sintaxis SSE:
    data: <json>\n\n
    """
    json_str = json.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n"


async def sse_response_generator(
    generator_func: AsyncGenerator[dict, None]
) -> AsyncGenerator[bytes, None]:
    """
    Recibe un AsyncGenerator que va emitiendo diccionarios,
    y los transforma a bytes formateados como SSE.
    """
    async for chunk in generator_func:
        data_str = json.dumps(chunk, ensure_ascii=False)
        # Enviar con prefijo "data: " + doble salto de línea
        yield f"data: {data_str}\n\n"
        # Asegurarse de que se propague inmediatamente
        await asyncio.sleep(0)