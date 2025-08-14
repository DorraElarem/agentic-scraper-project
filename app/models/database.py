"""
Configuration de la base de données avec SQLAlchemy 2.0
Modèle ScrapingTask compatible avec scraping_tasks.py et schemas.py
"""
import os
import logging
import uuid
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base pour les modèles - SANS metadata (nom réservé)
Base = declarative_base()

class DatabaseConfig:
    """Configuration de la base de données"""
    
    def __init__(self):
        # URL de base de données depuis les variables d'environnement
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # Configuration par défaut
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "dorra123")
            db_host = os.getenv("POSTGRES_HOST", "db")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "scraper_db")
            self.database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Configuration du pool
        self.pool_size = 20
        self.max_overflow = 10
        self.pool_timeout = 30
        self.pool_recycle = 3600

    def create_engine(self):
        """Créer le moteur SQLAlchemy"""
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
db_config = DatabaseConfig()
engine = db_config.create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ MODÈLE SCRAPINGTASK UNIFIÉ - Compatible avec scraping_tasks.py
class ScrapingTask(Base):
    """Modèle pour les tâches de scraping - VERSION UNIFIÉE"""
    __tablename__ = "scraping_tasks"
    
    # ✅ Colonnes principales
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # ✅ Configuration de la tâche
    urls = Column(JSON, nullable=False)  # Liste des URLs (compatible scraping_tasks.py)
    analysis_type = Column(String(50), nullable=False, default="standard")  # Compatible schemas.py
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=1)
    
    # ✅ Gestion des reprises
    max_retries = Column(Integer, default=3, nullable=True, server_default='3')
    current_retries = Column(Integer, default=0, nullable=True, server_default='0')
    
    # ✅ Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # ✅ Résultats et données (compatible scraping_tasks.py)
    results = Column(JSON, nullable=True)  # Liste des résultats de scraping
    error = Column(Text, nullable=True)  # Nom compatible avec scraping_tasks.py
    progress = Column(JSON, nullable=True)  # Format JSON unifié
    
    # ✅ Métriques et analytics
    metrics = Column(JSON, nullable=True)  # Utilisé dans scraping_tasks.py
    
    # ✅ Configuration avancée
    parameters = Column(JSON, nullable=True)  # Paramètres de scraping
    callback_url = Column(String, nullable=True)
    
    # ✅ Métadonnées (renommé pour éviter conflit)
    metadata_info = Column(JSON, nullable=True)
    
    # ✅ Informations worker
    worker_id = Column(String(100), nullable=True)
    
    # ✅ Champs de compatibilité pour l'ancien schéma
    url = Column(String, nullable=True)  # Maintenu pour compatibilité
    task_type = Column(String, default="scraping")
    error_message = Column(Text, nullable=True)  # Alias pour error
    
    def __repr__(self):
        return f"<ScrapingTask(task_id='{self.task_id}', status='{self.status}', urls={len(self.urls) if self.urls else 0})>"
    
    def to_dict(self):
        """Convertir en dictionnaire pour API JSON - Compatible schemas.py"""
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
            'progress': self.progress or {},
            'metrics': self.metrics or {},
            'parameters': self.parameters or {},
            'callback_url': self.callback_url,
            'max_retries': self.max_retries,
            'current_retries': self.current_retries,
            'worker_id': self.worker_id
        }

    def to_task_response(self):
        """Transformer l'objet ScrapingTask en réponse JSON pour l'API /tasks/{task_id}"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "analysis_type": self.analysis_type,
            "progress": self.progress or {"current": 0, "total": 1, "percentage": 0, "display": "0/1"},
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
            "task_type": self.task_type,
            "error_message": self.error_message,
            "metadata_info": self.metadata_info
        }


def get_db() -> Generator[Session, None, None]:
    """Générateur de session de base de données"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Erreur session DB: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager pour session DB"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Erreur session DB: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_database_connection() -> bool:
    """Tester la connexion à la base de données"""
    try:
        logger.info("🔧 Testing database connection...")
        with engine.connect() as connection:
            # SQLAlchemy 2.0 - Utiliser text() obligatoirement
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            if test_result and test_result[0] == 1:
                logger.info("✅ Database connection test successful")
                return True
            return False
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

def create_tables():
    """Créer toutes les tables"""
    try:
        logger.info("🔧 Creating database tables...")
        # Créer toutes les tables définies dans Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

def init_database():
    """Initialiser la base de données"""
    try:
        logger.info("🔧 Initializing database...")
        
        if not test_database_connection():
            raise Exception("Connection failed")
        
        # Ajoutez ces lignes :
        verify_schema()
        upgrade_schema()
        normalize_progress_column()
        
        if not create_tables():
            raise Exception("Table creation failed")
        
        logger.info("✅ Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

# Alias pour compatibilité avec les anciens scripts
def init_db():
    """Alias pour init_database() pour compatibilité"""
    return init_database()

def verify_schema():
    """Vérifier que le schéma de la base de données est à jour"""
    try:
        with engine.connect() as connection:
            # Vérifier l'existence de la table scraping_tasks
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'scraping_tasks'
                );
            """))
            
            table_exists = result.fetchone()[0]
            if table_exists:
                logger.info("✅ Database schema is up to date")
                
                # Vérifier si la colonne task_id existe
                column_check = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'scraping_tasks'
                        AND column_name = 'task_id'
                    );
                """))
                
                if column_check.fetchone()[0]:
                    logger.info("✅ task_id column exists")
                else:
                    logger.warning("⚠️ task_id column missing - will be created")
                    
            else:
                logger.info("ℹ️ scraping_tasks table will be created")
                
    except Exception as e:
        logger.warning(f"⚠️ Could not verify schema: {e}")

def normalize_progress_column():
    """Normaliser la colonne progress pour s'assurer qu'elle contient du JSON valide"""
    try:
        with engine.connect() as connection:
            # Mettre à jour les enregistrements avec progress NULL ou invalide
            update_query = text("""
                UPDATE scraping_tasks 
                SET progress = jsonb_build_object(
                    'current', COALESCE((progress->>'current')::int, 0),
                    'total', COALESCE((progress->>'total')::int, 1),
                    'percentage', COALESCE((progress->>'percentage')::float, 0.0),
                    'display', COALESCE(progress->>'display', '0/1')
                )
                WHERE progress IS NULL 
                OR NOT jsonb_typeof(progress) = 'object'
                OR progress->>'current' IS NULL
                OR progress->>'total' IS NULL;
            """)
            
            result = connection.execute(update_query)
            connection.commit()
            
            if result.rowcount > 0:
                logger.info(f"✅ Normalized {result.rowcount} progress records")
            else:
                logger.info("✅ Progress column is already normalized")
                
    except Exception as e:
        logger.warning(f"⚠️ Could not normalize progress column: {e}")

# ✅ FONCTION D'UPGRADE DE SCHÉMA (pour migration depuis ancien modèle)
def upgrade_schema():
    """Mettre à jour le schéma de la base de données"""
    try:
        logger.info("🔄 Upgrading database schema...")
        
        with engine.connect() as connection:
            # Ajouter task_id si elle n'existe pas
            try:
                connection.execute(text("""
                    ALTER TABLE scraping_tasks 
                    ADD COLUMN IF NOT EXISTS task_id VARCHAR(255) UNIQUE;
                """))
                logger.info("✅ task_id column added/verified")
            except Exception as e:
                logger.debug(f"task_id column might already exist: {e}")
            
            # Ajouter urls si elle n'existe pas
            try:
                connection.execute(text("""
                    ALTER TABLE scraping_tasks 
                    ADD COLUMN IF NOT EXISTS urls JSON;
                """))
                logger.info("✅ urls column added/verified")
            except Exception as e:
                logger.debug(f"urls column might already exist: {e}")
            
            # Ajouter analysis_type si elle n'existe pas
            try:
                connection.execute(text("""
                    ALTER TABLE scraping_tasks 
                    ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(50) DEFAULT 'standard';
                """))
                logger.info("✅ analysis_type column added/verified")
            except Exception as e:
                logger.debug(f"analysis_type column might already exist: {e}")
            
            # Ajouter metrics si elle n'existe pas
            try:
                connection.execute(text("""
                    ALTER TABLE scraping_tasks 
                    ADD COLUMN IF NOT EXISTS metrics JSON;
                """))
                logger.info("✅ metrics column added/verified")
            except Exception as e:
                logger.debug(f"metrics column might already exist: {e}")
            
            # Mettre à jour les task_id manquants
            connection.execute(text("""
                UPDATE scraping_tasks 
                SET task_id = gen_random_uuid()::text 
                WHERE task_id IS NULL OR task_id = '';
            """))
            
            connection.commit()
            logger.info("✅ Schema upgrade completed")
            
    except Exception as e:
        logger.error(f"❌ Schema upgrade failed: {e}")
        raise

# Variables d'export pour compatibilité
__all__ = [
    'Base', 'engine', 'SessionLocal', 'get_db', 'get_db_session',
    'test_database_connection', 'init_database', 'init_db', 'create_tables',
    'ScrapingTask', 'verify_schema', 'normalize_progress_column', 'upgrade_schema'
]