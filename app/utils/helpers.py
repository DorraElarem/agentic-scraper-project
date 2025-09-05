"""
Utilitaires intelligents CORRIGÉS - Seuils permissifs et validation robuste
VERSION CORRIGÉE avec corrections critiques pour résoudre les problèmes de validation
"""

import logging
from typing import Any, Dict, Optional, Union, List
from datetime import datetime
import json
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

# =====================================
# UTILITAIRES DE PROGRESSION
# =====================================

def suggest_extraction_improvements(debug_info: Dict[str, Any]) -> List[str]:
    """Fonction manquante pour les suggestions d'amélioration"""
    
    suggestions = []
    
    if not debug_info:
        return ["Aucune information de debug disponible"]
    
    # Suggestions basées sur les données de debug
    extraction_count = debug_info.get('extraction_count', 0)
    
    if extraction_count == 0:
        suggestions.append("Aucune donnée extraite - vérifier les sélecteurs CSS")
        suggestions.append("Considérer l'utilisation de Selenium pour le contenu JavaScript")
    elif extraction_count < 5:
        suggestions.append("Peu de données extraites - élargir les patterns de recherche")
        suggestions.append("Vérifier les filtres temporels et de validation")
    
    # Suggestions pour les sites gouvernementaux
    url = debug_info.get('url', '')
    if 'gov.tn' in url:
        suggestions.append("Site gouvernemental détecté - considérer des délais d'attente plus longs")
        suggestions.append("Vérifier si le contenu nécessite une authentification")
    
    return suggestions if suggestions else ["Extraction semble optimale"]



def safe_parse_progress(value: Any, default: int = 0) -> int:
    """Parse une valeur de progression de manière sécurisée"""
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
    """Valide et retourne une paire (current, total) sécurisée"""
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

def create_progress_info(current: int, total: int) -> Dict[str, Any]:
    """Crée un objet progress standardisé"""
    current, total = validate_progress_pair(current, total)
    percentage = round((current / total * 100), 1) if total > 0 else 0.0
    
    return {
        "current": current,
        "total": total,
        "percentage": percentage,
        "display": f"{current}/{total}"
    }

# =====================================
# UTILITAIRES TEMPORELS
# =====================================

def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Formate un timestamp en ISO format de manière sécurisée"""
    try:
        if dt:
            return dt.isoformat()
        return None
    except Exception as e:
        logger.warning(f"Erreur lors du formatage du timestamp: {e}")
        return None

def calculate_execution_time(start_time: Optional[datetime], end_time: Optional[datetime]) -> float:
    """Calcule le temps d'exécution en secondes"""
    try:
        if start_time and end_time:
            delta = end_time - start_time
            return round(delta.total_seconds(), 3)
        return 0.0
    except Exception as e:
        logger.warning(f"Erreur lors du calcul du temps d'exécution: {e}")
        return 0.0

def get_current_timestamp() -> str:
    """Retourne le timestamp actuel en format ISO"""
    return datetime.utcnow().isoformat()

# =====================================
# UTILITAIRES JSON
# =====================================

def safe_json_loads(data: Any, default: Any = None) -> Any:
    """Parse JSON de manière sécurisée avec fallback intelligent"""
    try:
        if isinstance(data, str):
            return json.loads(data)
        elif isinstance(data, (dict, list)):
            return data
        return data
    except Exception as e:
        logger.warning(f"Erreur lors du parsing JSON: {e}")
        return default or {}

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Sérialise en JSON de manière sécurisée"""
    try:
        return json.dumps(data, default=str, ensure_ascii=False, indent=None)
    except Exception as e:
        logger.warning(f"Erreur lors de la sérialisation JSON: {e}")
        return default

# =====================================
# UTILITAIRES URL ET VALIDATION - CORRIGÉS
# =====================================

def validate_url(url: str) -> bool:
    """Valide une URL de manière robuste - VERSION CORRIGÉE"""
    try:
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            return False
        
        parsed = urlparse(url)
        return bool(parsed.netloc and parsed.scheme)
    except Exception:
        return False

def extract_domain(url: str) -> str:
    """Extrait le domaine d'une URL de manière sécurisée"""
    try:
        parsed = urlparse(url.strip())
        return parsed.netloc or "unknown_domain"
    except Exception as e:
        logger.warning(f"Erreur lors de l'extraction du domaine: {e}")
        return "unknown_domain"

def categorize_url_type(url: str) -> str:
    """Catégorise automatiquement le type d'URL"""
    try:
        url_lower = url.lower()
        domain = extract_domain(url).lower()
        
        # APIs
        if any(indicator in url_lower for indicator in ['api.', '/api/', '.json', 'format=json']):
            return "api"
        
        # Sites gouvernementaux tunisiens
        elif any(gov in domain for gov in ['bct.gov.tn', 'ins.tn', 'finances.gov.tn']):
            return "government_tunisian"
        
        # Documents
        elif url_lower.endswith(('.pdf', '.xlsx', '.xls', '.doc', '.docx')):
            return "document"
        
        # Sites commerciaux/industriels
        elif any(indicator in domain for indicator in ['industrie', 'commerce', 'business']):
            return "commercial"
        
        # Par défaut
        else:
            return "general_web"
            
    except Exception as e:
        logger.warning(f"Error categorizing URL {url}: {e}")
        return "unknown"

# =====================================
# UTILITAIRES DE TÂCHES - CORRIGÉS
# =====================================

def validate_task_parameters(urls: List[str], **kwargs) -> Dict[str, Any]:
    """Valide les paramètres d'une tâche de scraping - VERSION ULTRA-PERMISSIVE"""
    try:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "normalized_params": {}
        }
        
        # Validation des URLs - CORRIGÉE (ultra-permissive)
        if not urls:
            validation_result["valid"] = False
            validation_result["errors"].append("Aucune URL fournie")
        else:
            valid_urls = []
            for url in urls:
                if url and url.strip():  # CORRIGÉ: Accepter toute URL non-vide
                    valid_urls.append(url.strip())
                else:
                    validation_result["warnings"].append(f"URL vide ignorée")
            
            if not valid_urls:
                validation_result["valid"] = False
                validation_result["errors"].append("Aucune URL valide")
            else:
                validation_result["normalized_params"]["urls"] = valid_urls
        
        # Validation des autres paramètres - SEUILS ULTRA-PERMISSIFS
        quality_threshold = kwargs.get('quality_threshold', 0.1)  # CORRIGÉ: 0.1 par défaut
        if not 0 <= quality_threshold <= 1:
            validation_result["warnings"].append("quality_threshold ajusté entre 0 et 1")
            quality_threshold = max(0, min(1, quality_threshold))
        # CORRIGÉ: Forcer un minimum très bas
        quality_threshold = max(quality_threshold, 0.05)
        validation_result["normalized_params"]["quality_threshold"] = quality_threshold
        
        timeout = kwargs.get('timeout', 60)
        if not 10 <= timeout <= 300:
            validation_result["warnings"].append("timeout ajusté entre 10 et 300 secondes")
            timeout = max(10, min(300, timeout))
        validation_result["normalized_params"]["timeout"] = timeout
        
        priority = kwargs.get('priority', 1)
        if not 1 <= priority <= 10:
            validation_result["warnings"].append("priority ajustée entre 1 et 10")
            priority = max(1, min(10, priority))
        validation_result["normalized_params"]["priority"] = priority
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating task parameters: {e}")
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "normalized_params": {}
        }

# =====================================
# NOUVELLES FONCTIONS DE DEBUG
# =====================================

def debug_extraction_data(extracted_data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Debug les données extraites pour identifier les problèmes"""
    debug_info = {
        'url': url,
        'timestamp': datetime.utcnow().isoformat(),
        'extraction_analysis': {}
    }
    
    try:
        values = extracted_data.get('values', {})
        debug_info['extraction_analysis'] = {
            'total_values_found': len(values),
            'value_types': {},
            'confidence_distribution': {},
            'categories_found': set(),
            'sample_values': {}
        }
        
        # Analyse des types de valeurs
        for key, value_data in values.items():
            if isinstance(value_data, dict):
                confidence = value_data.get('confidence_score', 0)
                category = value_data.get('category', 'unknown')
                
                debug_info['extraction_analysis']['categories_found'].add(category)
                
                # Distribution de confiance
                conf_range = 'high' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'low'
                debug_info['extraction_analysis']['confidence_distribution'][conf_range] = \
                    debug_info['extraction_analysis']['confidence_distribution'].get(conf_range, 0) + 1
                
                # Échantillon de valeurs (premières 3)
                if len(debug_info['extraction_analysis']['sample_values']) < 3:
                    debug_info['extraction_analysis']['sample_values'][key] = {
                        'value': value_data.get('value'),
                        'indicator_name': value_data.get('indicator_name'),
                        'confidence': confidence,
                        'validated': value_data.get('validated', False)
                    }
        
        debug_info['extraction_analysis']['categories_found'] = list(debug_info['extraction_analysis']['categories_found'])
        
        # Recommandations de debug
        recommendations = []
        if len(values) == 0:
            recommendations.append("Aucune valeur extraite - vérifier les patterns d'extraction")
        elif debug_info['extraction_analysis']['confidence_distribution'].get('low', 0) > len(values) * 0.5:
            recommendations.append("Beaucoup de valeurs à faible confiance - ajuster les seuils")
        elif debug_info['extraction_analysis']['confidence_distribution'].get('high', 0) > 0:
            recommendations.append("Extraction réussie avec de bonnes valeurs")
        
        debug_info['recommendations'] = recommendations
        
    except Exception as e:
        debug_info['error'] = str(e)
    
    return debug_info

def log_extraction_details(extracted_data: Dict[str, Any], url: str, strategy: str):
    """Log détaillé des extractions pour debug"""
    try:
        values = extracted_data.get('values', {})
        logger.info(f"=== EXTRACTION DETAILS for {url} (strategy: {strategy}) ===")
        logger.info(f"Total values extracted: {len(values)}")
        
        if values:
            for i, (key, value_data) in enumerate(values.items()):
                if i < 5:  # Log seulement les 5 premiers
                    if isinstance(value_data, dict):
                        logger.info(f"  [{i+1}] {key}:")
                        logger.info(f"      Value: {value_data.get('value')}")
                        logger.info(f"      Name: {value_data.get('indicator_name')}")
                        logger.info(f"      Confidence: {value_data.get('confidence_score', 0):.3f}")
                        logger.info(f"      Validated: {value_data.get('validated', False)}")
        else:
            logger.warning(f"No values extracted from {url}")
            
        # Log des métriques de qualité
        quality_metrics = extracted_data.get('quality_metrics', {})
        if quality_metrics:
            logger.info(f"Quality metrics: {quality_metrics}")
        
        logger.info("=== END EXTRACTION DETAILS ===")
        
    except Exception as e:
        logger.error(f"Error logging extraction details: {e}")

def suggest_extraction_improvements(debug_info: Dict[str, Any]) -> List[str]:
    """Suggère des améliorations basées sur l'analyse de debug"""
    suggestions = []
    
    try:
        analysis = debug_info.get('extraction_analysis', {})
        total_values = analysis.get('total_values_found', 0)
        conf_dist = analysis.get('confidence_distribution', {})
        
        if total_values == 0:
            suggestions.extend([
                "Vérifier si l'URL retourne du contenu",
                "Ajuster les patterns d'extraction",
                "Essayer la stratégie alternative",
                "Réduire les seuils de validation"
            ])
        elif conf_dist.get('low', 0) > total_values * 0.7:
            suggestions.extend([
                "Réduire le seuil de confiance minimum",
                "Améliorer la validation des indicateurs",
                "Vérifier la catégorisation automatique"
            ])
        elif total_values < 3:
            suggestions.extend([
                "Enrichir les patterns d'extraction",
                "Tester avec des seuils plus permissifs",
                "Vérifier la pertinence des mots-clés"
            ])
        else:
            suggestions.append("Extraction fonctionnelle - optimisations mineures possibles")
            
    except Exception as e:
        suggestions.append(f"Erreur d'analyse: {e}")
    
    return suggestions

# =====================================
# UTILITAIRES SPÉCIALISÉS TUNISIENS - AMÉLIORÉS
# =====================================

def detect_tunisian_content_patterns(content: str) -> Dict[str, Any]:
    """Détecte les patterns spécifiques au contenu économique tunisien - AMÉLIORÉ"""
    try:
        if not content:
            return {"tunisian_context": False}
        
        content_lower = content.lower()
        
        # Institutions tunisiennes
        institutions = ['bct', 'banque centrale tunisie', 'ins', 'institut national statistique']
        institution_matches = sum(1 for inst in institutions if inst in content_lower)
        
        # Références géographiques
        geographic_refs = ['tunisie', 'tunisia', 'tunis', 'sfax', 'sousse', 'gouvernorat']
        geo_matches = sum(1 for geo in geographic_refs if geo in content_lower)
        
        # Termes économiques tunisiens
        economic_terms = ['dinar', 'tnd', 'millimes', 'pib tunisien', 'économie tunisienne']
        economic_matches = sum(1 for term in economic_terms if term in content_lower)
        
        # NOUVEAU: Indicateurs numériques
        numbers = re.findall(r'\b\d+[.,]?\d*\b', content)
        numeric_density = len(numbers) / max(len(content.split()), 1) * 1000  # Pour 1000 mots
        
        # Indicateurs temporels
        years = re.findall(r'\b(20[0-2][0-9])\b', content)
        recent_years = [y for y in years if int(y) >= 2020]
        
        # Score global AMÉLIORÉ
        total_score = institution_matches + geo_matches + economic_matches
        
        return {
            "tunisian_context": total_score > 0,
            "context_strength": "high" if total_score >= 3 else "medium" if total_score >= 2 else "low" if total_score >= 1 else "none",
            "institutional_density": institution_matches,
            "geographic_density": geo_matches,
            "economic_density": economic_matches,
            "numeric_density": numeric_density,
            "temporal_relevance": len(recent_years),
            "tunisian_score": min(1.0, total_score / 5),
            "data_richness": "high" if numeric_density > 50 else "medium" if numeric_density > 20 else "low"
        }
        
    except Exception as e:
        logger.warning(f"Error detecting Tunisian content patterns: {e}")
        return {"tunisian_context": False, "error": str(e)}

def suggest_optimal_strategy(url: str, content: Optional[str] = None) -> Dict[str, Any]:
    """Suggère la stratégie optimale pour une URL donnée - AMÉLIORÉ"""
    try:
        url_type = categorize_url_type(url)
        domain = extract_domain(url)
        
        # Analyse du contenu si disponible
        content_analysis = {}
        if content:
            content_analysis = detect_tunisian_content_patterns(content)
        
        # Logique de recommandation CORRIGÉE
        if url_type == "api":
            recommended_strategy = "traditional"
            confidence = 0.9
            reason = "API détectée - méthode traditionnelle optimale"
        elif url_type == "government_tunisian":
            recommended_strategy = "intelligent"
            confidence = 0.95
            reason = "Site gouvernemental tunisien - méthode intelligente nécessaire"
        elif url_type == "document":
            recommended_strategy = "intelligent"
            confidence = 0.8
            reason = "Document détecté - extraction spécialisée requise"
        elif content_analysis.get("tunisian_context"):
            recommended_strategy = "intelligent"
            confidence = 0.8
            reason = "Contenu tunisien détecté - optimisation contextuelle"
        elif content_analysis.get("data_richness") == "high":
            recommended_strategy = "traditional"
            confidence = 0.7
            reason = "Données structurées détectées - méthode traditionnelle efficace"
        else:
            recommended_strategy = "traditional"  # CORRIGÉ: Préférer traditional par défaut
            confidence = 0.6
            reason = "Stratégie par défaut optimisée"
        
        return {
            "recommended_strategy": recommended_strategy,
            "confidence": confidence,
            "reason": reason,
            "url_type": url_type,
            "domain": domain,
            "content_analysis": content_analysis,
            "alternatives": {
                "fallback_strategy": "intelligent" if recommended_strategy == "traditional" else "traditional",
                "hybrid_approach": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error suggesting optimal strategy for {url}: {e}")
        return {
            "recommended_strategy": "traditional",  # CORRIGÉ: Fallback sûr
            "confidence": 0.5,
            "reason": "Erreur d'analyse - stratégie par défaut",
            "error": str(e)
        }

# =====================================
# UTILITAIRES DE CONTENU
# =====================================

def truncate_content(content: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Tronque le contenu à une longueur maximale de manière intelligente"""
    try:
        if not content:
            return content
        
        if len(content) <= max_length:
            return content
        
        # Tronquer en essayant de garder des phrases complètes
        truncated = content[:max_length]
        last_sentence = truncated.rfind('.')
        
        if last_sentence > max_length * 0.8:  # Si on trouve un point pas trop loin
            return truncated[:last_sentence + 1] + "..."
        else:
            return truncated + "..."
            
    except Exception as e:
        logger.warning(f"Erreur lors de la troncature du contenu: {e}")
        return content

def clean_text_content(content: str) -> str:
    """Nettoie le contenu textuel de manière intelligente"""
    try:
        if not content:
            return ""
        
        # Nettoyage basique
        cleaned = content.strip()
        
        # Supprimer les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Supprimer les caractères de contrôle
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        return cleaned
        
    except Exception as e:
        logger.warning(f"Error cleaning text content: {e}")
        return content

def extract_numbers_from_text(text: str) -> List[float]:
    """Extrait les nombres d'un texte de manière intelligente"""
    try:
        # Pattern pour nombres avec virgules/points décimaux
        number_pattern = r'\b\d+[.,]?\d*\b'
        matches = re.findall(number_pattern, text)
        
        numbers = []
        for match in matches:
            try:
                # Normaliser le format (virgule -> point)
                normalized = match.replace(',', '.')
                number = float(normalized)
                numbers.append(number)
            except ValueError:
                continue
        
        return numbers
        
    except Exception as e:
        logger.warning(f"Error extracting numbers from text: {e}")
        return []

# =====================================
# UTILITAIRES DE TÂCHES
# =====================================

def generate_task_summary(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un résumé intelligent d'une tâche"""
    try:
        urls = task_data.get('urls', [])
        results = task_data.get('results', [])
        
        successful = len([r for r in results if r.get('success', False)]) if results else 0
        failed = len(results) - successful if results else 0
        
        # Analyse des stratégies utilisées
        strategies = {}
        for result in results:
            strategy = result.get('strategy_used', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        # Calcul du score de qualité moyen
        quality_scores = [r.get('confidence_score', 0) for r in results if r.get('success')]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_urls": len(urls),
            "successful_urls": successful,
            "failed_urls": failed,
            "success_rate": round((successful / len(urls) * 100), 2) if urls else 0,
            "status": task_data.get('status', 'unknown'),
            "analysis_type": task_data.get('analysis_type', 'smart_automatic'),
            "strategy_distribution": strategies,
            "average_quality_score": round(avg_quality, 3),
            "processing_time": task_data.get('metrics', {}).get('execution_time', 0),
            "intelligence_features": {
                "automatic_strategy": True,
                "smart_coordination": True,
                "tunisian_optimization": True
            }
        }
    except Exception as e:
        logger.warning(f"Erreur lors de la génération du résumé: {e}")
        return {"error": str(e)}

def make_json_serializable(obj: Any) -> Any:
    """Rend un objet JSON-serializable de manière récursive"""
    if obj is None:
        return None
    elif isinstance(obj, (bool, int, float, str)):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'model_dump'):
        try:
            return make_json_serializable(obj.model_dump())
        except:
            return str(obj)
    elif hasattr(obj, 'dict'):
        try:
            return make_json_serializable(obj.dict())
        except:
            return str(obj)
    else:
        return str(obj)

# =====================================
# CLASSE UTILITAIRE POUR TRACKING
# =====================================

class SmartTaskProgressTracker:
    """Classe intelligente pour suivre le progrès d'une tâche"""
    
    def __init__(self, total: int, task_id: str = None):
        self.current = 0
        self.total = max(1, total)
        self.task_id = task_id
        self.start_time = datetime.utcnow()
        self.checkpoints = []
    
    def update(self, increment: int = 1) -> Dict[str, Any]:
        """Met à jour le progrès et retourne les métriques"""
        self.current = min(self.total, self.current + increment)
        
        # Enregistrer checkpoint
        now = datetime.utcnow()
        self.checkpoints.append({
            'time': now,
            'progress': self.current,
            'elapsed': (now - self.start_time).total_seconds()
        })
        
        return self.get_progress()
    
    def get_progress(self) -> Dict[str, Any]:
        """Retourne le progrès actuel avec métadonnées"""
        percentage = round((self.current / self.total) * 100, 1)
        
        return {
            "current": self.current,
            "total": self.total,
            "percentage": percentage,
            "display": f"{self.current}/{self.total}",
            "task_id": self.task_id,
            "elapsed_time": round((datetime.utcnow() - self.start_time).total_seconds(), 2),
            "estimated_remaining": self.get_estimated_time_remaining()
        }
    
    def is_complete(self) -> bool:
        """Vérifie si la tâche est terminée"""
        return self.current >= self.total
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estime le temps restant en secondes"""
        try:
            if self.current == 0 or len(self.checkpoints) < 2:
                return None
            
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            rate = self.current / elapsed if elapsed > 0 else 0
            remaining_items = self.total - self.current
            
            return round(remaining_items / rate, 1) if rate > 0 else None
        except Exception:
            return None

# Export des fonctions principales
__all__ = [
    # Progression
    'safe_parse_progress', 'validate_progress_pair', 'create_progress_info',
    
    # Temporel
    'format_timestamp', 'calculate_execution_time', 'get_current_timestamp',
    
    # JSON
    'safe_json_loads', 'safe_json_dumps', 'make_json_serializable',
    
    # URL et validation
    'validate_url', 'extract_domain', 'categorize_url_type',
    
    # Contenu
    'truncate_content', 'clean_text_content', 'extract_numbers_from_text',
    
    # Tâches
    'generate_task_summary', 'validate_task_parameters',
    
    # Classes
    'SmartTaskProgressTracker',
    
    # Debug - NOUVEAU
    'debug_extraction_data', 'log_extraction_details', 'suggest_extraction_improvements',
    
    # Spécialisés Tunisiens
    'detect_tunisian_content_patterns', 'suggest_optimal_strategy'
]