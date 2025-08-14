from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =====================================
# ENUMS - Définitions de base
# =====================================

class AnalysisType(str, Enum):
    STANDARD = "standard"
    ADVANCED = "advanced"
    CUSTOM = "custom"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExtractionMethod(str, Enum):
    SMART_PATTERN = "smart_pattern"
    AI_CONTEXTUAL = "ai_contextual_pattern"
    INTELLIGENT_VALIDATION = "intelligent_validation"
    UNIVERSAL_ADAPTIVE = "universal_adaptive"

class EconomicCategory(str, Enum):
    FINANCE_ET_MONNAIE = "finance_et_monnaie"
    PRIX_ET_INFLATION = "prix_et_inflation"
    COMMERCE_EXTERIEUR = "commerce_exterieur"
    PRODUCTION_ET_ACTIVITE = "production_et_activite"
    EMPLOI_ET_SALAIRES = "emploi_et_salaires"
    ECONOMIE_GENERALE = "economie_generale"

# =====================================
# MODÈLES DE PROGRESSION
# =====================================

class ProgressInfo(BaseModel):
    """Informations de progression standardisées"""
    current: int = 0
    total: int = 1
    percentage: float = 0.0
    display: str = "0/1"
    
    def update_from_values(self, current: int, total: int = None):
        """Met à jour la progression à partir de valeurs"""
        if total is not None:
            self.total = max(1, total)
        self.current = max(0, min(current, self.total))
        self.percentage = round((self.current / self.total) * 100, 2) if self.total > 0 else 0.0
        self.display = f"{self.current}/{self.total}"

# =====================================
# MODÈLES DE CONTENU
# =====================================

class ScrapedContent(BaseModel):
    """Contenu scrapé avec métadonnées"""
    raw_content: str
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]

class ExtractedValue(BaseModel):
    """Valeur extraite enrichie"""
    value: float
    raw_text: str
    indicator_name: str
    category: str
    unit: str
    unit_description: str = "Unité non spécifiée"
    
    # Métadonnées contextuelles
    context_text: str = ""
    extraction_method: ExtractionMethod = ExtractionMethod.SMART_PATTERN
    source_domain: Optional[str] = None
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Scores de qualité
    confidence_score: float = 0.0
    quality_score: float = 0.0
    
    # Flags de validation
    is_target_indicator: bool = False
    temporal_valid: bool = True
    validated: bool = False

class ExtractionSummary(BaseModel):
    """Résumé de l'extraction"""
    total_values: int = 0
    categories_found: int = 0
    target_indicators_found: int = 0
    validated_indicators: int = 0
    extraction_method: str = "smart_universal"
    processing_time: Optional[float] = None

# =====================================
# MODÈLES DE TÂCHES - VERSION UNIFIÉE
# =====================================

class TaskResponse(BaseModel):
    """Réponse de tâche unifiée - NOM PRINCIPAL"""
    task_id: str
    status: TaskStatus
    analysis_type: AnalysisType
    progress: ProgressInfo
    results: List[Dict[str, Any]] = []
    
    # Métadonnées temporelles
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Gestion d'erreurs
    error: Optional[str] = None
    
    # Configuration et données
    urls: List[str] = []
    parameters: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    
    # Informations d'extraction (optionnelles)
    extraction_summary: Optional[ExtractionSummary] = None
    settings_compliance: Optional[Dict[str, Any]] = None
    contextual_insights: Optional[Dict[str, Any]] = None
    
    # Propriétés calculées
    @property
    def has_error(self) -> bool:
        return self.error is not None
    
    @property
    def has_results(self) -> bool:
        return len(self.results) > 0
    
    @property
    def urls_count(self) -> int:
        return len(self.urls)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

class TaskListResponse(BaseModel):
    """Réponse de liste de tâches"""
    tasks: List[TaskResponse]
    total: int
    limit: int
    filter: Dict[str, Any] = {}

class TaskCreateResponse(BaseModel):
    """Réponse de création de tâche"""
    task_id: str
    status: TaskStatus
    message: str = "Task created successfully"

# =====================================
# MODÈLES DE REQUÊTE
# =====================================

class ScrapeRequest(BaseModel):
    """Requête de scraping - FORMAT UNIFIÉ"""
    urls: List[str]
    analysis_type: AnalysisType = AnalysisType.STANDARD
    parameters: Dict[str, Any] = {}
    callback_url: Optional[str] = None
    priority: int = 1
    
    # Options avancées
    timeout: int = 30
    enable_intelligent_analysis: bool = True
    enable_llm_analysis: bool = False
    quality_threshold: float = 0.6

# =====================================
# MODÈLES D'ANALYSE
# =====================================

class AnalysisResult(BaseModel):
    """Résultat d'analyse enrichi"""
    indicators: List[Dict[str, Any]]
    confidence: float
    analysis_type: AnalysisType
    insights: Dict[str, Any]
    
    # Métadonnées d'analyse
    processing_time: Optional[float] = None
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# =====================================
# MODÈLES POUR AGENTS ET SCRAPERS
# =====================================

class ScrapingResult(BaseModel):
    """Résultat de scraping pour agents"""
    url: str
    content: Optional[ScrapedContent] = None
    status_code: int = 200
    metadata: Dict[str, Any] = {}
    success: bool = True
    error: Optional[str] = None
    analysis_type: AnalysisType = AnalysisType.STANDARD
    llm_analysis: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def dict(self):
        """Méthode pour sérialisation"""
        return {
            'url': self.url,
            'content': self.content.dict() if self.content else None,
            'status_code': self.status_code,
            'metadata': self.metadata,
            'success': self.success,
            'error': self.error,
            'analysis_type': self.analysis_type.value,
            'llm_analysis': self.llm_analysis,
            'timestamp': self.timestamp.isoformat()
        }

class CoordinatorResult(BaseModel):
    """Résultat du coordinateur"""
    task_id: str
    scraping_results: List[ScrapingResult]
    analysis_results: List[Any] = []  # AnalysisResult depuis analyzer_agent
    final_insights: Dict[str, Any]
    status: str
    total_processing_time: float
    timestamp: str

# =====================================
# MODÈLES DE CONFIGURATION
# =====================================

class ScraperConfiguration(BaseModel):
    """Configuration du scraper"""
    delay: float = 1.0
    timeout: int = 30
    enable_caching: bool = True
    max_content_size: int = 100000
    
    # Options d'extraction
    extraction_method: str = "smart_universal"
    validation_threshold: float = 0.6
    enable_pattern_optimization: bool = True

# =====================================
# MODÈLES D'ERREUR
# =====================================

class ExtractionError(BaseModel):
    """Erreur d'extraction détaillée"""
    error_type: str
    error_message: str
    url: Optional[str] = None
    stage: str = "unknown"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    recoverable: bool = False

class ValidationError(BaseModel):
    """Erreur de validation"""
    field_name: str
    error_message: str
    provided_value: Any
    expected_format: Optional[str] = None

# =====================================
# MODÈLES POUR L'ANALYSE INTELLIGENTE
# =====================================

class TemporalMetadata(BaseModel):
    """Métadonnées temporelles précises"""
    reference_date: Optional[str] = None
    period_type: str = "unknown"  # daily, monthly, quarterly, yearly
    is_current_period: bool = False
    year: Optional[int] = None
    month: Optional[str] = None
    day: Optional[int] = None

class ValidationDetails(BaseModel):
    """Détails de validation sémantique"""
    is_economic_indicator: bool = False
    is_temporally_coherent: bool = False
    is_value_plausible: bool = False
    has_institutional_backing: bool = False
    semantic_score: float = 0.0

class EconomicCoherence(BaseModel):
    """Analyse de cohérence économique"""
    is_economically_plausible: bool = True
    value_range_check: str = "unknown"
    context_consistency: bool = True
    temporal_alignment: bool = True

class EnhancedExtractedValue(BaseModel):
    """Valeur extraite enrichie avec contexte complet"""
    # Données de base
    value: float
    raw_text: str
    indicator_name: str
    category: str
    unit: str
    unit_description: str = "Unité non spécifiée"
    
    # Enrichissement contextuel
    enhanced_indicator_name: Optional[str] = None
    context_text: str = ""
    extraction_method: ExtractionMethod = ExtractionMethod.SMART_PATTERN
    source_domain: Optional[str] = None
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Métadonnées avancées
    temporal_metadata: Optional[TemporalMetadata] = None
    institutional_source: Optional[str] = None
    economic_coherence: Optional[EconomicCoherence] = None
    
    # Scores de qualité
    confidence_score: float = 0.0
    semantic_quality: float = 0.0
    overall_validation_score: float = 0.0
    quality_score: float = 0.0
    
    # Flags de validation
    is_target_indicator: bool = False
    temporal_valid: bool = True
    validated: bool = False
    is_real_indicator: bool = True
    
    # Détails de validation
    validation_details: Optional[ValidationDetails] = None
    pattern_index: Optional[int] = None

class SettingsCompliance(BaseModel):
    """Évaluation de conformité aux settings"""
    target_indicators_compliance: bool = False
    recognized_units_compliance: bool = False
    temporal_compliance: bool = False
    semantic_quality_compliance: bool = False
    validation_compliance: bool = False
    overall_compliance_score: float = 0.0
    compliant: bool = False
    details: Optional[str] = None

class SourceAnalysis(BaseModel):
    """Analyse de la source"""
    domain: str
    is_government: bool = False
    is_trusted_source: bool = False
    content_type: str = "general"
    language: str = "unknown"
    data_freshness: str = "unknown"

class ExtractionQuality(BaseModel):
    """Métriques de qualité d'extraction"""
    total_extracted: int = 0
    high_quality_count: int = 0
    target_indicators_found: int = 0
    categories_covered: int = 0
    average_confidence: float = 0.0

class ProcessingInfo(BaseModel):
    """Informations de traitement"""
    scraper_version: str = "smart_universal_v2.0"
    extraction_method: str = "intelligent_patterns"
    validation_enabled: bool = True
    ai_enhanced: bool = False
    context_enriched: bool = False
    semantic_validation: bool = False

# =====================================
# MODÈLES POUR L'ANALYSE LLM
# =====================================

class DataSummary(BaseModel):
    """Résumé intelligent des données"""
    total_indicators: int = 0
    validated_indicators: int = 0
    categories_found: List[str] = []
    time_periods_covered: List[str] = []
    sources_identified: List[str] = []

class QualityAssessment(BaseModel):
    """Évaluation de la qualité des données"""
    average_quality: float = 0.0
    high_quality_indicators: int = 0
    temporal_coherence: bool = True
    data_completeness: float = 0.0

class IndicatorAnalysis(BaseModel):
    """Analyse des indicateurs par catégorie"""
    finance_et_monnaie: List[Dict[str, Any]] = []
    prix_et_inflation: List[Dict[str, Any]] = []
    commerce_exterieur: List[Dict[str, Any]] = []
    production_et_activite: List[Dict[str, Any]] = []
    emploi_et_salaires: List[Dict[str, Any]] = []
    economie_generale: List[Dict[str, Any]] = []

class TemporalAnalysis(BaseModel):
    """Analyse des patterns temporels"""
    periods_found: int = 0
    most_recent: Optional[int] = None
    period_types: List[str] = []

class DataCoherence(BaseModel):
    """Analyse de cohérence des données"""
    temporal_consistency: bool = True
    value_ranges_realistic: bool = True
    indicator_coverage: Dict[str, int] = {}
    data_quality_score: float = 0.0

class LLMAnalysis(BaseModel):
    """Analyse LLM (Ollama/Mistral)"""
    insights: Dict[str, Any] = {}
    llm_status: str = "not_configured"
    recommendations: List[str] = []
    economic_context: Optional[str] = None
    trend_analysis: Optional[str] = None

class SmartInsights(BaseModel):
    """Insights intelligents complets"""
    data_summary: DataSummary
    quality_assessment: QualityAssessment
    indicator_analysis: Dict[str, List[Dict[str, Any]]]
    temporal_analysis: TemporalAnalysis
    recommendations: List[str]
    llm_analysis: LLMAnalysis

# =====================================
# MODÈLES ÉTENDUS POUR LES MÉTRIQUES
# =====================================

class ExtendedTaskMetrics(BaseModel):
    """Métriques étendues de tâche"""
    extraction_time: Optional[float] = None
    analysis_time: Optional[float] = None
    total_processing_time: Optional[float] = None
    urls_processed: int = 0
    indicators_extracted: int = 0
    quality_score: float = 0.0
    compliance_score: float = 0.0

class TaskResult(BaseModel):
    """Résultat de tâche complet - VERSION ÉTENDUE"""
    task_id: str
    status: TaskStatus
    progress: ProgressInfo
    analysis_type: AnalysisType
    results: List[Dict[str, Any]] = []
    
    # Métadonnées temporelles
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Gestion d'erreurs
    error: Optional[str] = None
    
    # Métriques avancées
    metrics: Dict[str, Any] = {}
    extended_metrics: Optional[ExtendedTaskMetrics] = None
    
    # Configuration et URLs
    urls: List[str] = []
    parameters: Dict[str, Any] = {}
    
    # Résultats enrichis
    extraction_summary: Optional[ExtractionSummary] = None
    settings_compliance: Optional[SettingsCompliance] = None
    contextual_insights: Optional[SmartInsights] = None
    
    # Propriétés calculées
    @property
    def has_error(self) -> bool:
        return self.error is not None
    
    @property
    def has_results(self) -> bool:
        return len(self.results) > 0
    
    @property
    def urls_count(self) -> int:
        return len(self.urls)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

# =====================================
# MODÈLES DE REQUÊTE ÉTENDUS
# =====================================

class ScrapingRequest(BaseModel):
    """Requête de scraping enrichie"""
    urls: List[str]
    analysis_type: AnalysisType = AnalysisType.STANDARD
    parameters: Dict[str, Any] = {}
    timeout: int = 30
    depth: int = 1
    callback_url: Optional[str] = None
    priority: int = 5
    
    # Options avancées
    enable_intelligent_analysis: bool = True
    enable_llm_analysis: bool = False
    enable_semantic_validation: bool = True
    quality_threshold: float = 0.6
    
    # Contraintes personnalisées
    custom_indicators: Optional[List[str]] = None
    custom_time_range: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    """Requête d'analyse spécialisée"""
    content: str
    url: str
    analysis_type: AnalysisType = AnalysisType.ADVANCED
    enable_context_enrichment: bool = True
    enable_validation: bool = True

# =====================================
# EXPORTS ET ALIASES DE COMPATIBILITÉ
# =====================================

# Aliases pour rétrocompatibilité (mais TaskResponse est le nom principal)
TaskProgress = ProgressInfo

# Exports principaux
__all__ = [
    # Enums
    "AnalysisType", "TaskStatus", "ExtractionMethod", "EconomicCategory",
    
    # Modèles principaux de tâches
    "TaskResponse", "TaskResult", "TaskListResponse", "TaskCreateResponse", 
    "ScrapeRequest", "ScrapingRequest", "ProgressInfo", "TaskProgress",
    
    # Modèles de contenu
    "ScrapedContent", "ExtractedValue", "EnhancedExtractedValue",
    
    # Modèles d'analyse
    "AnalysisResult", "AnalysisRequest", "ExtractionSummary",
    
    # Modèles pour agents
    "ScrapingResult", "CoordinatorResult",
    
    # Modèles d'analyse intelligente
    "TemporalMetadata", "ValidationDetails", "EconomicCoherence",
    "SettingsCompliance", "SourceAnalysis", "ExtractionQuality", "ProcessingInfo",
    
    # Modèles LLM et insights
    "DataSummary", "QualityAssessment", "IndicatorAnalysis", "TemporalAnalysis",
    "DataCoherence", "LLMAnalysis", "SmartInsights",
    
    # Configuration et erreurs
    "ScraperConfiguration", "ExtractionError", "ValidationError",
    
    # Métriques étendues
    "ExtendedTaskMetrics"
]