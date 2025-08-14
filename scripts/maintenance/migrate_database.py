#!/usr/bin/env python3
"""
Script de migration pour ajouter la colonne progress et corriger la structure de la base de données
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text, inspect
import json
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Génère l'URL de connexion à la base de données"""
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "dorra123")
    db_host = os.getenv("DB_HOST", "db")
    db_name = os.getenv("POSTGRES_DB", "scraper_db")
    return f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"

def check_and_add_column(engine, table_name, column_name, column_type, default_value=None):
    """Vérifie et ajoute une colonne si elle n'existe pas"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            logger.info(f"Ajout de la colonne '{column_name}' à la table '{table_name}'...")
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    if default_value:
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                    else:
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    
                    conn.execute(text(sql))
                    trans.commit()
                    logger.info(f"✅ Colonne '{column_name}' ajoutée avec succès")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"❌ Erreur lors de l'ajout de la colonne: {e}")
                    return False
        else:
            logger.info(f"✅ Colonne '{column_name}' existe déjà")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification de la colonne: {e}")
        return False

def migrate_progress_data(engine):
    """Migre les données de progress_current/progress_total vers progress JSON"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('scraping_tasks')]
        
        # Si les anciennes colonnes existent, migrer les données
        if 'progress_current' in columns and 'progress_total' in columns:
            logger.info("Migration des données progress...")
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    # Migrer les données existantes
                    result = conn.execute(text("""
                        SELECT id, progress_current, progress_total 
                        FROM scraping_tasks 
                        WHERE progress_current IS NOT NULL OR progress_total IS NOT NULL
                    """))
                    
                    rows_migrated = 0
                    for row in result:
                        current = int(row.progress_current or 0)
                        total = int(row.progress_total or 1)
                        if total <= 0:
                            total = 1
                        if current > total:
                            current = total
                        
                        percentage = round((current / total) * 100, 2)
                        progress_json = {
                            "current": current,
                            "total": total,
                            "percentage": percentage,
                            "display": f"{current}/{total}"
                        }
                        
                        conn.execute(text("""
                            UPDATE scraping_tasks 
                            SET progress = :progress_data 
                            WHERE id = :row_id
                        """), {
                            "progress_data": json.dumps(progress_json),
                            "row_id": row.id
                        })
                        rows_migrated += 1
                    
                    # Supprimer les anciennes colonnes
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN IF EXISTS progress_current"))
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN IF EXISTS progress_total"))
                    
                    trans.commit()
                    logger.info(f"✅ Migration terminée: {rows_migrated} lignes migrées")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"❌ Erreur lors de la migration: {e}")
                    return False
        else:
            logger.info("✅ Pas de migration nécessaire")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration des données: {e}")
        return False

def ensure_all_columns(engine):
    """S'assure que toutes les colonnes nécessaires existent"""
    logger.info("Vérification de toutes les colonnes...")
    
    required_columns = {
        'id': 'SERIAL PRIMARY KEY',
        'task_id': 'VARCHAR(36) UNIQUE NOT NULL',
        'urls': 'JSON NOT NULL',
        'status': 'VARCHAR(20) DEFAULT \'pending\'',
        'progress': 'JSON DEFAULT \'{"current": 0, "total": 1, "percentage": 0.0, "display": "0/1"}\'::json',
        'analysis_type': 'VARCHAR(50) DEFAULT \'standard\'',
        'result': 'JSON',
        'results': 'JSON DEFAULT \'[]\'::json',
        'error': 'TEXT',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'started_at': 'TIMESTAMP',
        'completed_at': 'TIMESTAMP',
        'parameters': 'JSON',
        'callback_url': 'VARCHAR(512)',
        'priority': 'INTEGER DEFAULT 0',
        'metrics': 'JSON'
    }
    
    success = True
    for column_name, column_def in required_columns.items():
        if column_name in ['id']:  # Skip primary key
            continue
            
        # Extraire le type et la valeur par défaut
        if 'DEFAULT' in column_def:
            parts = column_def.split('DEFAULT')
            column_type = parts[0].strip()
            default_value = parts[1].strip().strip("'")
            
            # Pour les JSON, ne pas mettre de guillemets autour de la valeur par défaut
            if column_type == 'JSON':
                if not check_and_add_column(engine, 'scraping_tasks', column_name, column_type):
                    success = False
                else:
                    # Définir la valeur par défaut après création
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE scraping_tasks ALTER COLUMN {column_name} SET DEFAULT '{default_value}'::json"))
                            conn.commit()
                    except Exception:
                        pass  # Ignore si déjà défini
            else:
                if not check_and_add_column(engine, 'scraping_tasks', column_name, column_type, default_value):
                    success = False
        else:
            column_type = column_def
            if not check_and_add_column(engine, 'scraping_tasks', column_name, column_type):
                success = False
    
    return success

def test_table_operations(engine):
    """Test les opérations de base sur la table"""
    logger.info("Test des opérations sur la table...")
    
    try:
        with engine.connect() as conn:
            # Test d'insertion
            test_data = {
                'task_id': 'test-migration-12345',
                'urls': json.dumps(["http://test.com"]),
                'status': 'pending',
                'progress': json.dumps({"current": 0, "total": 1, "percentage": 0.0, "display": "0/1"}),
                'analysis_type': 'standard',
                'results': json.dumps([]),
                'priority': 0
            }
            
            # Supprimer s'il existe déjà
            conn.execute(text("DELETE FROM scraping_tasks WHERE task_id = :task_id"), 
                        {"task_id": test_data['task_id']})
            
            # Insérer
            result = conn.execute(text("""
                INSERT INTO scraping_tasks 
                (task_id, urls, status, progress, analysis_type, results, priority, created_at)
                VALUES 
                (:task_id, :urls, :status, :progress, :analysis_type, :results, :priority, NOW())
                RETURNING id
            """), test_data)
            
            inserted_id = result.fetchone()[0]
            
            # Test de lecture
            read_result = conn.execute(text("""
                SELECT task_id, status, progress, results 
                FROM scraping_tasks 
                WHERE id = :id
            """), {"id": inserted_id})
            
            row = read_result.fetchone()
            
            # Nettoyer
            conn.execute(text("DELETE FROM scraping_tasks WHERE id = :id"), {"id": inserted_id})
            conn.commit()
            
            logger.info("✅ Test des opérations réussi")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 MIGRATION DE LA BASE DE DONNÉES")
    logger.info("=" * 50)
    
    try:
        # Connexion à la base de données
        database_url = get_database_url()
        engine = create_engine(database_url, echo=False)
        
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connecté à PostgreSQL: {version.split()[0]} {version.split()[1]}")
        
        # Vérifier que la table existe
        inspector = inspect(engine)
        if 'scraping_tasks' not in inspector.get_table_names():
            logger.error("❌ Table 'scraping_tasks' n'existe pas!")
            return 1
        
        # 1. S'assurer que toutes les colonnes existent
        if not ensure_all_columns(engine):
            logger.error("❌ Échec de la vérification des colonnes")
            return 1
        
        # 2. Migrer les données de progress si nécessaire
        if not migrate_progress_data(engine):
            logger.error("❌ Échec de la migration des données")
            return 1
        
        # 3. Tester les opérations
        if not test_table_operations(engine):
            logger.error("❌ Échec du test des opérations")
            return 1
        
        logger.info("=" * 50)
        logger.info("✅ MIGRATION TERMINÉE AVEC SUCCÈS!")
        logger.info("\n📋 Actions recommandées:")
        logger.info("1. Redémarrez vos services: docker-compose restart")
        logger.info("2. Testez votre API: POST /scrape")
        logger.info("3. Vérifiez: GET /tasks")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())