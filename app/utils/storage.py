import json
from pathlib import Path
from datetime import datetime
from app.models.database import ScrapedData, get_db

class StorageManager:
    @staticmethod
    def save_to_disk(data: dict, filename: str = None):
        """Sauvegarder les données sur le disque"""
        filename = filename or f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("data").mkdir(exist_ok=True)
        with open(f"data/{filename}", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def save_to_db(data: dict):
        """Sauvegarder dans la base de données"""
        db = next(get_db())
        try:
            record = ScrapedData(
                url=data.get('url'),
                title=data.get('title', ''),
                content=data.get('content', ''),
                source_type=data.get('source_type', 'unknown'),
                metadata=data.get('metadata', {})
            )
            db.add(record)
            db.commit()
            return record.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()