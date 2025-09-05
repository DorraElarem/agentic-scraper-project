"""
Configuration CORRIGÉE - Fix Pydantic v2 annotations
"""

import os
from typing import Dict, List, Optional, ClassVar
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from enum import Enum

class AnalysisCategory(str, Enum):
    """Catégories d'analyse pour l'économie tunisienne"""
    MONETARY_FINANCIAL = "monetary_financial"
    STATISTICAL_DEMOGRAPHIC = "statistical_demographic"
    INDUSTRIAL_PRODUCTION = "industrial_production"
    TRADE_COMMERCE = "trade_commerce"
    EMPLOYMENT_SOCIAL = "employment_social"
    GENERAL = "general"

class Settings(BaseSettings):
    # Configuration principale
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    SECRET_KEY: str = Field("agentic-scraper-tunisia-2024-secret-key", env="SECRET_KEY")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    # INTELLIGENCE AUTOMATIQUE
    INTELLIGENCE_MODE: str = Field("auto", env="INTELLIGENCE_MODE")
    AUTO_STRATEGY_SELECTION: bool = Field(True, env="AUTO_STRATEGY_SELECTION")
    AUTO_LLM_ACTIVATION: bool = Field(True, env="AUTO_LLM_ACTIVATION")
    AUTO_QUALITY_OPTIMIZATION: bool = Field(True, env="AUTO_QUALITY_OPTIMIZATION")
    
    # FIX: Utiliser ClassVar pour les attributs non-field
    TUNISIAN_PRIORITY_INDICATORS: ClassVar[Dict[str, List[str]]] = {
        "monetary_financial": [
            "Taux directeur BCT", "Inflation", "Masse monétaire", 
            "Réserves de change", "Taux de change TND/USD"
        ],
        "statistical_demographic": [
            "Population totale", "Taux de natalité", 
            "Taux de chômage", "PIB par habitant"
        ],
        "industrial_production": [
            "Production industrielle", "Exportations", 
            "Capacité d'utilisation", "Investissement industriel"
        ],
        "trade_commerce": [
            "Balance commerciale", "Exportations de biens", 
            "Importations de biens", "Principaux partenaires"
        ],
        "employment_social": [
            "Taux de chômage", "Emploi par secteur", 
            "Salaire moyen", "Protection sociale"
        ]
    }

    # Années cibles pour l'analyse
    TARGET_YEARS: ClassVar[List[int]] = list(range(2018, 2026))  # 2018-2025 inclus
    
    TEMPORAL_CONFIG: ClassVar[Dict[str, int]] = {
        'start_year': 2018,
        'end_year': 2025,
        'strict_filtering': True
    }
    
    # Sources officielles tunisiennes fiables
    TRUSTED_TUNISIAN_SOURCES: ClassVar[List[str]] = [
        "bct.gov.tn", "ins.tn", "finances.gov.tn",
        "tunisieindustrie.nat.tn", "investintunisia.tn"
    ]
    
    # FIX: Annotation correcte avec ClassVar
    TUNISIAN_GOVERNMENT_PATTERNS: ClassVar[Dict[str, Dict[str, any]]] = {
        'bct.gov.tn': {
            'indicators': [
                'taux directeur', 'TMM', 'inflation', 'réserves', 'crédit', 
                'masse monétaire', 'change', 'liquidité'
            ],
            'units': ['%', 'MD', 'TND', 'USD'],
            'timeout_multiplier': 1.5
        },
        'ins.tn': {
            'indicators': [
                'population', 'chômage', 'emploi', 'natalité', 'mortalité',
                'PIB par habitant', 'démographie'
            ],
            'units': ['%', '‰', 'millions', 'TND'],
            'timeout_multiplier': 1.3
        },
        'finances.gov.tn': {
            'indicators': [
                'budget', 'recettes', 'dépenses', 'dette', 'déficit',
                'investissement', 'FBCF'
            ],
            'units': ['MD', '%', 'TND'],
            'timeout_multiplier': 1.2
        }
    }

    # Validation renforcée pour éviter les années comme valeurs
    YEAR_VALUE_VALIDATION: ClassVar[Dict[str, any]] = {
        'min_year': 2018,  # CORRIGÉ: 2018 au lieu de 1990
        'max_year': 2025,  # CORRIGÉ: 2025 au lieu de 2030
        'reject_isolated_years': True,
        'context_keywords': ['année', 'year', 'en', 'depuis', 'période']
    }

    # Extraction temporelle améliorée
    TEMPORAL_EXTRACTION_CONFIG: ClassVar[Dict[str, any]] = {
        'search_radius': 200,
        'year_priority': 'most_recent',
        'default_to_current': True,
        'validate_year_context': True
    }

    # CONFIGURATION DU SCRAPING
    MAX_SCRAPE_RETRIES: int = Field(3, env="SCRAPE_MAX_RETRIES")
    REQUEST_TIMEOUT: int = Field(30, env="SCRAPE_TIMEOUT_SEC")
    DEFAULT_DELAY: float = Field(1.0, env="SCRAPE_DELAY_SEC")
    MIN_CONTENT_LENGTH: int = Field(50, env="MIN_CONTENT_LENGTH")
    MAX_CONTENT_LENGTH: int = Field(500000, env="MAX_CONTENT_LENGTH")
    
    SCRAPE_USER_AGENT: str = Field(
        "Mozilla/5.0 (compatible; TunisianEconomicScraper/2.0)", 
        env="SCRAPE_USER_AGENT"
    )
    
    # Configuration Redis/Celery
    REDIS_URL: str = Field("redis://redis:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://redis:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Configuration Ollama
    OLLAMA_HOST: str = Field("http://ollama:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field("mistral:7b-instruct-v0.2-q4_0", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(600, env="OLLAMA_TIMEOUT")
    OLLAMA_CONNECTION_TIMEOUT: int = Field(30, env="OLLAMA_CONNECTION_TIMEOUT") 
    OLLAMA_QUICK_TIMEOUT: int = Field(120, env="OLLAMA_QUICK_TIMEOUT") 
    OLLAMA_MAX_TOKENS: int = Field(600, env="OLLAMA_MAX_TOKENS")
    OLLAMA_KEEP_ALIVE: str = Field("10m", env="OLLAMA_KEEP_ALIVE")
    OLLAMA_NUM_CTX: int = Field(4096, env="OLLAMA_NUM_CTX")
    OLLAMA_TEMPERATURE: float = Field(0.1, env="OLLAMA_TEMPERATURE")
    
    # LLM Configuration
    ENABLE_LLM_ANALYSIS: bool = Field(True, env="ENABLE_LLM_ANALYSIS")
    LLM_AUTO_ACTIVATION: bool = Field(True, env="LLM_AUTO_ACTIVATION")
    LLM_QUALITY_THRESHOLD: float = Field(0.1, env="LLM_QUALITY_THRESHOLD")
    
    # LANGCHAIN Configuration
    LANGCHAIN_ENABLED: bool = Field(True, env="LANGCHAIN_ENABLED")
    LANGGRAPH_ENABLED: bool = Field(True, env="LANGGRAPH_ENABLED")
    AUTOGEN_ENABLED: bool = Field(False, env="AUTOGEN_ENABLED")

    # Configuration base de données
    DATABASE_URL: str = Field("postgresql://postgres:dorra123@db:5432/scraper_db", env="DATABASE_URL")
    DB_HOST: str = Field("db", env="DB_HOST")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("dorra123", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("scraper_db", env="POSTGRES_DB")
    
    # Configuration des workers
    MAX_WORKERS: int = Field(4, env="MAX_WORKERS")
    INTELLIGENT_WORKER_SCALING: bool = Field(True, env="INTELLIGENT_WORKER_SCALING")
    TASK_TIME_LIMIT: int = Field(720, env="TASK_TIME_LIMIT")
    TASK_SOFT_TIME_LIMIT: int = Field(660, env="TASK_SOFT_TIME_LIMIT")
    WORKER_MAX_TASKS_PER_CHILD: int = Field(50, env="WORKER_MAX_TASKS_PER_CHILD")  # Réduit
    WORKER_PREFETCH_MULTIPLIER: int = Field(1, env="WORKER_PREFETCH_MULTIPLIER")
    
    # Configuration de performance
    PERFORMANCE_TRACKING: bool = Field(True, env="PERFORMANCE_TRACKING")
    AUTO_OPTIMIZATION: bool = Field(True, env="AUTO_OPTIMIZATION")
    LEARNING_ENABLED: bool = Field(True, env="LEARNING_ENABLED")
    
    # UNITÉS RECONNUES - FIX avec ClassVar
    RECOGNIZED_UNITS: ClassVar[Dict[str, str]] = {
        'md': 'Millions de dinars',
        'mdt': 'Millions de dinars tunisiens',
        'tnd': 'Dinar tunisien',
        'usd': 'Dollar américain',
        'eur': 'Euro',
        '%': 'Pourcentage',
        'millions': 'Millions',
        'milliards': 'Milliards',
        'index': 'Indice',
        'ratio': 'Ratio',
        'billion': 'Milliard',
        'thousand': 'Millier',
        'kg': 'Kilogramme',
        'ton': 'Tonne',
        'year': 'Année',
        'month': 'Mois'
    }
    
    # SEUILS DE VALIDATION - FIX avec ClassVar
    VALIDATION_THRESHOLDS: ClassVar[Dict[str, float]] = {
        'minimum': 0.05,
        'acceptable': 0.15,
        'good': 0.4,
        'excellent': 0.7
    }
    
    # NOUVEAUX PARAMÈTRES
    ULTRA_PERMISSIVE_MODE: bool = Field(True, env="ULTRA_PERMISSIVE_MODE")
    EMERGENCY_FALLBACK_ENABLED: bool = Field(True, env="EMERGENCY_FALLBACK_ENABLED")
    DEBUG_EXTRACTION_ENABLED: bool = Field(True, env="DEBUG_EXTRACTION_ENABLED")
    
    def get_celery_config(self) -> dict:
        """Configuration Celery avec timeouts de sécurité"""
        return {
            'broker_url': self.CELERY_BROKER_URL,
            'result_backend': self.CELERY_RESULT_BACKEND,
            'accept_content': ['json'],
            'task_serializer': 'json',
            'result_serializer': 'json',
            'timezone': 'Africa/Tunis',
            'enable_utc': True,
            'task_track_started': True,
            'result_expires': 7200,
            'worker_prefetch_multiplier': self.WORKER_PREFETCH_MULTIPLIER,
            'task_acks_late': True,
            'broker_connection_retry_on_startup': True,
            'task_always_eager': False,
            
            'task_soft_time_limit': self.TASK_SOFT_TIME_LIMIT,
            'task_time_limit': self.TASK_TIME_LIMIT,
            'worker_max_tasks_per_child': self.WORKER_MAX_TASKS_PER_CHILD,
            'worker_disable_rate_limits': True,
            'task_compression': 'gzip',
            'task_reject_on_worker_lost': True,
            'task_ignore_result': False,
            
            'task_routes': {
                'app.tasks.scraping_tasks.smart_scrape_task': {
                    'queue': 'scraping_long',
                    'routing_key': 'scraping.long'
                },
                'app.tasks.scraping_tasks.health_check_task': {
                    'queue': 'monitoring',
                    'routing_key': 'monitoring'
                },
            },
            
            # Queues spécialisées
            'task_default_queue': 'default',
            'task_create_missing_queues': True,
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

# Instance settings globale
settings = Settings()

# Fonctions d'aide
def get_intelligence_config():
    return settings.get_intelligent_config() if hasattr(settings, 'get_intelligent_config') else {}

def get_tunisian_sources():
    return settings.TRUSTED_TUNISIAN_SOURCES

def get_priority_indicators():
    return settings.TUNISIAN_PRIORITY_INDICATORS

def get_validation_config():
    return {
        'thresholds': settings.VALIDATION_THRESHOLDS,
        'recognized_units': settings.RECOGNIZED_UNITS,
        'ultra_permissive': settings.ULTRA_PERMISSIVE_MODE
    }

def get_timeout_config():
    return {
        'request_timeout': settings.REQUEST_TIMEOUT,
        'task_soft_limit': settings.TASK_SOFT_TIME_LIMIT,
        'task_hard_limit': settings.TASK_TIME_LIMIT
    }

def validate_config():
    """Valide la configuration"""
    issues = []
    
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        issues.append("SECRET_KEY invalide")
    
    if settings.ENABLE_LLM_ANALYSIS and not settings.OLLAMA_HOST:
        issues.append("OLLAMA_HOST manquant avec LLM activé")
    
    if not settings.DATABASE_URL:
        issues.append("DATABASE_URL manquant")
    
    if not settings.REDIS_URL:
        issues.append("REDIS_URL manquant")
    
    if issues:
        raise ValueError(f"Configuration invalide: {', '.join(issues)}")
    
    return True

# Export des éléments principaux
__all__ = [
    'Settings', 'settings', 'AnalysisCategory',
    'get_intelligence_config', 'get_tunisian_sources', 'get_priority_indicators',
    'get_validation_config', 'get_timeout_config', 'validate_config'
]