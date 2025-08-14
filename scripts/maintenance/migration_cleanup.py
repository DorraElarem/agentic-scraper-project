#!/usr/bin/env python3
"""
Script de migration et nettoyage pour corriger l'erreur "invalid literal for int() with base 10: '0/1'"

Ce script :
1. Analyse toutes les tâches existantes
2. Identifie les valeurs de progression problématiques
3. Normalise toutes les valeurs au format correct
4. Génère un rapport détaillé des corrections

Usage:
    python migration_cleanup.py                    # Mode normal
    python migration_cleanup.py --dry-run          # Simulation sans modifications
    python migration_cleanup.py --verbose          # Mode verbeux
    python migration_cleanup.py --backup           # Crée une sauvegarde avant
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
import json

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.database import ScrapingTask, SessionLocal, engine, get_database_url
    from app.utils.helpers import (
        safe_parse_progress, 
        validate_progress_pair, 
        normalize_progress_string,
        diagnose_progress_value
    )
    from sqlalchemy import text, inspect, create_engine
    from sqlalchemy.exc import SQLAlchemyError
    from urllib.parse import quote_plus
except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
    print("Assurez-vous que le script est exécuté depuis la racine du projet.")
    sys.exit(1)

# Configuration du logging
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'migration_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

class ProgressMigrationTool:
    """Outil de migration pour corriger les données de progression"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = setup_logging(verbose)
        self.stats = {
            'total_tasks': 0,
            'problematic_tasks': 0,
            'fixed_tasks': 0,
            'errors': 0,
            'details': []
        }
    
    def check_database_connection(self) -> bool:
        """Vérifier la connexion à la base de données avec gestion d'encodage"""
        try:
            # Première tentative avec l'engine existant
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.logger.info("✅ Connexion à la base de données OK")
                return True
        except UnicodeDecodeError as unicode_error:
            self.logger.warning(f"⚠️ Problème d'encodage détecté : {unicode_error}")
            return self._try_connection_with_fixed_encoding()
        except Exception as e:
            self.logger.error(f"❌ Erreur de connexion DB : {e}")
            return self._try_connection_with_fixed_encoding()
    
    def _try_connection_with_fixed_encoding(self) -> bool:
        """Tentative de connexion avec encodage corrigé"""
        try:
            self.logger.info("🔧 Tentative de connexion avec encodage UTF-8 forcé...")
            
            # Récupérer les paramètres de connexion avec encodage correct
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_pass = os.getenv("POSTGRES_PASSWORD", "dorra123")
            db_host = os.getenv("DB_HOST", "localhost")  # localhost par défaut pour script
            db_name = os.getenv("POSTGRES_DB", "scraper_db")
            
            # Encodage sûr du mot de passe
            db_pass_encoded = quote_plus(db_pass)
            
            # URL de connexion avec options d'encodage
            fixed_url = f"postgresql://{db_user}:{db_pass_encoded}@{db_host}:5432/{db_name}"
            
            # Créer un nouvel engine avec options d'encodage spécifiques
            fixed_engine = create_engine(
                fixed_url,
                echo=False,
                pool_pre_ping=True,
                connect_args={
                    "client_encoding": "utf8",
                    "connect_timeout": 10,
                    "options": "-c client_encoding=utf8"
                },
                pool_recycle=3600
            )
            
            # Test de connexion
            with fixed_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.logger.info("✅ Connexion réussie avec encodage corrigé")
                
                # Remplacer l'engine global pour le reste du script
                global engine
                engine = fixed_engine
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Échec connexion avec encodage corrigé : {e}")
            self._suggest_connection_fixes()
            return False
    
    def _suggest_connection_fixes(self):
        """Suggérer des solutions pour les problèmes de connexion"""
        self.logger.info("\n🛠️ SUGGESTIONS DE CORRECTION :")
        self.logger.info("1. Vérifiez que PostgreSQL est démarré :")
        self.logger.info("   docker-compose up -d db")
        self.logger.info("2. Vérifiez les variables d'environnement :")
        self.logger.info(f"   POSTGRES_USER={os.getenv('POSTGRES_USER', 'NON_DÉFINI')}")
        self.logger.info(f"   POSTGRES_PASSWORD=***")
        self.logger.info(f"   DB_HOST={os.getenv('DB_HOST', 'NON_DÉFINI')}")
        self.logger.info(f"   POSTGRES_DB={os.getenv('POSTGRES_DB', 'NON_DÉFINI')}")
        self.logger.info("3. Si Docker, utilisez : DB_HOST=localhost")
        self.logger.info("4. Si caractères spéciaux dans le mot de passe, vérifiez l'encodage")
    
    def check_table_exists(self) -> bool:
        """Vérifier que la table scraping_tasks existe"""
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if 'scraping_tasks' not in tables:
                self.logger.error("❌ Table 'scraping_tasks' introuvable")
                return False
            self.logger.info("✅ Table 'scraping_tasks' trouvée")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification table : {e}")
            return False
    
    def analyze_task_progress(self, task: ScrapingTask) -> Dict[str, Any]:
        """Analyser les données de progression d'une tâche"""
        analysis = {
            'task_id': task.task_id,
            'current_raw': task.progress_current,
            'total_raw': task.progress_total,
            'is_problematic': False,
            'issues': [],
            'suggested_fix': None
        }
        
        # Diagnostic de la valeur current
        current_diagnosis = diagnose_progress_value(task.progress_current)
        total_diagnosis = diagnose_progress_value(task.progress_total)
        
        # Identifier les problèmes
        if current_diagnosis['contains_slash']:
            analysis['is_problematic'] = True
            analysis['issues'].append(f"progress_current contient '/' : '{task.progress_current}'")
        
        if total_diagnosis['contains_slash']:
            analysis['is_problematic'] = True
            analysis['issues'].append(f"progress_total contient '/' : '{task.progress_total}'")
        
        # Vérifier si la conversion standard échouerait
        try:
            int(str(task.progress_current))
        except ValueError:
            analysis['is_problematic'] = True
            analysis['issues'].append(f"progress_current non convertible en int : '{task.progress_current}'")
        
        try:
            int(str(task.progress_total))
        except ValueError:
            analysis['is_problematic'] = True
            analysis['issues'].append(f"progress_total non convertible en int : '{task.progress_total}'")
        
        # Calculer la correction suggérée si problématique
        if analysis['is_problematic']:
            try:
                current_fixed, total_fixed = validate_progress_pair(
                    task.progress_current, 
                    task.progress_total
                )
                analysis['suggested_fix'] = {
                    'current': str(current_fixed),
                    'total': str(total_fixed)
                }
            except Exception as e:
                analysis['suggested_fix'] = {'current': '0', 'total': '1'}
                analysis['issues'].append(f"Erreur calcul correction : {e}")
        
        return analysis
    
    def create_backup(self) -> bool:
        """Créer une sauvegarde des données problématiques"""
        try:
            db = SessionLocal()
            tasks = db.query(ScrapingTask).all()
            
            backup_data = []
            for task in tasks:
                backup_data.append({
                    'id': task.id,
                    'task_id': task.task_id,
                    'progress_current': task.progress_current,
                    'progress_total': task.progress_total,
                    'status': task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                })
            
            backup_filename = f"backup_progress_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Sauvegarde créée : {backup_filename}")
            db.close()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur création sauvegarde : {e}")
            return False
    
    def analyze_all_tasks(self) -> List[Dict[str, Any]]:
        """Analyser toutes les tâches pour identifier les problèmes"""
        self.logger.info("🔍 Analyse de toutes les tâches...")
        
        db = SessionLocal()
        try:
            tasks = db.query(ScrapingTask).all()
            self.stats['total_tasks'] = len(tasks)
            
            analyses = []
            for task in tasks:
                analysis = self.analyze_task_progress(task)
                if analysis['is_problematic']:
                    self.stats['problematic_tasks'] += 1
                    analyses.append(analysis)
                    if self.verbose:
                        self.logger.debug(f"Tâche problématique : {task.task_id} - {analysis['issues']}")
            
            self.logger.info(f"📊 Analyse terminée : {self.stats['problematic_tasks']}/{self.stats['total_tasks']} tâches problématiques")
            return analyses
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse : {e}")
            return []
        finally:
            db.close()
    
    def fix_task_progress(self, task: ScrapingTask, suggested_fix: Dict[str, str]) -> bool:
        """Corriger la progression d'une tâche spécifique"""
        try:
            old_current = task.progress_current
            old_total = task.progress_total
            
            # Appliquer la correction
            task.progress_current = suggested_fix['current']
            task.progress_total = suggested_fix['total']
            
            self.stats['details'].append({
                'task_id': task.task_id,
                'old_current': old_current,
                'old_total': old_total,
                'new_current': task.progress_current,
                'new_total': task.progress_total
            })
            
            if self.verbose:
                self.logger.debug(f"Tâche {task.task_id} : {old_current}/{old_total} → {task.progress_current}/{task.progress_total}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur correction tâche {task.task_id} : {e}")
            self.stats['errors'] += 1
            return False
    
    def run_migration(self, problematic_analyses: List[Dict[str, Any]]) -> bool:
        """Exécuter les corrections en base de données"""
        if not problematic_analyses:
            self.logger.info("✅ Aucune correction nécessaire")
            return True
        
        if self.dry_run:
            self.logger.info(f"🧪 MODE DRY-RUN : {len(problematic_analyses)} tâches seraient corrigées")
            for analysis in problematic_analyses:
                fix = analysis.get('suggested_fix', {})
                self.logger.info(f"  - {analysis['task_id']} : {analysis['current_raw']}/{analysis['total_raw']} → {fix.get('current', '?')}/{fix.get('total', '?')}")
            return True
        
        self.logger.info(f"🔧 Correction de {len(problematic_analyses)} tâches...")
        
        db = SessionLocal()
        try:
            for analysis in problematic_analyses:
                task = db.query(ScrapingTask).filter(
                    ScrapingTask.task_id == analysis['task_id']
                ).first()
                
                if not task:
                    self.logger.warning(f"⚠️ Tâche {analysis['task_id']} introuvable")
                    continue
                
                if analysis['suggested_fix']:
                    if self.fix_task_progress(task, analysis['suggested_fix']):
                        self.stats['fixed_tasks'] += 1
            
            # Commit toutes les modifications
            db.commit()
            self.logger.info(f"✅ Migration terminée : {self.stats['fixed_tasks']} tâches corrigées")
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Erreur SQL durant migration : {e}")
            db.rollback()
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur durant migration : {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def generate_report(self) -> str:
        """Générer un rapport détaillé de la migration"""
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    RAPPORT DE MIGRATION                      ║
║                Correction progression tasks                  ║
╠══════════════════════════════════════════════════════════════╣
║ Date/Heure     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
║ Mode           : {'DRY-RUN (simulation)' if self.dry_run else 'PRODUCTION (réel)'}               ║
║ Tâches totales : {self.stats['total_tasks']:<6}                                   ║
║ Problématiques : {self.stats['problematic_tasks']:<6}                                   ║
║ Corrigées      : {self.stats['fixed_tasks']:<6}                                   ║
║ Erreurs        : {self.stats['errors']:<6}                                   ║
╚══════════════════════════════════════════════════════════════╝

"""
        
        if self.stats['details']:
            report += "\n📋 DÉTAIL DES CORRECTIONS :\n"
            report += "-" * 80 + "\n"
            for detail in self.stats['details']:
                report += f"Tâche: {detail['task_id']}\n"
                report += f"  Avant : {detail['old_current']}/{detail['old_total']}\n"
                report += f"  Après : {detail['new_current']}/{detail['new_total']}\n"
                report += "-" * 40 + "\n"
        
        # Sauvegarder le rapport
        report_filename = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report

def main():
    """Fonction principale du script de migration"""
    parser = argparse.ArgumentParser(description="Script de migration des données de progression")
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans modifications')
    parser.add_argument('--verbose', action='store_true', help='Mode verbeux')
    parser.add_argument('--backup', action='store_true', help='Créer une sauvegarde avant migration')
    parser.add_argument('--force', action='store_true', help='Forcer la migration sans confirmation')
    
    args = parser.parse_args()
    
    print("🚀 Script de Migration - Correction Progression Tasks")
    print("=" * 60)
    
    # Initialiser l'outil de migration
    migration_tool = ProgressMigrationTool(dry_run=args.dry_run, verbose=args.verbose)
    
    # Vérifications préliminaires
    if not migration_tool.check_database_connection():
        print("❌ Impossible de se connecter à la base de données")
        sys.exit(1)
    
    if not migration_tool.check_table_exists():
        print("❌ Table 'scraping_tasks' introuvable")
        sys.exit(1)
    
    # Sauvegarde si demandée
    if args.backup:
        print("💾 Création de la sauvegarde...")
        if not migration_tool.create_backup():
            print("❌ Échec de la sauvegarde")
            if not args.force:
                sys.exit(1)
    
    # Analyse des tâches
    print("🔍 Analyse des tâches en cours...")
    problematic_analyses = migration_tool.analyze_all_tasks()
    
    if not problematic_analyses:
        print("✅ Aucune tâche problématique trouvée !")
        print("   Toutes les valeurs de progression sont déjà au bon format.")
        return
    
    # Affichage du résumé
    print(f"\n📊 RÉSUMÉ DE L'ANALYSE :")
    print(f"   Total des tâches        : {migration_tool.stats['total_tasks']}")
    print(f"   Tâches problématiques   : {migration_tool.stats['problematic_tasks']}")
    print(f"   Nécessitent correction  : {len(problematic_analyses)}")
    
    # Afficher quelques exemples
    if args.verbose and problematic_analyses:
        print(f"\n🔍 EXEMPLES DE PROBLÈMES DÉTECTÉS :")
        for i, analysis in enumerate(problematic_analyses[:3]):  # Premiers 3
            print(f"   {i+1}. Tâche {analysis['task_id'][:8]}...")
            for issue in analysis['issues']:
                print(f"      - {issue}")
            fix = analysis.get('suggested_fix', {})
            print(f"      → Correction : {fix.get('current', '?')}/{fix.get('total', '?')}")
        if len(problematic_analyses) > 3:
            print(f"   ... et {len(problematic_analyses) - 3} autres")
    
    # Confirmation si pas en mode force ou dry-run
    if not args.dry_run and not args.force:
        print(f"\n⚠️  ATTENTION : Cette opération va modifier {len(problematic_analyses)} tâches en base.")
        confirm = input("   Voulez-vous continuer ? (oui/non) : ").lower().strip()
        if confirm not in ['oui', 'o', 'yes', 'y']:
            print("❌ Migration annulée par l'utilisateur")
            return
    
    # Exécution de la migration
    print(f"\n🔧 {'Simulation' if args.dry_run else 'Exécution'} de la migration...")
    success = migration_tool.run_migration(problematic_analyses)
    
    # Génération du rapport
    report = migration_tool.generate_report()
    print(report)
    
    if success:
        print("✅ Migration terminée avec succès !")
        if not args.dry_run:
            print("   Les données ont été corrigées en base de données.")
            print("   L'erreur 'invalid literal for int()' devrait être résolue.")
        else:
            print("   Exécutez sans --dry-run pour appliquer les corrections.")
    else:
        print("❌ Échec de la migration !")
        print("   Vérifiez les logs pour plus de détails.")
        sys.exit(1)

# Tests unitaires intégrés
def run_self_tests():
    """Tests de validation du script"""
    print("🧪 Exécution des tests de validation...")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Parsing de valeurs problématiques
    tests_total += 1
    try:
        result = safe_parse_progress("3/5")
        assert result == 3, f"Expected 3, got {result}"
        tests_passed += 1
        print("✅ Test parsing '3/5' : OK")
    except Exception as e:
        print(f"❌ Test parsing '3/5' : {e}")
    
    # Test 2: Normalisation
    tests_total += 1
    try:
        result = normalize_progress_string("  4.7  ")
        assert result == "4", f"Expected '4', got '{result}'"
        tests_passed += 1
        print("✅ Test normalisation '  4.7  ' : OK")
    except Exception as e:
        print(f"❌ Test normalisation : {e}")
    
    # Test 3: Validation de paire
    tests_total += 1
    try:
        current, total = validate_progress_pair("3/5", "10")
        assert current == 3 and total == 10, f"Expected (3, 10), got ({current}, {total})"
        tests_passed += 1
        print("✅ Test validation paire : OK")
    except Exception as e:
        print(f"❌ Test validation paire : {e}")
    
    print(f"\n📊 Tests : {tests_passed}/{tests_total} réussis")
    return tests_passed == tests_total

if __name__ == "__main__":
    # Vérifier si demande de tests
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        if run_self_tests():
            print("✅ Tous les tests passent, le script est prêt !")
        else:
            print("❌ Certains tests échouent, vérifiez votre installation")
        sys.exit(0)
    
    # Exécution normale
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)