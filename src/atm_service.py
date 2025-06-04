# src/atm_service.py

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_PATH = os.path.join(DATA_DIR, "leads.json")

def save_lead(lead_record: dict):
    """
    Guarda el lead calificado en un archivo JSON local (en lugar de Airtable).
    """
    all_leads = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            try:
                all_leads = json.load(f)
            except json.JSONDecodeError:
                all_leads = []

    all_leads.append(lead_record)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, indent=2, ensure_ascii=False)
    return {"status": "ok", "file": LOG_PATH}
