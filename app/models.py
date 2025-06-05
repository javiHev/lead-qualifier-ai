from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Cada mensaje de la conversación proveniente del iframe.
    """
    role: Literal["user", "assistant"]
    content: str


class ChatStreamRequest(BaseModel):
    """
    Payload que envía el iframe para solicitar streaming de respuesta.
    """
    messages: List[ChatMessage]


class ChatStreamResponseChunk(BaseModel):
    """
    Cada chunk de la respuesta streameada se enviará en este formato.
    El cliente debe concatenar el campo 'delta' para reconstruir el mensaje completo.
    """
    role: Literal["assistant"]
    delta: str


class ChatFinishRequest(BaseModel):
    """
    Cuando la conversación terminará, el front-end manda:
    - toda la conversación (messages)
    - opcionalmente metadata extra (e.g. user_id, session_id)
    """
    messages: List[ChatMessage]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class CrewaiResult(BaseModel):
    """
    Se corresponderá con el JSON que devuelve el proceso Crewai,
    basado en tu modelo LeadScore, pero ampliable si se requieren más campos.
    """
    lead_score: float
    use_case_summary: str
    talking_points: List[str]


class ChatFinishResponse(BaseModel):
    """
    Respuesta final al front-end con estado de éxito y datos guardados.
    """
    success: bool
    airtable_record_id: Optional[str] = None
    crewai_result: Optional[CrewaiResult] = None
    summary: Optional[str] = None
    message: Optional[str] = None
