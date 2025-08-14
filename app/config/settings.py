import os
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Dict, List, Optional, Union
from enum import Enum

class AnalysisCategory(str, Enum):
    """Catégories d'analyse pour le classement des indicateurs"""
    NATIONAL_ACCOUNTS = "comptes_nationaux"
    INSTITUTIONAL = "secteurs_institutionnels"
    PRICES = "prix_et_inflation"
    HOUSEHOLDS = "menages"
    TRADE = "commerce_exterieur"
    FINANCE = "finance_et_monnaie"

class Settings(BaseSettings):
    # Configuration principale avec valeurs par défaut sécurisées
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    SECRET_KEY: str = Field("dev-secret-key-change-in-production-32chars", env="SECRET_KEY")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    
    @validator('DEBUG')
    def validate_debug(cls, v):
        if v and os.getenv('APP_ENV') == 'production':
            raise ValueError("Debug mode cannot be enabled in production")
        return v

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
        
    # Configuration des indicateurs prioritaires (2018-2025)
    TARGET_INDICATORS: Dict[AnalysisCategory, List[str]] = {
        AnalysisCategory.NATIONAL_ACCOUNTS: [
            "Produit Intérieur Brut (aux prix du marché)",
            "Revenu national",
            "Revenu national disponible brut",
            "Epargne nationale (brute)",
            "Epargne nationale (nette)",
            "PIB par habitant"
        ],
        AnalysisCategory.INSTITUTIONAL: [
            "Sociétés non financières",
            "Institutions financières",
            "Administration Publique",
            "Ménages",
            "Institutions sans but lucratif"
        ],
        AnalysisCategory.PRICES: [
            "Indice des prix à la consommation (IPC; 2015=100)",
            "Inflation",
            "Déflateur du PIB",
            "Indice des prix à la production"
        ],
        AnalysisCategory.HOUSEHOLDS: [
            "Revenu disponible brut des ménages",
            "Taille moyenne d'un ménage",
            "Dépenses de consommation finale",
            "Taux d'épargne des ménages"
        ],
        AnalysisCategory.TRADE: [
            "Exportations de biens",
            "Importations de biens",
            "Balance commerciale",
            "Taux de couverture"
        ],
        AnalysisCategory.FINANCE: [
            "Masse monétaire M3",
            "Crédits à l'économie",
            "Taux directeur BCT",
            "Réserves de change"
        ]
    }

    # Période d'analyse (2018-2025)
    TARGET_YEARS: List[int] = list(range(2018, 2026))
    
    # Unités de mesure reconnues
    RECOGNIZED_UNITS: Dict[str, str] = {
        "md": "millions de dinars",
        "mdt": "millions de dinars tunisiens",
        "milliers": "milliers",
        "dinars courants": "dinars courants",
        "dinars de 2015": "dinars constants 2015",
        "%": "pourcentage",
        "tnd": "dinars tunisiens",
        "usd": "dollars américains",
        "eur": "euros"
    }

    # Sources officielles fiables
    TRUSTED_SOURCES: List[str] = [
        "bct.gov.tn",
        "ins.tn",
        "finances.gov.tn",
        "tunisieindustrie.nat.tn",
        "investintunisia.tn",
        "commerce.gov.tn"
    ]

    # Configuration du scraping
    MAX_SCRAPE_RETRIES: int = Field(3, env="SCRAPE_MAX_RETRIES")
    REQUEST_TIMEOUT: int = Field(30, env="SCRAPE_TIMEOUT_SEC")
    DEFAULT_DELAY: float = Field(2.5, env="SCRAPE_DELAY_SEC")
    MIN_CONTENT_LENGTH: int = Field(5000, env="MAX_CONTENT_LENGTH_KB")
    KEYPHRASE_MIN_WORDS: int = Field(5)
    SCRAPE_USER_AGENT: str = Field(
        "Mozilla/5.0 (compatible; AgenticScraper/1.0; +https://votredomaine.com/bot)", 
        env="SCRAPE_USER_AGENT"
    )

    # Configuration Celery - 🔥 CORRECTION CRITIQUE
    CELERY_BROKER_URL: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://redis:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Configuration Redis pour compatibilité
    REDIS_URL: str = Field("redis://redis:6379/0", env="REDIS_URL")
    
    # 🔥 FIX CRITIQUE: Utiliser Union pour accepter string OU liste
    CELERY_ACCEPT_CONTENT: Union[str, List[str]] = Field("json", env="CELERY_ACCEPT_CONTENT")
    
    CELERY_TASK_SERIALIZER: str = Field("json", env="CELERY_TASK_SERIALIZER")
    CELERY_RESULT_SERIALIZER: str = Field("json", env="CELERY_RESULT_SERIALIZER")
    CELERY_TIMEZONE: str = Field("UTC", env="CELERY_TIMEZONE")
    CELERYD_PREFETCH_MULTIPLIER: int = Field(1, env="CELERYD_PREFETCH_MULTIPLIER")

    @validator('CELERY_ACCEPT_CONTENT', pre=True, always=True)
    def validate_celery_accept_content(cls, v):
        """Convertit différents formats en liste pour Celery - VERSION RENFORCÉE"""
        # Si c'est None ou vide, retourner la valeur par défaut
        if v is None or v == "":
            return "json"
        
        # Si c'est déjà une string simple
        if isinstance(v, str):
            # Éviter de parser comme JSON si c'est juste "json"
            if v in ["json", "pickle", "yaml", "msgpack"]:
                return v  # Retourner comme string
            # Si c'est une string avec des virgules
            elif ',' in v:
                return [item.strip() for item in v.split(',')]
            else:
                return v  # Retourner comme string
        
        # Si c'est déjà une liste
        elif isinstance(v, list):
            return [str(item) for item in v]
        
        # Fallback sécurisé
        else:
            return "json"
    
    # Configuration Ollama
    OLLAMA_HOST: str = Field("http://ollama:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field("tinyllama:latest", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(160, env="OLLAMA_TIMEOUT")
    OLLAMA_MAX_TOKENS: int = Field(2000, env="OLLAMA_MAX_TOKENS")
    OLLAMA_KEEP_ALIVE: str = Field("5m", env="OLLAMA_KEEP_ALIVE")
    OLLAMA_NUM_CTX: int = Field(4096, env="OLLAMA_NUM_CTX")
    OLLAMA_TEMPERATURE: float = Field(0.3, env="OLLAMA_TEMPERATURE")
    ENABLE_LLM_ANALYSIS: bool = Field(True, env="ENABLE_LLM_ANALYSIS")
    
    # Configuration base de données
    DATABASE_URL: str = Field("postgresql://postgres:dorra123@db:5432/scraper_db", env="DATABASE_URL")
    DB_HOST: str = Field("db", env="DB_HOST")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("dorra123", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("scraper_db", env="POSTGRES_DB")
    
    # 🚀 Méthode helper pour Celery
    def get_celery_config(self) -> dict:
        """Retourne la configuration Celery formatée correctement"""
        # Convertir CELERY_ACCEPT_CONTENT en liste si c'est une string
        accept_content = self.CELERY_ACCEPT_CONTENT
        if isinstance(accept_content, str):
            if ',' in accept_content:
                accept_content = [item.strip() for item in accept_content.split(',')]
            else:
                accept_content = [accept_content]
        
        return {
            'broker_url': self.CELERY_BROKER_URL,
            'result_backend': self.CELERY_RESULT_BACKEND,
            'accept_content': accept_content,  # Toujours une liste ici
            'task_serializer': self.CELERY_TASK_SERIALIZER,
            'result_serializer': self.CELERY_RESULT_SERIALIZER,
            'timezone': self.CELERY_TIMEZONE,
            'enable_utc': True,
            'task_track_started': True,
            'result_expires': 3600,
            'worker_prefetch_multiplier': self.CELERYD_PREFETCH_MULTIPLIER,
            'task_acks_late': True,
            'broker_connection_retry_on_startup': True,
            'task_always_eager': False,
            'task_eager_propagates': False,
            'worker_log_level': 'INFO',
            'task_reject_on_worker_lost': True,
            'task_soft_time_limit': 300,  # 5 minutes
            'task_time_limit': 600,       # 10 minutes
            'worker_max_tasks_per_child': 50,
        }
    
    # Configuration Pydantic v2
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

# ✅ Instance settings globale
settings = Settings()

# ✅ Export explicite
__all__ = ['Settings', 'settings', 'AnalysisCategory']