import logging
from typing import Any, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def safe_parse_progress(value: Any, default: int = 0) -> int:
    """Parse une valeur de progression en entier sûr"""
    try:
        if isinstance(value, (int, float)):
            return int(max(0, value))
        elif isinstance(value, str):
            # Gérer les formats "3", "3.0", "3/5" etc.
            if '/' in value:
                parts = value.split('/')
                return int(max(0, float(parts[0].strip())))
            else:
                return int(max(0, float(value.strip())))
        else:
            return default
    except (ValueError, TypeError, AttributeError):
        logger.warning(f"Could not parse progress value: {value}, using default: {default}")
        return default

def validate_progress_pair(current: Any, total: Any) -> tuple[int, int]:
    """Valide et retourne une paire (current, total) sûre"""
    try:
        current_val = safe_parse_progress(current, 0)
        total_val = safe_parse_progress(total, 1)
        
        # Assurer que total >= 1
        if total_val <= 0:
            total_val = 1
            
        # Assurer que current <= total
        if current_val > total_val:
            current_val = total_val
            
        return current_val, total_val
    except Exception as e:
        logger.warning(f"Error validating progress pair ({current}, {total}): {e}")
        return 0, 1

def normalize_progress_string(value: Any) -> str:
    """Normalise une valeur en string sûre pour la base de données"""
    try:
        parsed_value = safe_parse_progress(value, 0)
        return str(parsed_value)
    except Exception as e:
        logger.warning(f"Error normalizing progress string: {e}")
        return "0"

def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Formate un timestamp en ISO format"""
    try:
        if dt:
            return dt.isoformat()
        return None
    except Exception as e:
        logger.warning(f"Erreur lors du formatage du timestamp: {e}")
        return None

def safe_json_loads(data: Any, default: Any = None) -> Any:
    """Parse JSON de manière sécurisée"""
    try:
        if isinstance(data, str):
            return json.loads(data)
        return data
    except Exception as e:
        logger.warning(f"Erreur lors du parsing JSON: {e}")
        return default or {}

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Sérialise en JSON de manière sécurisée"""
    try:
        return json.dumps(data, default=str)
    except Exception as e:
        logger.warning(f"Erreur lors de la sérialisation JSON: {e}")
        return default

def validate_url(url: str) -> bool:
    """Valide basiquement une URL"""
    try:
        url = url.strip()
        return url.startswith(('http://', 'https://')) and len(url) > 8
    except Exception:
        return False

def calculate_execution_time(start_time: Optional[datetime], end_time: Optional[datetime]) -> Optional[float]:
    """Calcule le temps d'exécution en secondes"""
    try:
        if start_time and end_time:
            delta = end_time - start_time
            return delta.total_seconds()
        return None
    except Exception as e:
        logger.warning(f"Erreur lors du calcul du temps d'exécution: {e}")
        return None

def truncate_content(content: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Tronque le contenu à une longueur maximale"""
    try:
        if content and len(content) > max_length:
            return content[:max_length] + "..."
        return content
    except Exception as e:
        logger.warning(f"Erreur lors de la troncature du contenu: {e}")
        return content

def extract_domain(url: str) -> Optional[str]:
    """Extrait le domaine d'une URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception as e:
        logger.warning(f"Erreur lors de l'extraction du domaine: {e}")
        return None

def generate_task_summary(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un résumé d'une tâche"""
    try:
        urls = task_data.get('urls', [])
        results = task_data.get('results', [])
        
        successful = len([r for r in results if r.get('success', False)]) if results else 0
        failed = len(results) - successful if results else 0
        
        return {
            "total_urls": len(urls),
            "successful_urls": successful,
            "failed_urls": failed,
            "success_rate": (successful / len(urls) * 100) if urls else 0,
            "status": task_data.get('status', 'unknown'),
            "analysis_type": task_data.get('analysis_type', 'standard')
        }
    except Exception as e:
        logger.warning(f"Erreur lors de la génération du résumé: {e}")
        return {}

class TaskProgressTracker:
    """Classe pour suivre le progrès d'une tâche"""
    
    def __init__(self, total: int):
        self.current = 0
        self.total = max(1, total)
        self.start_time = datetime.utcnow()
    
    def update(self, increment: int = 1) -> Dict[str, Any]:
        """Met à jour le progrès"""
        self.current = min(self.total, self.current + increment)
        return self.get_progress()
    
    def get_progress(self) -> Dict[str, Any]:
        """Retourne le progrès actuel"""
        percentage = int((self.current / self.total) * 100)
        return {
            "current": self.current,
            "total": self.total,
            "percentage": percentage,
            "display": f"{self.current}/{self.total}"
        }
    
    def is_complete(self) -> bool:
        """Vérifie si la tâche est terminée"""
        return self.current >= self.total
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estime le temps restant en secondes"""
        try:
            if self.current == 0:
                return None
            
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            rate = self.current / elapsed
            remaining_items = self.total - self.current
            
            return remaining_items / rate if rate > 0 else None
        except Exception:
            return None