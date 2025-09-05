"""
Schémas Pydantic Simplifiés avec Intelligence Automatique
API unifiée sans complexité - Le système décide automatiquement
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid

# =====================================
# ÉNUMÉRATIONS SIMPLIFIÉES
# =====================================

class TaskStatus(str, Enum):
    """Statuts des tâches de scraping"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisType(str, Enum):
    """Types d'analyse (compatibilité)"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    CUSTOM = "custom"

class EconomicCategory(str, Enum):
    """Catégories économiques tunisiennes"""
    ECONOMIE_GENERALE = "economie_generale"
    FINANCE_ET_MONNAIE = "finance_et_monnaie"
    PRIX_ET_INFLATION = "prix_et_inflation"
    EMPLOI_ET_SALAIRES = "emploi_et_salaires"
    COMMERCE_EXTERIEUR = "commerce_exterieur"
    SECTEURS_INSTITUTIONNELS = "secteurs_institutionnels"

class ExtractionMethod(str, Enum):
    """Méthodes d'extraction pour tracking"""
    TRADITIONAL = "traditional"
    INTELLIGENT = "intelligent"
    SMART_PATTERN = "smart_pattern"
    AI_CONTEXTUAL = "ai_contextual_pattern"
    UNIVERSAL_ADAPTIVE = "universal_adaptive"
    INTELLIGENT_VALIDATION = "intelligent_validation"

# =====================================
# MODÈLES DE BASE SIMPLIFIÉS
# =====================================

class ProgressInfo(BaseModel):
    """Informations de progression standardisées"""
    current: int = 0
    total: int = 1
    percentage: float = 0.0
    display: str = "0/1"

class HealthCheck(BaseModel):
    """Vérification de santé du système"""
    healthy: bool = True
    services: Dict[str, str] = Field(default_factory=dict)
    coordinator_status: str = "operational"
    message: Optional[str] = None
    intelligence_mode: str = "automatic"

class SystemStatus(BaseModel):
    """Statut système détaillé"""
    status: str = "healthy"
    coordinator_active: bool = True
    scrapers_available: Dict[str, bool] = Field(default_factory=dict)
    llm_enabled: bool = False
    features: List[str] = Field(default_factory=list)
    intelligence_features: Dict[str, bool] = Field(default_factory=lambda: {
        "automatic_strategy_selection": True,
        "smart_llm_activation": True,
        "intelligent_fallbacks": True,
        "tunisian_optimization": True
    })
    message: Optional[str] = None

# =====================================
# REQUÊTES SIMPLIFIÉES
# =====================================

class ScrapingRequest(BaseModel):
    """Requête de scraping simplifiée - Intelligence automatique"""
    urls: List[str] = Field(..., min_length=1, max_length=10, description="URLs à scraper")
    enable_llm_analysis: bool = Field(False, description="Forcer l'activation LLM (optionnel)")
    priority: int = Field(1, ge=1, le=10, description="Priorité de la tâche")
    quality_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Seuil de qualité")
    callback_url: Optional[str] = Field(None, description="URL de callback")
    
    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v):
        if not v:
            raise ValueError("Au moins une URL est requise")
        
        valid_urls = []
        for url in v:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"URL invalide: {url}")
            valid_urls.append(url)
        
        return valid_urls
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "urls": [],
                "enable_llm_analysis": True,
                "priority": 1,
                "quality_threshold": 0.8
            }
        }
    }

class TaskCreateResponse(BaseModel):
    """Réponse de création de tâche"""
    task_id: str
    status: TaskStatus
    message: str
    coordinator_mode: str = "smart_automatic"
    intelligence_activated: bool = True

class TaskResponse(BaseModel):
    """Réponse unifiée de statut de tâche"""
    task_id: str
    status: TaskStatus
    progress: ProgressInfo
    results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    urls: List[str] = Field(default_factory=list)
    
    # Métadonnées intelligentes
    llm_analysis_enabled: bool = False
    ai_enhanced: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)
    strategy_used: str = "smart_automatic"
    coordinator_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Configuration par défaut
    intelligence_features: Dict[str, bool] = Field(default_factory=lambda: {
        "automatic_strategy_selection": True,
        "smart_coordination": True,
        "tunisian_optimization": True
    })

# =====================================
# MODÈLES DE DONNÉES EXTRAITES
# =====================================

class TemporalMetadata(BaseModel):
    """Métadonnées temporelles"""
    reference_date: Optional[str] = None
    period_type: str = "unknown"
    is_current_period: bool = False
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None

class EconomicCoherence(BaseModel):
    """Cohérence économique des données"""
    is_economically_plausible: bool = True
    value_range_check: str = "normal"
    context_consistency: bool = True
    temporal_alignment: bool = True

class ValidationDetails(BaseModel):
    """Détails de validation"""
    is_economic_indicator: bool = False
    is_temporally_coherent: bool = True
    is_value_plausible: bool = True
    has_institutional_backing: bool = False
    semantic_score: float = 0.0

class EnhancedExtractedValue(BaseModel):
    """Valeur extraite enrichie avec intelligence automatique"""
    value: Union[float, int, str]
    raw_text: str
    indicator_name: str
    enhanced_indicator_name: Optional[str] = None
    category: str = EconomicCategory.ECONOMIE_GENERALE.value
    unit: str = ""
    unit_description: str = "Unité non spécifiée"
    context_text: str = ""
    extraction_method: ExtractionMethod = ExtractionMethod.SMART_PATTERN
    source_domain: str
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Métadonnées enrichies
    temporal_metadata: Optional[TemporalMetadata] = None
    institutional_source: Optional[str] = None
    economic_coherence: EconomicCoherence = Field(default_factory=EconomicCoherence)
    
    # Scores de qualité automatiques
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    semantic_quality: float = Field(0.0, ge=0.0, le=1.0)
    overall_validation_score: float = Field(0.0, ge=0.0, le=1.0)
    quality_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Indicateurs de validation
    is_target_indicator: bool = False
    temporal_valid: bool = True
    validated: bool = False
    is_real_indicator: bool = True
    validation_details: ValidationDetails = Field(default_factory=ValidationDetails)
    pattern_index: Optional[int] = None

# =====================================
# MODÈLES D'ANALYSE INTELLIGENTE
# =====================================

class DataSummary(BaseModel):
    """Résumé des données extraites"""
    total_indicators: int = 0
    validated_indicators: int = 0
    categories_found: List[str] = Field(default_factory=list)
    time_periods_covered: List[str] = Field(default_factory=list)
    sources_identified: List[str] = Field(default_factory=list)

class QualityAssessment(BaseModel):
    """Évaluation automatique de qualité"""
    average_quality: float = 0.0
    high_quality_indicators: int = 0
    temporal_coherence: bool = True
    data_completeness: float = 0.0

class TemporalAnalysis(BaseModel):
    """Analyse temporelle automatique"""
    periods_found: int = 0
    most_recent: Optional[int] = None
    period_types: List[str] = Field(default_factory=list)

class LLMAnalysis(BaseModel):
    """Analyse LLM intelligente"""
    insights: Dict[str, Any] = Field(default_factory=dict)
    llm_status: str = "not_configured"
    recommendations: List[str] = Field(default_factory=list)
    economic_context: Optional[str] = None
    trend_analysis: Optional[str] = None

class SmartInsights(BaseModel):
    """Insights intelligents automatiques"""
    data_summary: DataSummary = Field(default_factory=DataSummary)
    quality_assessment: QualityAssessment = Field(default_factory=QualityAssessment)
    indicator_analysis: Dict[str, Any] = Field(default_factory=dict)
    temporal_analysis: TemporalAnalysis = Field(default_factory=TemporalAnalysis)
    recommendations: List[str] = Field(default_factory=list)
    llm_analysis: LLMAnalysis = Field(default_factory=LLMAnalysis)

class SettingsCompliance(BaseModel):
    """Conformité aux settings du projet"""
    target_indicators_compliance: bool = False
    recognized_units_compliance: bool = False
    temporal_compliance: bool = False
    semantic_quality_compliance: bool = False
    validation_compliance: bool = False
    overall_compliance_score: float = 0.0
    compliant: bool = False
    details: str = ""

# =====================================
# MODÈLES DE CONTENU
# =====================================

class SourceAnalysis(BaseModel):
    """Analyse intelligente de la source"""
    domain: str
    is_government: bool = False
    is_trusted_source: bool = False
    content_type: str = "general"
    language: str = "french"
    data_freshness: str = "unknown"

class ExtractionSummary(BaseModel):
    """Résumé d'extraction intelligent"""
    total_values: int = 0
    categories_found: int = 0
    target_indicators_found: int = 0
    validated_indicators: int = 0
    extraction_method: str = "smart_automatic"
    processing_time: float = 0.0

class ExtractionQuality(BaseModel):
    """Qualité d'extraction automatique"""
    total_extracted: int = 0
    high_quality_count: int = 0
    target_indicators_found: int = 0
    categories_covered: int = 0
    average_confidence: float = 0.0

class ProcessingInfo(BaseModel):
    """Informations de traitement intelligent"""
    scraper_version: str = "2.0_smart_unified"
    extraction_method: str = "intelligent_patterns"
    validation_enabled: bool = True
    ai_enhanced: bool = False
    context_enriched: bool = True
    semantic_validation: bool = True

class ScrapedContent(BaseModel):
    raw_content: Optional[str] = None
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def indicators(self) -> List[Dict[str, Any]]:
        """Retourne la liste des indicateurs extraits"""
        extracted_values = self.structured_data.get('extracted_values', {})
        if isinstance(extracted_values, dict):
            return list(extracted_values.values())
        return []

class AnalysisResult(BaseModel):
    """Résultat d'analyse intelligent complet"""
    success: bool = True
    total_indicators: int = 0
    validated_indicators: int = 0
    high_quality_indicators: int = 0
    average_quality_score: float = 0.0
    extraction_method: str = "intelligent_automatic"
    processing_time: float = 0.0
    
    # Données extraites
    extracted_values: List[EnhancedExtractedValue] = Field(default_factory=list)
    
    # Analyses intelligentes
    insights: SmartInsights = Field(default_factory=SmartInsights)
    source_analysis: Optional[SourceAnalysis] = None
    extraction_summary: ExtractionSummary = Field(default_factory=ExtractionSummary)
    extraction_quality: ExtractionQuality = Field(default_factory=ExtractionQuality)
    processing_info: ProcessingInfo = Field(default_factory=ProcessingInfo)
    
    # Conformité et validation
    settings_compliance: SettingsCompliance = Field(default_factory=SettingsCompliance)
    
    # Métadonnées
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source_url: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    # Intelligence automatique
    intelligence_metadata: Dict[str, Any] = Field(default_factory=lambda: {
        "automatic_analysis": True,
        "smart_categorization": True,
        "tunisian_optimization": True,
        "llm_enhanced": False
    })
    
    # Contenu original
    scraped_content: Optional[ScrapedContent] = None

# =====================================
# MODÈLES DE COMPATIBILITÉ
# =====================================

class ExtractedValue(BaseModel):
    """Valeur extraite simple (compatibilité)"""
    indicator_name: str
    value: Union[float, int, str]
    unit: str = ""
    confidence_score: float = 0.0
    source_domain: str
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SimpleTaskResult(BaseModel):
    """Résultat de tâche simplifié"""
    task_id: str
    status: str
    urls_processed: int = 0
    results_found: int = 0
    processing_time: float = 0.0
    success_rate: float = 0.0
    intelligence_used: bool = True

# =====================================
# MODÈLES POUR COORDINATION INTELLIGENTE
# =====================================

class CoordinatorStatus(BaseModel):
    """Statut du coordinateur intelligent"""
    coordinator_type: str = "SmartScrapingCoordinator"
    version: str = "2.0_automatic"
    available_strategies: List[str] = Field(default_factory=lambda: ["traditional", "intelligent"])
    auto_selection_enabled: bool = True
    fallback_enabled: bool = True
    performance_tracking: bool = True
    tunisian_optimization: bool = True

class ScrapingStrategy(BaseModel):
    """Stratégie de scraping automatique"""
    strategy_name: str
    reason: str
    confidence: float = 0.0
    fallback_available: bool = True
    expected_performance: str = "good"

class IntelligenceReport(BaseModel):
    """Rapport d'intelligence du système"""
    total_operations: int = 0
    success_rate: float = 0.0
    strategy_distribution: Dict[str, int] = Field(default_factory=dict)
    llm_activation_rate: float = 0.0
    tunisian_sources_processed: int = 0
    average_processing_time: float = 0.0
    performance_level: str = "optimal"
    recommendations: List[str] = Field(default_factory=list)

# Alias pour compatibilité
ScrapeRequest = ScrapingRequest

# Export des classes principales
__all__ = [
    # Énumérations
    'TaskStatus', 'EconomicCategory', 'ExtractionMethod', 'AnalysisType',
    
    # Modèles de base
    'ProgressInfo', 'HealthCheck', 'SystemStatus',
    
    # Requêtes/Réponses
    'ScrapingRequest', 'ScrapeRequest', 'TaskCreateResponse', 'TaskResponse',
    
    # Données extraites
    'EnhancedExtractedValue', 'TemporalMetadata', 'EconomicCoherence', 'ValidationDetails',
    
    # Analyse intelligente
    'SmartInsights', 'DataSummary', 'QualityAssessment', 'LLMAnalysis', 'SettingsCompliance',
    'AnalysisResult', 'TemporalAnalysis',
    
    # Contenu
    'ScrapedContent', 'SourceAnalysis', 'ExtractionSummary', 'ExtractionQuality', 'ProcessingInfo',
    
    # Coordination intelligente
    'CoordinatorStatus', 'ScrapingStrategy', 'IntelligenceReport', 'SimpleTaskResult',
    
    # Compatibilité
    'ExtractedValue'
]