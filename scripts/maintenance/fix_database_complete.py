#!/usr/bin/env python3
"""
Script pour corriger définitivement l'erreur de colonne 'results' manquante
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError
import json
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dorra123'),
    'database': os.getenv('POSTGRES_DB', 'scraper_db')
}

def get_database_url():
    """Génère l'URL de connexion à la base de données"""
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def check_column_exists(engine, table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la colonne: {e}")
        return False

def get_table_schema(engine, table_name):
    """Récupère le schéma complet d'une table"""
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return None
        
        columns = inspector.get_columns(table_name)
        return {col['name']: str(col['type']) for col in columns}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du schéma: {e}")
        return None

def fix_scraping_tasks_table(engine):
    """Corrige la table scraping_tasks pour avoir toutes les colonnes nécessaires"""
    logger.info("🔄 Correction de la table scraping_tasks...")
    
    # Vérifier l'état actuel
    schema = get_table_schema(engine, 'scraping_tasks')
    if not schema:
        logger.error("❌ Table scraping_tasks introuvable!")
        return False
    
    logger.info(f"📋 Schéma actuel: {list(schema.keys())}")
    
    required_columns = {
        'id': 'INTEGER',
        'task_id': 'VARCHAR(36)',
        'urls': 'JSON', 
        'status': 'VARCHAR(20)',
        'progress': 'JSON',
        'analysis_type': 'VARCHAR(50)',
        'result': 'JSON',        # Colonne pour compatibilité
        'results': 'JSON',       # Colonne principale
        'error': 'TEXT',
        'created_at': 'TIMESTAMP',
        'started_at': 'TIMESTAMP',
        'completed_at': 'TIMESTAMP',
        'parameters': 'JSON',
        'callback_url': 'VARCHAR(512)',
        'priority': 'INTEGER',
        'metrics': 'JSON'
    }
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            changes_made = False
            
            # Ajouter les colonnes manquantes
            for col_name, col_type in required_columns.items():
                if col_name not in schema:
                    logger.info(f"  ➕ Ajout de la colonne '{col_name}' ({col_type})...")
                    
                    if col_type == 'JSON':
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} JSON DEFAULT '{{}}'::json"
                    elif col_type == 'INTEGER':
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} INTEGER DEFAULT 0"
                    elif col_type == 'TIMESTAMP':
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} TIMESTAMP NULL"
                    elif 'VARCHAR' in col_type:
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} {col_type} NULL"
                    elif col_type == 'TEXT':
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} TEXT NULL"
                    else:
                        sql = f"ALTER TABLE scraping_tasks ADD COLUMN {col_name} {col_type}"
                    
                    conn.execute(text(sql))
                    changes_made = True
                    logger.info(f"    ✅ Colonne '{col_name}' ajoutée")
            
            # Migration spéciale pour les colonnes progress
            if 'progress_current' in schema or 'progress_total' in schema:
                logger.info("  🔄 Migration des données progress...")
                
                # Migrer les données existantes vers la nouvelle structure
                result = conn.execute(text("""
                    UPDATE scraping_tasks 
                    SET progress = json_build_object(
                        'current', COALESCE(progress_current::integer, 0),
                        'total', COALESCE(progress_total::integer, 1),
                        'percentage', ROUND((COALESCE(progress_current::integer, 0)::numeric / 
                                            NULLIF(COALESCE(progress_total::integer, 1), 0)::numeric) * 100, 2),
                        'display', CONCAT(COALESCE(progress_current::integer, 0), '/', 
                                          COALESCE(progress_total::integer, 1))
                    )
                    WHERE (progress_current IS NOT NULL OR progress_total IS NOT NULL)
                    AND (progress IS NULL OR progress::text = '{}')
                """))
                logger.info(f"    ✅ {result.rowcount} lignes migrées")
                
                # Supprimer les anciennes colonnes
                if 'progress_current' in schema:
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN progress_current"))
                    logger.info("    ✅ Colonne 'progress_current' supprimée")
                    changes_made = True
                
                if 'progress_total' in schema:
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN progress_total"))
                    logger.info("    ✅ Colonne 'progress_total' supprimée")
                    changes_made = True
            
            # Synchroniser les données entre result et results
            logger.info("  🔄 Synchronisation result ↔ results...")
            sync_result = conn.execute(text("""
		UPDATE scraping_tasks 
    		SET results = CASE 
        	    WHEN results IS NULL OR results::text IN ('{}', '[]', 'null') THEN
            	    	CASE 
                	    WHEN result IS NOT NULL AND result::text NOT IN ('{}', 'null') THEN 
                    		json_build_array(result)
                	    ELSE '[]'::json 
            		END
        	    ELSE results 
    		END,
    		result = CASE 
        	    WHEN result IS NULL OR result::text IN ('{}', 'null') THEN
            		CASE 
                	    WHEN results IS NOT NULL AND results::text NOT IN ('{}', '[]', 'null') AND
                     		 json_typeof(results) = 'array' AND json_array_length(results) > 0 THEN
                    		results->0
                	    ELSE '{}'::json 
            		END
        	    ELSE result 
    		END
    		WHERE (result IS NULL OR result::text IN ('{}', 'null'))
       		    OR (results IS NULL OR results::text IN ('{}', '[]', 'null'))
	    """))
            logger.info(f"    ✅ {sync_result.rowcount} lignes synchronisées")
            
            trans.commit()
            
            if changes_made:
                logger.info("✅ Table scraping_tasks corrigée avec succès!")
            else:
                logger.info("✅ Table scraping_tasks déjà à jour")
            
            return True
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Erreur lors de la correction: {e}")
            raise

def validate_table_structure(engine):
    """Valide que la table a la structure correcte"""
    logger.info("🔍 Validation de la structure de la table...")
    
    try:
        with engine.connect() as conn:
            # Test de la requête qui posait problème
            test_query = text("""
                SELECT 
                    id, task_id, urls, status, progress, analysis_type, 
                    result, results, error, created_at, started_at, 
                    completed_at, parameters, callback_url, priority, metrics
                FROM scraping_tasks 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            result = conn.execute(test_query)
            row = result.fetchone()
            
            logger.info("✅ Requête de validation réussie!")
            
            if row:
                logger.info(f"📋 Exemple de données: task_id={row[1] if len(row) > 1 else 'N/A'}")
            else:
                logger.info("📋 Aucune donnée dans la table (c'est normal)")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation: {e}")
        return False

def create_test_task(engine):
    """Crée une tâche de test pour vérifier le bon fonctionnement"""
    logger.info("🧪 Création d'une tâche de test...")
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            test_data = {
                'task_id': 'test-task-12345',
                'status': 'completed',
                'urls': json.dumps(["http://example.com"]),
                'progress': json.dumps({"current": 1, "total": 1, "percentage": 100.0, "display": "1/1"}),
                'analysis_type': 'standard',
                'result': json.dumps({"url": "http://example.com", "success": True}),
                'results': json.dumps([{"url": "http://example.com", "success": True}]),
                'priority': 0
            }
            
            # Supprimer la tâche de test existante
            conn.execute(text("DELETE FROM scraping_tasks WHERE task_id = :task_id"), 
                        {"task_id": test_data['task_id']})
            
            # Insérer la nouvelle tâche de test
            insert_query = text("""
                INSERT INTO scraping_tasks 
                (task_id, status, urls, progress, analysis_type, result, results, priority, created_at)
                VALUES 
                (:task_id, :status, :urls, :progress, :analysis_type, :result, :results, :priority, NOW())
            """)
            
            conn.execute(insert_query, test_data)
            trans.commit()
            
            logger.info(f"✅ Tâche de test créée: {test_data['task_id']}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la tâche de test: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 CORRECTION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        # Connexion à la base de données
        logger.info("🔌 Connexion à la base de données...")
        engine = create_engine(get_database_url(), echo=False)
        
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connecté à PostgreSQL: {version.split()[0]} {version.split()[1]}")
        
        # 1. Corriger la table scraping_tasks
        if not fix_scraping_tasks_table(engine):
            logger.error("❌ Échec de la correction de la table")
            sys.exit(1)
        
        # 2. Valider la structure
        if not validate_table_structure(engine):
            logger.error("❌ Échec de la validation")
            sys.exit(1)
        
        # 3. Créer une tâche de test
        create_test_task(engine)
        
        print("=" * 60)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS!")
        print("\n📋 Actions recommandées:")
        print("1. Redémarrez vos services: docker-compose restart")
        print("2. Testez votre API: POST /scrape")
        print("3. Vérifiez: GET /tasks")
        print("4. Si tout fonctionne, supprimez la tâche de test")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        print("\n🔧 Actions de dépannage:")
        print("1. Vérifiez que PostgreSQL est démarré")
        print("2. Vérifiez les variables d'environnement")
        print("3. Vérifiez les permissions de la base de données")
        sys.exit(1)

if __name__ == "__main__":
    main()