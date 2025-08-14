"""
Module des modèles de données pour l'Agentic Scraper
"""

# Import de la base et des utilitaires de base de données
from .database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_database,
    init_db,
    test_database_connection,
    create_tables,
    ScrapingTask
)

# Import des modèles spécifiques (si ils existent)
try:
    from .scraping_task import ScrapingTask as ScrapingTaskModel
except ImportError:
    # Utiliser le modèle défini dans database.py si pas de fichier séparé
    ScrapingTaskModel = ScrapingTask

# Export de tous les éléments importants
__all__ = [
    # Base SQLAlchemy
    'Base',
    'engine',
    'SessionLocal',
    
    # Fonctions de session
    'get_db',
    'get_db_session',
    
    # Fonctions d'initialisation
    'init_database',
    'init_db',
    'test_database_connection',
    'create_tables',
    
    # Modèles
    'ScrapingTask',
    'ScrapingTaskModel',
]

# Placeholder pour d'autres modèles si nécessaires
models = {
    'ScrapingTask': ScrapingTask,
}

def get_model(model_name: str):
    """Récupérer un modèle par son nom"""
    return models.get(model_name)

def list_models():
    """Lister tous les modèles disponibles"""
    return list(models.keys())

# Informations du module
__version__ = "1.0.0"
__author__ = "Agentic Scraper Team"