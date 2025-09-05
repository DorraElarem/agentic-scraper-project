"""
Configuration de base de données simplifiée avec intelligence automatique
Architecture unifiée compatible avec l'ensemble du système
"""

import os
import logging
import uuid
from typing import Optional, Generator, Dict, Any, List
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

logger = logging.getLogger(__name__)

# Base pour les modèles
Base = declarative_base()

class SmartDatabaseConfig:
    """Configuration intelligente de base de données"""
    
    def __init__(self):
        # Configuration automatique depuis l'environnement
        self.database_url = self._build_database_url()
        
        # Paramètres optimisés pour l'intelligence automatique
        self.pool_size = 20
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 3600
        
        logger.info(f"Smart database config initialized: {self._mask_url(self.database_url)}")

    def _build_database_url(self) -> str:
        """Construction intelligente de l'URL de base de données"""
        # Vérifier DATABASE_URL d'abord
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # Construction automatique depuis les composants
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "dorra123")
        db_host = os.getenv("DB_HOST", "db")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "scraper_db")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _mask_url(self, url: str) -> str:
        """Masquer le mot de passe dans l'URL pour les logs"""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)

    def create_engine(self):
        """Créer le moteur SQLAlchemy optimisé"""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            echo=False
        )

# Instance globale
db_config = SmartDatabaseConfig()
engine = db_config.create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ScrapingTask(Base):
    """Modèle unifié pour les tâches de scraping intelligent"""
    __tablename__ = "scraping_tasks"
    
    # Colonnes principales
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Configuration intelligente de la tâche
    urls = Column(JSON, nullable=False)  # Liste des URLs
    analysis_type = Column(String(50), nullable=False, default="standard")
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=1)
    
    # Gestion automatique des reprises
    max_retries = Column(Integer, default=3, nullable=False)
    current_retries = Column(Integer, default=0, nullable=False)
    
    # Timestamps automatiques
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Résultats et données intelligentes
    results = Column(JSON, nullable=True)  # Résultats de scraping
    error = Column(Text, nullable=True)  # Messages d'erreur
    progress = Column(JSON, nullable=True)  # Progression unifiée
    
    # Métriques et intelligence
    metrics = Column(JSON, nullable=True)  # Métriques de performance
    parameters = Column(JSON, nullable=True)  # Paramètres de scraping
    callback_url = Column(String, nullable=True)
    
    # Métadonnées intelligentes
    metadata_info = Column(JSON, nullable=True)
    worker_id = Column(String(100), nullable=True)
    
    # Champs de compatibilité
    url = Column(String, nullable=True)
    task_type = Column(String, default="scraping")
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ScrapingTask(task_id='{self.task_id}', status='{self.status}', urls_count={len(self.urls) if self.urls else 0})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire pour API JSON"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'urls': self.urls or [],
            'analysis_type': self.analysis_type,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': self.results or [],
            'error': self.error,
            'progress': self.progress or self._default_progress(),
            'metrics': self.metrics or {},
            'parameters': self.parameters or {},
            'callback_url': self.callback_url,
            'max_retries': self.max_retries,
            'current_retries': self.current_retries,
            'worker_id': self.worker_id,
            'task_type': self.task_type,
            'metadata_info': self.metadata_info
        }

    def to_task_response(self) -> Dict[str, Any]:
        """Conversion pour réponse API /tasks/{task_id}"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "analysis_type": self.analysis_type,
            "progress": self.progress or self._default_progress(),
            "results": self.results or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "urls": self.urls or [],
            "parameters": self.parameters or {},
            "metrics": self.metrics or {},
            "callback_url": self.callback_url,
            "worker_id": self.worker_id,
            "intelligence_features": {
                "smart_coordination": True,
                "automatic_strategy": True,
                "llm_available": False,  # Sera mis à jour dynamiquement
                "tunisian_optimization": True
            }
        }
    
    def _default_progress(self) -> Dict[str, Any]:
        """Progression par défaut standardisée"""
        return {
            "current": 0,
            "total": len(self.urls) if self.urls else 1,
            "percentage": 0.0,
            "display": f"0/{len(self.urls) if self.urls else 1}"
        }
    
    def update_progress(self, current: int, total: Optional[int] = None):
        """Mise à jour intelligente de la progression"""
        if total is None:
            total = len(self.urls) if self.urls else 1
        
        percentage = (current / total * 100) if total > 0 else 0
        
        self.progress = {
            "current": current,
            "total": total,
            "percentage": round(percentage, 1),
            "display": f"{current}/{total}"
        }

def get_db() -> Generator[Session, None, None]:
    """Générateur de session de base de données"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager pour session DB avec gestion automatique"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_database_connection() -> bool:
    """Test intelligent de connexion base de données"""
    try:
        logger.info("Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            if test_result and test_result[0] == 1:
                logger.info("Database connection test successful")
                return True
            return False
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def create_tables() -> bool:
    """Création intelligente des tables"""
    try:
        logger.info("Creating/verifying database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def init_database() -> bool:
    """Initialisation intelligente de la base de données"""
    try:
        logger.info("Initializing smart database...")
        
        # Test de connexion
        if not test_database_connection():
            raise Exception("Database connection failed")
        
        # Mise à jour du schéma
        upgrade_schema_smart()
        
        # Normalisation des données
        normalize_data_smart()
        
        # Création des tables
        if not create_tables():
            raise Exception("Table creation failed")
        
        logger.info("Smart database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Smart database initialization failed: {e}")
        return False

def upgrade_schema_smart():
    """Mise à jour intelligente du schéma"""
    try:
        logger.info("Upgrading database schema...")
        
        with engine.connect() as connection:
            # Vérifier l'existence de la table
            table_exists = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'scraping_tasks'
                );
            """)).fetchone()[0]
            
            if not table_exists:
                logger.info("Table scraping_tasks will be created")
                return
            
            # Ajouter colonnes manquantes si nécessaire
            columns_to_add = [
                ("task_id", "VARCHAR(255) UNIQUE"),
                ("urls", "JSON"),
                ("analysis_type", "VARCHAR(50) DEFAULT 'standard'"),
                ("metrics", "JSON"),
                ("parameters", "JSON"),
                ("metadata_info", "JSON"),
                ("max_retries", "INTEGER DEFAULT 3"),
                ("current_retries", "INTEGER DEFAULT 0")
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    connection.execute(text(f"""
                        ALTER TABLE scraping_tasks 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_def};
                    """))
                    logger.debug(f"Column {column_name} added/verified")
                except Exception as e:
                    logger.debug(f"Column {column_name} might already exist: {e}")
            
            # Mise à jour des task_id manquants
            connection.execute(text("""
                UPDATE scraping_tasks 
                SET task_id = CAST(random() * 1000000000 AS VARCHAR) || '-' || CAST(EXTRACT(epoch FROM NOW()) AS VARCHAR)
                WHERE task_id IS NULL OR task_id = '';
            """))
            
            connection.commit()
            logger.info("Schema upgrade completed successfully")
            
    except Exception as e:
        logger.error(f"Schema upgrade failed: {e}")
        raise

def normalize_data_smart():
    """Normalisation intelligente des données existantes"""
    try:
        with engine.connect() as connection:
            # Normaliser la colonne progress
            connection.execute(text("""
                UPDATE scraping_tasks 
                SET progress = '{"current": 0, "total": 1, "percentage": 0.0, "display": "0/1"}'::json
                WHERE progress IS NULL 
                OR progress::text = 'null'
                OR progress::text = '{}';
            """))
            
            # Normaliser la colonne urls pour les anciennes tâches
            connection.execute(text("""
                UPDATE scraping_tasks 
                SET urls = CASE 
                    WHEN url IS NOT NULL AND urls IS NULL THEN json_build_array(url)
                    WHEN urls IS NULL THEN '[]'::json
                    ELSE urls
                END;
            """))
            
            # Normaliser les métriques
            connection.execute(text("""
                UPDATE scraping_tasks 
                SET metrics = '{}'::json
                WHERE metrics IS NULL;
            """))
            
            connection.commit()
            logger.info("Data normalization completed")
            
    except Exception as e:
        logger.warning(f"Data normalization failed: {e}")

def get_database_status() -> Dict[str, Any]:
    """Statut intelligent de la base de données"""
    try:
        status = {
            "connection": test_database_connection(),
            "tables_exist": False,
            "total_tasks": 0,
            "active_tasks": 0,
            "database_url_configured": bool(db_config.database_url)
        }
        
        if status["connection"]:
            with engine.connect() as connection:
                # Vérifier l'existence des tables
                table_check = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'scraping_tasks'
                    );
                """))
                status["tables_exist"] = table_check.fetchone()[0]
                
                if status["tables_exist"]:
                    # Compter les tâches
                    total_count = connection.execute(text("SELECT COUNT(*) FROM scraping_tasks"))
                    status["total_tasks"] = total_count.fetchone()[0]
                    
                    active_count = connection.execute(text("""
                        SELECT COUNT(*) FROM scraping_tasks 
                        WHERE status IN ('pending', 'running')
                    """))
                    status["active_tasks"] = active_count.fetchone()[0]
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        return {"connection": False, "error": str(e)}

# Fonctions de compatibilité
def init_db():
    """Alias pour compatibilité"""
    return init_database()

def verify_schema():
    """Vérification de schéma pour compatibilité"""
    try:
        upgrade_schema_smart()
        return True
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False

# Export des éléments principaux
__all__ = [
    'Base', 'engine', 'SessionLocal', 'get_db', 'get_db_session',
    'test_database_connection', 'init_database', 'init_db', 'create_tables',
    'ScrapingTask', 'upgrade_schema_smart', 'normalize_data_smart', 
    'get_database_status', 'SmartDatabaseConfig'
]