from typing import Dict, Any
from app.config import settings
from crewai_plus_lead_scoring.crew import CrewaiPlusLeadScoringCrew
from app.models import CrewaiResult
import json


class CrewaiService:
    """
    Servicio para invocar al crew de CrewAI y obtener el JSON final de scoring.
    """

    @staticmethod
    def run_lead_scoring(
        form_response: str,
        additional_info: Dict[str, Any] = None,
    ) -> CrewaiResult:
        """
        Lanza el crew secuencial de CrewAI y devuelve un CrewaiResult validado.
        """

        # 1) Construir inputs para el crew
        payload = {
            "company": settings.company_name,
            "product_name": settings.product_name,
            "product_description": settings.product_description,
            "icp_description": settings.icp_description,
            "form_response": form_response,
        }
        if additional_info:
            payload.update(additional_info)

        # 2) Ejecutar el crew
        try:
            crew = CrewaiPlusLeadScoringCrew()
            raw_output = crew.crew().kickoff(inputs=payload)
        except Exception as e:
            raise RuntimeError(f"Error al ejecutar el crew de CrewAI: {e}")

        # 3) Convertir el output a diccionario
        if isinstance(raw_output, dict):
            output_dict = raw_output
        elif hasattr(raw_output, "json_dict") and raw_output.json_dict:
            output_dict = raw_output.json_dict
        elif hasattr(raw_output, "model_dump"):
            output_dict = raw_output.model_dump()
        elif hasattr(raw_output, "dict"):
            output_dict = raw_output.dict()
        else:
            output_dict = dict(raw_output)

        # 4) Validar/parsear contra nuestro Pydantic CrewaiResult
        try:
            result = CrewaiResult(**output_dict)
        except ValidationError as e:
            raise ValueError(f"Respuesta de CrewAI no coincide con el schema esperado: {e}")

        return result
