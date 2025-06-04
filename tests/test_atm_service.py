import json
from pathlib import Path
import sys

# Permitir importaciones desde src/
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

import atm_service


def test_save_lead_creates_json(tmp_path, monkeypatch):
    log_file = tmp_path / "leads.json"
    monkeypatch.setattr(atm_service, "LOG_PATH", str(log_file))

    sample = {"name": "John", "email": "john@example.com"}
    result = atm_service.save_lead(sample)

    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert sample in data
    assert result["status"] == "ok"
    assert result["file"] == str(log_file)
