#!/usr/bin/env python3
"""
Script de migration simple pour corriger la base de données
Contourne les problèmes d'encodage
"""

import os
import sys
import psycopg2
import json
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Connexion directe à PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'dorra123'),
            database=os.getenv('POSTGRES_DB', 'scraper_db'),
            # Forcer l'encodage UTF-8
            client_encoding='utf8'
        )
        conn.set_client_encoding('UTF8')
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Vérifie si une colonne existe"""
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de colonne: {e}")
        return False

def add_progress_column(cursor):
    """Ajoute la colonne progress"""
    try:
        if not check_column_exists(cursor, 'scraping_tasks', 'progress'):
            logger.info("Ajout de la colonne 'progress'...")
            cursor.execute("""
                ALTER TABLE scraping_tasks 
                ADD COLUMN progress JSON DEFAULT '{"current": 0, "total": 1, "percentage": 0.0, "display": "0/1"}'::json
            """)
            logger.info("✅ Colonne 'progress' ajoutée")
            return True
        else:
            logger.info("✅ Colonne 'progress' existe déjà")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de la colonne progress: {e}")
        return False

def add_results_column(cursor):
    """Ajoute la colonne results"""
    try:
        if not check_column_exists(cursor, 'scraping_tasks', 'results'):
            logger.info("Ajout de la colonne 'results'...")
            cursor.execute("""
                ALTER TABLE scraping_tasks 
                ADD COLUMN results JSON DEFAULT '[]'::json
            """)
            logger.info("✅ Colonne 'results' ajoutée")
            return True
        else:
            logger.info("✅ Colonne 'results' existe déjà")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de la colonne results: {e}")
        return False

def add_metrics_column(cursor):
    """Ajoute la colonne metrics"""
    try:
        if not check_column_exists(cursor, 'scraping_tasks', 'metrics'):
            logger.info("Ajout de la colonne 'metrics'...")
            cursor.execute("""
                ALTER TABLE scraping_tasks 
                ADD COLUMN metrics JSON
            """)
            logger.info("✅ Colonne 'metrics' ajoutée")
            return True
        else:
            logger.info("✅ Colonne 'metrics' existe déjà")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de la colonne metrics: {e}")
        return False

def test_insert(cursor):
    """Test d'insertion pour vérifier que tout fonctionne"""
    try:
        # Test d'insertion
        test_id = 'test-migration-' + str(int(os.urandom(4).hex(), 16))
        
        cursor.execute("""
            INSERT INTO scraping_tasks 
            (task_id, urls, status, progress, analysis_type, results, priority, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            test_id,
            json.dumps(["http://test.com"]),
            'pending',
            json.dumps({"current": 0, "total": 1, "percentage": 0.0, "display": "0/1"}),
            'standard',
            json.dumps([]),
            0
        ))
        
        inserted_id = cursor.fetchone()[0]
        
        # Test de lecture
        cursor.execute("""
            SELECT task_id, status, progress, results 
            FROM scraping_tasks 
            WHERE id = %s
        """, (inserted_id,))
        
        row = cursor.fetchone()
        if row:
            logger.info(f"✅ Test d'insertion réussi: {row[0]}")
        
        # Nettoyer
        cursor.execute("DELETE FROM scraping_tasks WHERE id = %s", (inserted_id,))
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 MIGRATION SIMPLE DE LA BASE DE DONNÉES")
    logger.info("=" * 50)
    
    # Connexion à la base
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Impossible de se connecter à la base de données")
        return 1
    
    try:
        cursor = conn.cursor()
        
        # Vérifier la connexion
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"✅ Connecté à PostgreSQL")
        
        # Vérifier que la table existe
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'scraping_tasks'
        """)
        
        if not cursor.fetchone():
            logger.error("❌ Table 'scraping_tasks' n'existe pas!")
            return 1
        
        logger.info("✅ Table 'scraping_tasks' trouvée")
        
        # Commencer la transaction
        success = True
        
        # 1. Ajouter la colonne progress
        if not add_progress_column(cursor):
            success = False
        
        # 2. Ajouter la colonne results
        if not add_results_column(cursor):
            success = False
        
        # 3. Ajouter la colonne metrics
        if not add_metrics_column(cursor):
            success = False
        
        if success:
            # 4. Test d'insertion
            if test_insert(cursor):
                # Confirmer les changements
                conn.commit()
                logger.info("=" * 50)
                logger.info("✅ MIGRATION TERMINÉE AVEC SUCCÈS!")
                logger.info("\n📋 Prochaines étapes:")
                logger.info("1. Redémarrez les services: docker-compose restart")
                logger.info("2. Testez l'API: POST /scrape")
                return 0
            else:
                conn.rollback()
                logger.error("❌ Échec du test d'insertion")
                return 1
        else:
            conn.rollback()
            logger.error("❌ Échec de la migration")
            return 1
            
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        return 1
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sys.exit(main())