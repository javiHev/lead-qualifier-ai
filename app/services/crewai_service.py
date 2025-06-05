from typing import Dict, Any
from app.config import settings
from crewai_plus_lead_scoring.crew import CrewaiPlusLeadScoringCrew
from app.models import CrewaiResult


class CrewaiService:
    """
    Servicio para invocar al crew de Crewai y obtener el JSON de scoring.
    """

    @staticmethod
    def run_lead_scoring(
        form_response: str,  # Por ejemplo, resumen de datos de formulario
        additional_info: Dict[str, Any] = None,
    ) -> CrewaiResult:
        """
        Lanza el crew secuencial de Crewai y devuelve un objeto CrewaiResult.
        - La entrada debe incluir company, product_name, product_description,
          icp_description y form_response (y cualquier metadata extra).
        - El crew ejecuta las tareas en orden y produce un JSON final.
        """
        # Construir inputs para el crew
        payload = {
            "company": settings.company_name,
            "product_name": settings.product_name,
            "product_description": settings.product_description,
            "icp_description": settings.icp_description,
            "form_response": form_response,
        }

        if additional_info:
            payload.update(additional_info)

        # Instanciar el crew
        crew = CrewaiPlusLeadScoringCrew()

        # Ejecutar de forma síncrona (el SDK de Crewai maneja internamente)
        # Asumimos que crew().kickoff devuelve un diccionario con el output de la última tarea:
        # e.g. {"lead_score": 8.5, "use_case_summary": "...", "talking_points": [...]}
        try:
            output = crew.crew().kickoff(inputs=payload)
        except Exception as e:
            raise RuntimeError(f"Error al ejecutar Crewai crew: {e}")

        # Validar/parsear a nuestro Pydantic CrewaiResult
        try:
            result = CrewaiResult(**output)
        except Exception as e:
            raise ValueError(f"Respuesta de Crewai no coincide con schema esperado: {e}")

        return result
