from datetime import datetime
from pydantic import BaseModel, validator

class TunisianIndicator(BaseModel):
    year: int
    value: float
    unit: str

    @validator('year')
    def validate_year(cls, v):
        if not 2018 <= v <= datetime.now().year:
            raise ValueError(f"Année {v} hors période 2018-2025")
        return v

    @validator('unit')
    def validate_unit(cls, v):
        valid_units = ["MD", "%", "milliers", "TND"]
        if v not in valid_units:
            raise ValueError(f"Unité {v} non valide. Options: {valid_units}")
        return v

def validate_indicators(data: list) -> dict:
    """Valide une liste de données et retourne les erreurs"""
    errors = []
    valid_data = []
    for item in data:
        try:
            valid_data.append(TunisianIndicator(**item).dict())
        except ValueError as e:
            errors.append(str(e))
    return {"valid_data": valid_data, "errors": errors}