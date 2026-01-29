import json
import os
from typing import Dict, Optional, Any


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subjects.json")

def _load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_subject(name: str, data: Dict[str, Any]):
    db = _load_data()
    db[name.lower()] = data
    _save_data(db)

def get_subject(name: str) -> Optional[Dict[str, Any]]:
    db = _load_data()
    return db.get(name.lower())

def delete_subject(name: str) -> bool:
    db = _load_data()
    if name.lower() in db:
        del db[name.lower()]
        _save_data(db)
        return True
    return False

def list_subjects() -> list[str]:
    db = _load_data()
    return list(db.keys())
