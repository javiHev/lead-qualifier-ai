import os
import requests
from typing import Dict, Any
from app.config import settings


class AirtableService:
    """
    Servicio para interactuar con Airtable: crear registros en una tabla.
    """

    BASE_URL = "https://api.airtable.com/v0"

    @staticmethod
    def create_record(
        fields: Dict[str, Any]
    ) -> str:
        """
        Inserta un registro en la tabla definida en settings.airtable_table_name.
        Devuelve el record_id si se creó con éxito.
        """
        url = f"{AirtableService.BASE_URL}/{settings.airtable_base_id}/{settings.airtable_table_name}"
        headers = {
            "Authorization": f"Bearer {settings.airtable_api_key}",
            "Content-Type": "application/json",
        }
        data = {"fields": fields}

        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Airtable API error {resp.status_code}: {resp.text}")

        record = resp.json()
        return record.get("id")


    @staticmethod
    def build_lead_fields(
        user_id: str,
        session_id: str,
        crewai_data: Dict[str, Any],
        summary: str,
        conversation: str,
    ) -> Dict[str, Any]:
        """
        Construye el dict 'fields' que Airtable API espera, mezclando:
        - datos fijos (user_id, session_id)
        - datos de Crewai (lead_score, etc.)
        - resumen de la conversación
        - quizá la transcripción completa (opcional; podría guardarse en otro lado)
        """
        fields = {
            "User ID": user_id,
            "Session ID": session_id,
            "Lead Score": crewai_data.get("lead_score"),
            "Use Case Summary": crewai_data.get("use_case_summary"),
            "Talking Points": crewai_data.get("talking_points"),
            "Conversation Summary": summary,
            "Full Conversation": conversation,
        }
        # Añade más campos si tu base de Airtable los necesita (e.g. fecha, tags, etc.)
        return fields
