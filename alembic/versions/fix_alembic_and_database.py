#!/usr/bin/env python3
"""
Script pour corriger la base de données et Alembic
Résout l'erreur de colonne 'progress' manquante
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError
import json

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
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
        print(f"Erreur lors de la vérification de la colonne: {e}")
        return False

def migrate_progress_columns(engine):
    """Migre les colonnes progress_current et progress_total vers progress JSON"""
    print("🔄 Migration des colonnes progress...")
    
    with engine.connect() as conn:
        # Vérifier l'état actuel des colonnes
        has_progress = check_column_exists(engine, 'scraping_tasks', 'progress')
        has_progress_current = check_column_exists(engine, 'scraping_tasks', 'progress_current')
        has_progress_total = check_column_exists(engine, 'scraping_tasks', 'progress_total')
        
        print(f"  - Colonne 'progress' existe: {has_progress}")
        print(f"  - Colonne 'progress_current' existe: {has_progress_current}")
        print(f"  - Colonne 'progress_total' existe: {has_progress_total}")
        
        trans = conn.begin()
        try:
            # Si on a les anciennes colonnes mais pas la nouvelle
            if (has_progress_current or has_progress_total) and not has_progress:
                print("  ✅ Ajout de la colonne 'progress' JSON...")
                conn.execute(text("ALTER TABLE scraping_tasks ADD COLUMN progress JSON DEFAULT '{}'::json"))
                
                # Migrer les données existantes
                if has_progress_current and has_progress_total:
                    print("  ✅ Migration des données existantes...")
                    result = conn.execute(text("""
                        UPDATE scraping_tasks 
                        SET progress = json_build_object(
                            'current', COALESCE(progress_current, 0),
                            'total', COALESCE(progress_total, 0)
                        )
                        WHERE progress_current IS NOT NULL OR progress_total IS NOT NULL
                    """))
                    print(f"  ✅ {result.rowcount} lignes mises à jour")
                
                # Supprimer les anciennes colonnes
                if has_progress_current:
                    print("  ✅ Suppression de 'progress_current'...")
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN progress_current"))
                
                if has_progress_total:
                    print("  ✅ Suppression de 'progress_total'...")
                    conn.execute(text("ALTER TABLE scraping_tasks DROP COLUMN progress_total"))
            
            # Si on n'a pas la colonne progress du tout
            elif not has_progress:
                print("  ✅ Ajout de la colonne 'progress' JSON...")
                conn.execute(text("ALTER TABLE scraping_tasks ADD COLUMN progress JSON DEFAULT '{}'::json"))
            
            else:
                print("  ✅ La colonne 'progress' existe déjà, rien à faire")
            
            trans.commit()
            print("✅ Migration des colonnes terminée avec succès!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            raise

def reset_alembic_state(engine):
    """Remet à zéro l'état d'Alembic"""
    print("🔄 Remise à zéro de l'état Alembic...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Supprimer la table alembic_version si elle existe
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            print("  ✅ Table alembic_version supprimée")
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Erreur lors de la remise à zéro d'Alembic: {e}")
            raise

def create_initial_migration():
    """Crée une migration initiale pour l'état actuel"""
    print("🔄 Création de la migration initiale...")
    
    migration_content = '''"""Initial migration - Current database state

Revision ID: initial_state
Revises: 
Create Date: 2025-08-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_state'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Mark current state as migrated - no actual changes"""
    pass

def downgrade():
    """Cannot downgrade from initial state"""
    pass
'''
    
    # Créer le fichier de migration
    migration_file = "alembic/versions/001_initial_state.py"
    os.makedirs("alembic/versions", exist_ok=True)
    
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(migration_content)
    
    print(f"  ✅ Migration créée: {migration_file}")

def test_api_query(engine):
    """Test la requête qui posait problème"""
    print("🔄 Test de la requête API...")
    
    try:
        with engine.connect() as conn:
            # Requête similaire à celle qui échouait
            result = conn.execute(text("""
                SELECT 
                    id, task_id, urls, status, progress, analysis_type, 
                    result, results, error, created_at, started_at, 
                    completed_at, parameters, callback_url, priority, metrics
                FROM scraping_tasks 
                WHERE status = :status 
                ORDER BY created_at DESC 
                LIMIT :limit
            """), {"status": "running", "limit": 50})
            
            rows = result.fetchall()
            print(f"  ✅ Requête réussie! {len(rows)} tâches trouvées")
            return True
            
    except Exception as e:
        print(f"  ❌ Erreur dans la requête: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Démarrage de la correction de la base de données...")
    print("=" * 60)
    
    try:
        # Connexion à la base de données
        print("🔌 Connexion à la base de données...")
        engine = create_engine(get_database_url())
        
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"  ✅ Connecté à PostgreSQL: {version}")
        
        # 1. Migrer les colonnes progress
        migrate_progress_columns(engine)
        
        # 2. Remettre à zéro Alembic
        reset_alembic_state(engine)
        
        # 3. Créer une migration initiale
        create_initial_migration()
        
        # 4. Tester la requête API
        test_api_query(engine)
        
        print("=" * 60)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS!")
        print("\nProchaines étapes:")
        print("1. Exécutez: alembic stamp initial_state")
        print("2. Redémarrez vos services: docker-compose restart")
        print("3. Testez votre API: GET /tasks")
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()